import logging
from datetime import datetime

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routes.stock import fetch_stock_quote
from app.models.user import User
from app.models.portfolio import Portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)


class HoldingItem(BaseModel):
    ticker: str
    quantity: float
    average_price: float
    current_price: float | None = None
    current_value: float | None = None
    invested_amount: float | None = None
    pl_amount: float | None = None
    pl_percent: float | None = None
    day_change: float | None = None
    day_change_percent: float | None = None
    name: str | None = None
    asset_class: str | None = None


class PortfolioAddBody(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, description="Stock ticker (e.g. AAPL)")
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share for this lot")


class PortfolioSummaryResponse(BaseModel):
    total_invested: float = Field(..., description="Sum of (quantity * average_price) for all holdings")
    current_value: float = Field(..., description="Sum of (quantity * current_price) for all holdings")
    total_pl: float = Field(..., description="Current value minus total invested")
    percent_pl: float = Field(..., description="(total_pl / total_invested) * 100, or 0 if no holdings")
    day_pl: float = Field(..., description="Today's profit/loss across the portfolio")
    day_percent: float = Field(..., description="Today's profit/loss percentage")
    buying_power: float = Field(..., description="Available cash buying power if known, otherwise 0")


class AllocationItem(BaseModel):
    category: str
    value: float
    percent: float


class PortfolioAllocationResponse(BaseModel):
    total_value: float
    allocations: list[AllocationItem]


class PortfolioGrowthPoint(BaseModel):
    date: str
    value: float


class PortfolioRemoveBody(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, description="Stock ticker to remove")


def _holdings_list(db: Session, user_id: int) -> list[HoldingItem]:
    rows = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(Portfolio.ticker)
        .all()
    )
    return [
        HoldingItem(
            ticker=r.ticker.upper(),
            quantity=r.quantity,
            average_price=r.average_price,
            name=_resolve_asset_name(r.ticker.upper()),
            asset_class=_classify_asset(r.ticker.upper()),
        )
        for r in rows
    ]


KNOWN_ASSET_NAMES = {
    "AAPL": "Apple Inc.",
    "AMD": "AMD Inc.",
    "AMZN": "Amazon.com Inc.",
    "BTC": "Bitcoin",
    "COIN": "Coinbase",
    "ETH": "Ethereum",
    "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms",
    "MSFT": "Microsoft Corp.",
    "NFLX": "Netflix",
    "NVDA": "NVIDIA Corp.",
    "TSLA": "Tesla, Inc.",
    "WMT": "Walmart Inc.",
}

CRYPTO_TICKERS = {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "BNB", "AVAX", "MSTR", "COIN", "RIOT", "MARA"}
CONSUMER_TICKERS = {"TSLA", "AMZN", "WMT", "HD", "MCD", "NKE", "SBUX", "COST", "DIS", "NFLX"}
TECHNOLOGY_TICKERS = {"AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "INTC", "CRM", "ADBE", "CSCO", "ORCL"}


def _resolve_asset_name(ticker: str) -> str:
    return KNOWN_ASSET_NAMES.get(ticker.upper(), ticker.upper())


def _classify_asset(ticker: str) -> str:
    normalized = ticker.upper()
    if normalized in CRYPTO_TICKERS:
        return "Crypto"
    if normalized in CONSUMER_TICKERS:
        return "Consumer"
    if normalized in TECHNOLOGY_TICKERS:
        return "Technology"
    return "Technology"


def _enrich_holding(holding: HoldingItem) -> HoldingItem:
    quantity = float(holding.quantity or 0)
    average_price = float(holding.average_price or 0)
    invested_amount = quantity * average_price

    current_price = average_price
    previous_close = average_price
    try:
        quote = fetch_stock_quote(holding.ticker)
        current_price = float(quote.price or average_price)
        previous_close = float(quote.previous_close or current_price)
    except HTTPException:
        pass

    current_value = quantity * current_price
    pl_amount = current_value - invested_amount
    pl_percent = (pl_amount / invested_amount * 100) if invested_amount > 0 else 0.0
    day_change = quantity * (current_price - previous_close)
    day_percent = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0.0

    return HoldingItem(
        ticker=holding.ticker,
        quantity=holding.quantity,
        average_price=holding.average_price,
        current_price=round(current_price, 2),
        current_value=round(current_value, 2),
        invested_amount=round(invested_amount, 2),
        pl_amount=round(pl_amount, 2),
        pl_percent=round(pl_percent, 2),
        day_change=round(day_change, 2),
        day_change_percent=round(day_percent, 2),
        name=holding.name or _resolve_asset_name(holding.ticker),
        asset_class=holding.asset_class or _classify_asset(holding.ticker),
    )


def _enriched_holdings(db: Session, user_id: int) -> list[HoldingItem]:
    return [_enrich_holding(holding) for holding in _holdings_list(db, user_id)]


@router.get("", response_model=list[HoldingItem], summary="Get my portfolio")
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Return all holdings for the current user."""
    logger.info("Portfolio requested", extra={"user_id": current_user.id})
    return _enriched_holdings(db, current_user.id)


@router.get("/summary", response_model=PortfolioSummaryResponse, summary="Get portfolio summary")
def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PortfolioSummaryResponse:
    """
    Return total invested, current value, and total P/L for the user's portfolio.
    Uses live quotes from Finnhub; falls back to average price if a quote cannot be fetched.
    """
    logger.info("Portfolio summary requested", extra={"user_id": current_user.id})
    holdings = _enriched_holdings(db, current_user.id)
    total_invested = sum(float(holding.invested_amount or 0) for holding in holdings)
    current_value = sum(float(holding.current_value or 0) for holding in holdings)
    day_pl = sum(float(holding.day_change or 0) for holding in holdings)
    total_pl = current_value - total_invested
    percent_pl = (total_pl / total_invested * 100) if total_invested > 0 else 0.0
    day_percent = (day_pl / (current_value - day_pl) * 100) if (current_value - day_pl) > 0 else 0.0

    return PortfolioSummaryResponse(
        total_invested=round(total_invested, 2),
        current_value=round(current_value, 2),
        total_pl=round(total_pl, 2),
        percent_pl=round(percent_pl, 2),
        day_pl=round(day_pl, 2),
        day_percent=round(day_percent, 2),
        buying_power=0.0,
    )


@router.get("/allocation", response_model=PortfolioAllocationResponse, summary="Get portfolio asset allocation")
def get_portfolio_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PortfolioAllocationResponse:
    """Return portfolio allocation grouped into Technology, Crypto, Consumer, and fallbacks."""
    logger.info("Portfolio allocation requested", extra={"user_id": current_user.id})
    holdings = _enriched_holdings(db, current_user.id)
    total_value = sum(float(holding.current_value or 0) for holding in holdings)
    grouped: dict[str, float] = {}

    for holding in holdings:
        category = holding.asset_class or _classify_asset(holding.ticker)
        grouped[category] = grouped.get(category, 0.0) + float(holding.current_value or 0)

    allocations = [
        AllocationItem(
            category=category,
            value=round(value, 2),
            percent=round((value / total_value * 100) if total_value > 0 else 0.0, 2),
        )
        for category, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    ]

    return PortfolioAllocationResponse(
        total_value=round(total_value, 2),
        allocations=allocations,
    )


_GROWTH_RANGE_CONFIG: dict[str, tuple[str, str, int]] = {
    "1d": ("5d", "1h", 24),
    "1w": ("1mo", "1d", 7),
    "1m": ("3mo", "1d", 31),
    "1y": ("1y", "1wk", 53),
}


@router.get("/growth", response_model=list[PortfolioGrowthPoint], summary="Get portfolio growth history")
def get_portfolio_growth(
    range_key: str = Query("1y", alias="range", pattern="^(1d|1w|1m|1y)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[PortfolioGrowthPoint]:
    """Return historical portfolio value points for the selected time range."""
    logger.info("Portfolio growth requested", extra={"user_id": current_user.id, "range": range_key})
    holdings = _holdings_list(db, current_user.id)
    if not holdings:
        return []

    period, interval, max_points = _GROWTH_RANGE_CONFIG[range_key]
    portfolio_points: dict[str, float] = {}

    for holding in holdings:
        try:
            history = yf.Ticker(holding.ticker).history(period=period, interval=interval, auto_adjust=False)
        except Exception:
            history = None

        if history is None or history.empty:
            continue

        quantity = float(holding.quantity or 0)
        for idx, row in history.iterrows():
            if getattr(idx, "tzinfo", None) is not None:
                idx = idx.tz_convert(None)
            date_label = idx.strftime("%Y-%m-%d %H:%M") if range_key == "1d" else idx.strftime("%Y-%m-%d")
            close_price = float(row.get("Close") or 0)
            portfolio_points[date_label] = portfolio_points.get(date_label, 0.0) + (close_price * quantity)

    sorted_points = sorted(
        (PortfolioGrowthPoint(date=date_key, value=round(value, 2)) for date_key, value in portfolio_points.items()),
        key=lambda point: datetime.fromisoformat(point.date),
    )
    if len(sorted_points) > max_points:
        sorted_points = sorted_points[-max_points:]
    return sorted_points


@router.post("", response_model=list[HoldingItem], status_code=status.HTTP_201_CREATED, summary="Add or update position")
def add_or_update_position(
    body: PortfolioAddBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Add shares to a position or create a new position. Recalculates average price."""
    ticker_upper = body.ticker.strip().upper()
    logger.info("Portfolio add/update requested", extra={"user_id": current_user.id, "ticker": ticker_upper})
    if not ticker_upper:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker cannot be empty")

    existing = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id, Portfolio.ticker == ticker_upper)
        .first()
    )

    if existing:
        # Update: new quantity = old + new, new average = (old_qty * old_avg + new_qty * price) / new_qty
        new_quantity = float(existing.quantity or 0) + body.quantity
        if new_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Updated quantity must be greater than zero",
            )
        new_average = ((float(existing.quantity or 0) * float(existing.average_price or 0)) + (body.quantity * body.price)) / new_quantity
        existing.quantity = new_quantity
        existing.average_price = new_average
        db.commit()
    else:
        db.add(
            Portfolio(
                user_id=current_user.id,
                ticker=ticker_upper,
                quantity=body.quantity,
                average_price=body.price,
            )
        )
        db.commit()

    return _holdings_list(db, current_user.id)


@router.post("/remove", response_model=list[HoldingItem], summary="Remove holding by body")
def remove_position_by_body(
    body: PortfolioRemoveBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Remove a ticker from the current user's portfolio using a request body."""
    return _remove_position(body.ticker, current_user, db)


@router.delete("/{ticker}", response_model=list[HoldingItem], summary="Remove holding")
def remove_position(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Remove a ticker from the current user's portfolio."""
    return _remove_position(ticker, current_user, db)


def _remove_position(
    ticker: str,
    current_user: User,
    db: Session,
) -> list[HoldingItem]:
    ticker_upper = ticker.strip().upper()
    logger.info("Portfolio remove requested", extra={"user_id": current_user.id, "ticker": ticker_upper})
    if not ticker_upper:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker cannot be empty")

    position = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id, Portfolio.ticker == ticker_upper)
        .first()
    )
    if not position:
        return _holdings_list(db, current_user.id)

    db.delete(position)
    db.commit()
    return _holdings_list(db, current_user.id)
