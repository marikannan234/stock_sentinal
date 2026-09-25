"""
Trading endpoints for managing trades and trade history.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.models.trading import Trade, TradeHistory, TradeStatus
from app.services import trading_service
from app.services.trading_service import TradeRequest, TradingError
from app.schemas.trading import (
    TradeCreate,
    TradeRead,
    TradeUpdate,
    TradeHistoryRead,
    TradeHistorySummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trade", tags=["trading"])


def _parse_trade_status(status_value: str) -> TradeStatus:
    """Convert a raw status string into the model enum with a clean client error."""

    try:
        return TradeStatus(status_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid trade status: {status_value}",
        ) from exc




@router.post("/", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    trade_create: TradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Trade:
    """Execute a trade at the current market price.

    `entry_price` in the request body is ignored: the execution price is
    always resolved server-side. BUY/SHORT open a position; SELL reduces a
    long position; CLOSE closes the whole position (quantity is ignored).
    """
    try:
        trade = trading_service.execute_trade(
            db,
            current_user.id,
            TradeRequest(
                symbol=trade_create.symbol,
                quantity=trade_create.quantity,
                trade_type=trade_create.trade_type,
                notes=trade_create.notes,
            ),
        )
    except TradingError as exc:
        raise exc.to_http() from exc

    logger.info(f"Trade {trade.id} executed for user {current_user.id}: {trade.trade_type.value} {trade.symbol}")
    return trade


@router.get("/", response_model=List[TradeRead])
def list_user_trades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    status_filter: Optional[str] = Query(None),
    symbol_filter: Optional[str] = Query(None),
) -> List[Trade]:
    """Get all trades for current user."""
    
    query = db.query(Trade).filter(Trade.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Trade.status == _parse_trade_status(status_filter))
    
    if symbol_filter:
        query = query.filter(Trade.symbol == symbol_filter.upper())
    
    trades = query.order_by(desc(Trade.created_at)).all()
    return trades


@router.get("/{trade_id}", response_model=TradeRead)
def get_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Trade:
    """Get a specific trade."""
    
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )
    
    return trade



@router.put("/{trade_id}", response_model=TradeRead)
def update_trade(
    trade_id: int,
    trade_update: TradeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Trade:
    """Update a trade's notes.

    Status and prices are managed by the server: use POST /trade/{id}/close to
    close a trade. Changing them here would desynchronise the portfolio.
    """
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    # A closed trade already has a history row; reopening it would let the
    # same trade be closed (and its P/L counted) twice.
    if trade.status == TradeStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed trades cannot be modified",
        )

    update_data = trade_update.dict(exclude_unset=True)
    if update_data.get("status") is not None:
        if _parse_trade_status(update_data["status"]) == TradeStatus.CLOSED:
            detail = "Use POST /trade/{trade_id}/close to close a trade"
        else:
            detail = "Trade status is managed by the server"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if update_data.get("current_price") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade prices are set by the server",
        )

    if "notes" in update_data:
        trade.notes = update_data["notes"]
    trade.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(trade)

    logger.info(f"Trade {trade.id} updated by user {current_user.id}")
    return trade


@router.post("/{trade_id}/close", response_model=TradeHistoryRead)
def close_trade(
    trade_id: int,
    exit_price: Optional[float] = Query(
        None,
        deprecated=True,
        description="Ignored. Trades are closed at the current market price.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> TradeHistory:
    """Close an open BUY or SHORT trade at the current market price."""
    try:
        history = trading_service.close_trade(db, current_user.id, trade_id)
    except TradingError as exc:
        raise exc.to_http() from exc

    logger.info(f"Trade {trade_id} closed by user {current_user.id}")
    return history


@router.get("/history/list", response_model=List[TradeHistoryRead])
def get_trade_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    symbol_filter: Optional[str] = Query(None),
) -> List[dict]:
    """Get trade history for current user with computed status."""
    
    query = db.query(TradeHistory).filter(TradeHistory.user_id == current_user.id)
    
    if symbol_filter:
        query = query.filter(TradeHistory.symbol == symbol_filter.upper())
    
    history = query.order_by(desc(TradeHistory.created_at)).all()
    
    # Compute status for each trade
    result = []
    for trade in history:
        trade_dict = {
            "id": trade.id,
            "user_id": trade.user_id,
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "trade_type": trade.trade_type.value if hasattr(trade.trade_type, "value") else str(trade.trade_type),
            "profit_loss": trade.profit_loss,
            "profit_loss_percent": trade.profit_loss_percent,
            "duration_minutes": trade.duration_minutes,
            "notes": trade.notes,
            "created_at": trade.created_at,
            "closed_at": trade.closed_at,
            "status": "closed" if trade.exit_price is not None else "open"
        }
        result.append(trade_dict)
    
    return result


@router.get("/history/summary", response_model=TradeHistorySummary)
def get_trade_history_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> TradeHistorySummary:
    """Get trade history summary (total trades, win rate, net profit, avg execution)."""
    
    trades = db.query(TradeHistory).filter(
        TradeHistory.user_id == current_user.id,
        TradeHistory.exit_price.isnot(None)  # Only closed trades
    ).all()
    
    if not trades:
        return TradeHistorySummary(
            total_trades=0,
            win_rate=0.0,
            net_profit=0.0,
            avg_execution=None,
        )
    
    total_trades = len(trades)
    
    # Calculate net profit
    profit_values = [t.profit_loss for t in trades if t.profit_loss is not None]
    net_profit = sum(profit_values) if profit_values else 0.0
    
    # Calculate win rate
    winning_trades = sum(1 for profit in profit_values if profit and profit > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    # Calculate average execution time
    durations = [t.duration_minutes for t in trades if t.duration_minutes is not None]
    avg_execution = sum(durations) / len(durations) if durations else None
    
    return TradeHistorySummary(
        total_trades=total_trades,
        win_rate=round(win_rate, 2),
        net_profit=round(net_profit, 2),
        avg_execution=round(avg_execution, 2) if avg_execution else None,
    )


@router.get("/summary/stats", response_model=TradeHistorySummary)
def get_trade_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> TradeHistorySummary:
    """Get trade statistics summary."""
    
    trades = db.query(TradeHistory).filter(
        TradeHistory.user_id == current_user.id
    ).all()
    
    if not trades:
        return TradeHistorySummary(
            total_trades=0,
            win_rate=0.0,
            net_profit=0.0,
            avg_execution=None,
        )
    
    total_trades = len(trades)
    profit_values = [t.profit_loss for t in trades if t.profit_loss is not None]
    winning_trades = sum(1 for profit in profit_values if profit and profit > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    net_profit = sum(profit_values) if profit_values else 0.0
    
    durations = [t.duration_minutes for t in trades if t.duration_minutes is not None]
    avg_execution = sum(durations) / len(durations) if durations else None
    
    return TradeHistorySummary(
        total_trades=total_trades,
        win_rate=round(win_rate, 2),
        net_profit=round(net_profit, 2),
        avg_execution=round(avg_execution, 2) if avg_execution else None,
    )
