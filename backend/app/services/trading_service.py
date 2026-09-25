"""
Paper-trading engine: the only code that changes trades, positions and cash.

Model
-----
* A BUY or SHORT trade with status OPEN is a *lot*: shares bought (or sold
  short) at one price. Lots are the source of truth.
* A `Portfolio` row is derived from the user's open lots for one symbol
  (net quantity and weighted average entry price) and is rewritten by
  `_sync_position` after every change, so it can never drift from the lots.
* SELL closes BUY lots oldest-first (FIFO). CLOSE closes every open lot for
  the symbol. Closing one trade (`close_trade`) closes that lot only. Each
  closed (part of a) lot produces one TradeHistory row with its realised P/L.
* Cash: BUY pays qty x price. SHORT sets aside qty x price as collateral (no
  leverage); covering returns the collateral plus/minus the P/L. Selling long
  shares credits qty x price.

Guarantees
----------
* Execution prices always come from the server-side market quote, never from
  the client. If no real price is available the trade is refused.
* All money/quantity math uses Decimal; cash and P/L are rounded to cents.
* Each operation runs in one transaction and locks the user's row first, so
  concurrent requests for the same user are serialised. Nothing is written
  if any step fails.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Callable, TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.trading import Trade, TradeHistory, TradeStatus, TradeType
from app.models.user import User

logger = logging.getLogger(__name__)

_QUANTITY_STEP = Decimal("0.00000001")  # Numeric(20, 8)
_PRICE_STEP = Decimal("0.000001")  # Numeric(18, 6)
_MONEY_STEP = Decimal("0.01")  # Numeric(18, 2)

_T = TypeVar("_T")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class TradingError(Exception):
    """A trade was refused. Routes turn this into an HTTP error response."""

    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail

    def to_http(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=self.detail)


class InsufficientFundsError(TradingError):
    pass


class InsufficientSharesError(TradingError):
    pass


class InvalidTradeError(TradingError):
    pass


class TradeNotFoundError(TradingError):
    status_code = 404


class MarketDataUnavailableError(TradingError):
    status_code = 503


# ---------------------------------------------------------------------------
# Decimal helpers
# ---------------------------------------------------------------------------

def to_quantity(value: object) -> Decimal:
    return _to_decimal(value).quantize(_QUANTITY_STEP, rounding=ROUND_HALF_UP)


def to_price(value: object) -> Decimal:
    return _to_decimal(value).quantize(_PRICE_STEP, rounding=ROUND_HALF_UP)


def to_money(value: object) -> Decimal:
    return _to_decimal(value).quantize(_MONEY_STEP, rounding=ROUND_HALF_UP)


def _to_decimal(value: object) -> Decimal:
    # str() first so floats keep their shortest repr (0.1 -> "0.1"), not their
    # binary expansion (0.1000000000000000055...).
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation as exc:
        raise InvalidTradeError(f"Invalid numeric value: {value!r}") from exc


def _normalize_symbol(symbol: str) -> str:
    normalized = (symbol or "").strip().upper()
    if not normalized:
        raise InvalidTradeError("Symbol cannot be empty")
    return normalized


def _positive_quantity(quantity: object) -> Decimal:
    qty = to_quantity(quantity)
    if qty <= 0:
        raise InvalidTradeError("Quantity must be greater than zero")
    return qty


# ---------------------------------------------------------------------------
# Market price
# ---------------------------------------------------------------------------

def get_market_price(symbol: str) -> Decimal:
    """Current market price for `symbol`, or MarketDataUnavailableError.

    Uses the same quote source as GET /api/stocks/{symbol}/price (Finnhub, then
    yfinance). Never returns zero, a negative, or a made-up fallback price.
    """
    # Imported lazily: the stocks router pulls in yfinance/pandas.
    from app.api.routes.stocks_extended import _build_live_quote

    try:
        quote = _build_live_quote(symbol)
    except HTTPException as exc:
        raise MarketDataUnavailableError(
            f"Could not get a market price for {symbol}. The trade was not executed."
        ) from exc
    except Exception as exc:  # network/library failures
        logger.warning("Market price lookup failed for %s: %s", symbol, exc)
        raise MarketDataUnavailableError(
            f"Could not get a market price for {symbol}. The trade was not executed."
        ) from exc

    price = getattr(quote, "price", None)
    if price is None or not _to_decimal(price) > 0:
        raise MarketDataUnavailableError(
            f"No valid market price for {symbol}. The trade was not executed."
        )
    return to_price(price)


# ---------------------------------------------------------------------------
# Public operations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TradeRequest:
    symbol: str
    quantity: object
    trade_type: object
    notes: str | None = None


def execute_trade(db: Session, user_id: int, request: TradeRequest) -> Trade:
    """Execute a BUY, SELL, SHORT or CLOSE at the current market price.

    BUY/SHORT return the new open lot. SELL/CLOSE return an EXECUTED trade
    record of the shares that were closed.
    """
    trade_type = TradeType(request.trade_type)
    symbol = _normalize_symbol(request.symbol)
    # CLOSE always closes the whole position; its quantity is not used.
    quantity = None if trade_type == TradeType.CLOSE else _positive_quantity(request.quantity)

    price = get_market_price(symbol)

    def _run() -> Trade:
        user = _lock_user(db, user_id)
        if trade_type == TradeType.BUY:
            trade = _open_long(db, user, symbol, quantity, price, request.notes)
        elif trade_type == TradeType.SHORT:
            trade = _open_short(db, user, symbol, quantity, price, request.notes)
        elif trade_type == TradeType.SELL:
            trade = _sell_long(db, user, symbol, quantity, price, request.notes)
        else:
            trade = _close_all(db, user, symbol, price, request.notes)
        _sync_position(db, user.id, symbol)
        return trade

    return _in_transaction(db, _run)


def close_trade(db: Session, user_id: int, trade_id: int) -> TradeHistory:
    """Close one open BUY or SHORT lot at the current market price."""
    trade = _get_user_trade(db, user_id, trade_id)
    _ensure_closable(trade)

    price = get_market_price(trade.symbol)

    def _run() -> TradeHistory:
        user = _lock_user(db, user_id)
        # Re-read under the lock: another request may have closed it meanwhile.
        lot = _get_user_trade(db, user_id, trade_id, for_update=True)
        _ensure_closable(lot)
        history = _realize(db, user, lot, lot.quantity, price)
        _sync_position(db, user.id, lot.symbol)
        return history

    return _in_transaction(db, _run)


def has_position(db: Session, user_id: int, symbol: str) -> bool:
    return _open_lots(db, user_id, _normalize_symbol(symbol)) != []


# ---------------------------------------------------------------------------
# Operations (run inside _in_transaction with the user row locked)
# ---------------------------------------------------------------------------

def _open_long(db, user, symbol, quantity, price, notes) -> Trade:
    if _open_lots(db, user.id, symbol, TradeType.SHORT):
        raise InvalidTradeError(
            f"You have an open short position in {symbol}. Close it before buying."
        )
    cost = to_money(quantity * price)
    _debit(user, cost)
    return _new_trade(db, user.id, symbol, TradeType.BUY, TradeStatus.OPEN, quantity, price, notes)


def _open_short(db, user, symbol, quantity, price, notes) -> Trade:
    if _open_lots(db, user.id, symbol, TradeType.BUY):
        raise InvalidTradeError(
            f"You hold {symbol} shares. Sell them before opening a short position."
        )
    collateral = to_money(quantity * price)
    _debit(user, collateral)
    return _new_trade(db, user.id, symbol, TradeType.SHORT, TradeStatus.OPEN, quantity, price, notes)


def _sell_long(db, user, symbol, quantity, price, notes) -> Trade:
    lots = _open_lots(db, user.id, symbol, TradeType.BUY)
    owned = sum((lot.quantity for lot in lots), Decimal("0"))
    if owned < quantity:
        raise InsufficientSharesError(
            f"Insufficient shares for {symbol}: you own {owned.normalize()}, tried to sell {quantity.normalize()}"
        )

    remaining = quantity
    for lot in lots:  # oldest first
        if remaining <= 0:
            break
        take = min(lot.quantity, remaining)
        _realize(db, user, lot, take, price)
        remaining -= take

    return _new_trade(db, user.id, symbol, TradeType.SELL, TradeStatus.EXECUTED, quantity, price, notes)


def _close_all(db, user, symbol, price, notes) -> Trade:
    lots = _open_lots(db, user.id, symbol)
    if not lots:
        raise InvalidTradeError(f"No open position in {symbol}")

    closed = Decimal("0")
    for lot in lots:
        closed += lot.quantity
        _realize(db, user, lot, lot.quantity, price)

    return _new_trade(db, user.id, symbol, TradeType.CLOSE, TradeStatus.EXECUTED, closed, price, notes)


def _realize(db, user, lot: Trade, take: Decimal, exit_price: Decimal) -> TradeHistory:
    """Close `take` shares of `lot` at `exit_price`: settle cash, record P/L."""
    entry_value = to_money(take * lot.entry_price)
    exit_value = to_money(take * exit_price)

    if TradeType(lot.trade_type) == TradeType.BUY:
        profit_loss = exit_value - entry_value
        _credit(user, exit_value)
    else:  # SHORT: collateral back, plus the gain (or minus the loss)
        profit_loss = entry_value - exit_value
        cash_change = entry_value + profit_loss
        if cash_change < 0:
            _debit(user, -cash_change)
        else:
            _credit(user, cash_change)

    now = datetime.utcnow()
    history = TradeHistory(
        trade_id=lot.id,
        user_id=user.id,
        symbol=lot.symbol,
        quantity=take,
        entry_price=lot.entry_price,
        exit_price=exit_price,
        profit_loss=profit_loss,
        profit_loss_percent=float(profit_loss / entry_value * 100) if entry_value > 0 else None,
        duration_minutes=int((now - lot.created_at).total_seconds() // 60),
        trade_type=lot.trade_type,
        notes=lot.notes,
        created_at=now,
        closed_at=now,
    )
    db.add(history)

    lot.current_price = exit_price
    lot.updated_at = now
    if take >= lot.quantity:
        # Fully closed; the lot keeps the size it had when it was closed.
        lot.status = TradeStatus.CLOSED
    else:
        lot.quantity = lot.quantity - take
    return history


def _sync_position(db: Session, user_id: int, symbol: str) -> None:
    """Rewrite the Portfolio row for `symbol` from the user's open lots."""
    db.flush()
    lots = _open_lots(db, user_id, symbol)
    position = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id, Portfolio.ticker == symbol)
        .with_for_update()
        .first()
    )

    total_quantity = sum((lot.quantity for lot in lots), Decimal("0"))
    if total_quantity == 0:
        if position is not None:
            db.delete(position)
        return

    # _open_long/_open_short guarantee all open lots are on the same side.
    sign = Decimal("1") if TradeType(lots[0].trade_type) == TradeType.BUY else Decimal("-1")
    average_price = to_price(sum((lot.quantity * lot.entry_price for lot in lots), Decimal("0")) / total_quantity)

    if position is None:
        position = Portfolio(user_id=user_id, ticker=symbol, created_at=datetime.utcnow())
        db.add(position)
    position.quantity = sign * total_quantity
    position.average_price = average_price
    position.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _in_transaction(db: Session, operation: Callable[[], _T]) -> _T:
    try:
        result = operation()
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(result)
    return result


def _lock_user(db: Session, user_id: int) -> User:
    # populate_existing: the request already loaded this user without a lock;
    # re-read the balance now that we hold it.
    return (
        db.query(User)
        .filter(User.id == user_id)
        .with_for_update()
        .populate_existing()
        .one()
    )


def _open_lots(db: Session, user_id: int, symbol: str, trade_type: TradeType | None = None) -> list[Trade]:
    query = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.symbol == symbol,
        Trade.status == TradeStatus.OPEN,
        Trade.trade_type.in_([trade_type] if trade_type else [TradeType.BUY, TradeType.SHORT]),
    )
    return query.order_by(Trade.created_at, Trade.id).with_for_update().all()


def _get_user_trade(db: Session, user_id: int, trade_id: int, for_update: bool = False) -> Trade:
    query = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id)
    if for_update:
        query = query.with_for_update().populate_existing()
    trade = query.first()
    if trade is None:
        raise TradeNotFoundError("Trade not found")
    return trade


def _ensure_closable(trade: Trade) -> None:
    if trade.status == TradeStatus.CLOSED:
        raise InvalidTradeError("Trade is already closed")
    if trade.status != TradeStatus.OPEN or TradeType(trade.trade_type) not in (TradeType.BUY, TradeType.SHORT):
        raise InvalidTradeError("Only open BUY or SHORT trades can be closed")


def _new_trade(db, user_id, symbol, trade_type, status, quantity, price, notes) -> Trade:
    now = datetime.utcnow()
    trade = Trade(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        entry_price=price,
        current_price=price,
        trade_type=trade_type,
        status=status,
        notes=notes,
        created_at=now,
        updated_at=now,
        executed_at=now,
    )
    db.add(trade)
    return trade


def _debit(user: User, amount: Decimal) -> None:
    if user.cash_balance < amount:
        raise InsufficientFundsError(
            f"Insufficient cash: this trade needs ${amount:,.2f} and you have ${user.cash_balance:,.2f}"
        )
    user.cash_balance = to_money(user.cash_balance - amount)


def _credit(user: User, amount: Decimal) -> None:
    user.cash_balance = to_money(user.cash_balance + amount)
