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
from app.models.trading import Trade, TradeHistory, TradeStatus, TradeType
from app.models.portfolio import Portfolio
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


def _update_portfolio_from_trade(
    user_id: int,
    symbol: str,
    quantity: float,
    price: float,
    trade_type: str,
    db: Session,
) -> None:
    """Update user's portfolio based on trade."""

    # Coerce to string in case it's a Pydantic enum or TradeType enum
    normalized_trade_type = str(trade_type)
    ticker = symbol.upper()
    portfolio = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.ticker == ticker
    ).first()

    if normalized_trade_type == TradeType.BUY.value:
        if portfolio:
            portfolio.quantity += quantity
            portfolio.average_price = (
                (portfolio.average_price * (portfolio.quantity - quantity) + price * quantity) 
                / portfolio.quantity
            )
        else:
            portfolio = Portfolio(
                user_id=user_id,
                ticker=ticker,
                quantity=quantity,
                average_price=price,
                created_at=datetime.utcnow(),
            )
            db.add(portfolio)

    elif normalized_trade_type == TradeType.SELL.value:
        if portfolio:
            if portfolio.quantity >= quantity:
                portfolio.quantity -= quantity
                if portfolio.quantity == 0:
                    db.delete(portfolio)
            else:
                raise ValueError(f"Insufficient shares for {ticker}")

    elif normalized_trade_type == TradeType.SHORT.value:
        if portfolio:
            portfolio.quantity -= quantity
        else:
            portfolio = Portfolio(
                user_id=user_id,
                ticker=ticker,
                quantity=-quantity,
                average_price=price,
                created_at=datetime.utcnow(),
            )
            db.add(portfolio)

    elif normalized_trade_type == TradeType.CLOSE.value:
        if portfolio:
            portfolio.quantity = 0
            db.delete(portfolio)


@router.post("/", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    trade_create: TradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Trade:
    """Create a new trade."""
    
    try:
        _update_portfolio_from_trade(
            user_id=current_user.id,
            symbol=trade_create.symbol,
            quantity=trade_create.quantity,
            price=trade_create.entry_price,
            trade_type=trade_create.trade_type,
            db=db,
        )
        
        trade = Trade(
            user_id=current_user.id,
            symbol=trade_create.symbol,
            quantity=trade_create.quantity,
            entry_price=trade_create.entry_price,
            current_price=trade_create.entry_price,
            trade_type=TradeType(trade_create.trade_type),
            status=TradeStatus.OPEN,
            created_at=datetime.utcnow(),
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        logger.info(f"Trade {trade.id} created for user {current_user.id}: {trade_create.symbol}")
        return trade
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
    """Update a trade."""
    
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )
    
    update_data = trade_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                value = _parse_trade_status(value)
            setattr(trade, field, value)
    
    trade.updated_at = datetime.utcnow()
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    logger.info(f"Trade {trade.id} updated by user {current_user.id}")
    return trade


@router.post("/{trade_id}/close", response_model=TradeHistoryRead)
def close_trade(
    trade_id: int,
    exit_price: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> TradeHistory:
    """Close a trade and move to history."""
    
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )
    
    if trade.status == TradeStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade is already closed",
        )
    
    # Calculate profit/loss
    if trade.trade_type in {TradeType.BUY, TradeType.SHORT}:
        profit_loss = (exit_price - trade.entry_price) * trade.quantity
    else:
        profit_loss = 0.0

    profit_loss_percent = None
    if trade.entry_price > 0:
        profit_loss_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100

    # Calculate duration
    duration_minutes = int((datetime.utcnow() - trade.created_at).total_seconds() / 60)
    
    # Create history record
    history = TradeHistory(
        trade_id=trade.id,
        user_id=current_user.id,
        symbol=trade.symbol,
        quantity=trade.quantity,
        entry_price=trade.entry_price,
        exit_price=exit_price,
        profit_loss=profit_loss,
        profit_loss_percent=profit_loss_percent,
        duration_minutes=duration_minutes,
        trade_type=trade.trade_type,
        notes=trade.notes,
        closed_at=datetime.utcnow(),
    )
    
    # Update trade status
    trade.status = TradeStatus.CLOSED
    trade.current_price = exit_price
    trade.updated_at = datetime.utcnow()
    
    db.add(trade)
    db.add(history)
    db.commit()
    db.refresh(history)
    
    logger.info(f"Trade {trade.id} closed by user {current_user.id}")
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
