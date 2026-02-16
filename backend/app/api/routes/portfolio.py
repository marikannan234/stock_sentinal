from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routes.stock import fetch_stock_quote
from app.models.user import User
from app.models.portfolio import Portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class HoldingItem(BaseModel):
    ticker: str
    quantity: float
    average_price: float


class PortfolioAddBody(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, description="Stock ticker (e.g. AAPL)")
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share for this lot")


class PortfolioSummaryResponse(BaseModel):
    total_invested: float = Field(..., description="Sum of (quantity * average_price) for all holdings")
    current_value: float = Field(..., description="Sum of (quantity * current_price) for all holdings")
    total_pl: float = Field(..., description="Current value minus total invested")
    percent_pl: float = Field(..., description="(total_pl / total_invested) * 100, or 0 if no holdings")


def _holdings_list(db: Session, user_id: int) -> list[HoldingItem]:
    rows = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(Portfolio.ticker)
        .all()
    )
    return [
        HoldingItem(ticker=r.ticker.upper(), quantity=r.quantity, average_price=r.average_price)
        for r in rows
    ]


@router.get("", response_model=list[HoldingItem], summary="Get my portfolio")
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Return all holdings for the current user."""
    return _holdings_list(db, current_user.id)


@router.get("/summary", response_model=PortfolioSummaryResponse, summary="Get portfolio summary")
def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PortfolioSummaryResponse:
    """
    Return total invested, current value, and total P/L for the user's portfolio.
    Uses live quotes from Finnhub; falls back to average price if a quote cannot be fetched.
    """
    holdings = _holdings_list(db, current_user.id)
    total_invested = 0.0
    current_value = 0.0

    for h in holdings:
        cost = h.quantity * h.average_price
        total_invested += cost
        try:
            quote = fetch_stock_quote(h.ticker)
            price = quote.price
        except HTTPException:
            price = h.average_price
        current_value += h.quantity * price

    total_pl = current_value - total_invested
    percent_pl = (total_pl / total_invested * 100) if total_invested > 0 else 0.0

    return PortfolioSummaryResponse(
        total_invested=round(total_invested, 2),
        current_value=round(current_value, 2),
        total_pl=round(total_pl, 2),
        percent_pl=round(percent_pl, 2),
    )


@router.post("", response_model=list[HoldingItem], status_code=status.HTTP_201_CREATED, summary="Add or update position")
def add_or_update_position(
    body: PortfolioAddBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Add shares to a position or create a new position. Recalculates average price."""
    ticker_upper = body.ticker.strip().upper()
    if not ticker_upper:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker cannot be empty")

    existing = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id, Portfolio.ticker == ticker_upper)
        .first()
    )

    if existing:
        # Update: new quantity = old + new, new average = (old_qty * old_avg + new_qty * price) / new_qty
        new_quantity = existing.quantity + body.quantity
        new_average = (existing.quantity * existing.average_price + body.quantity * body.price) / new_quantity
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


@router.delete("/{ticker}", response_model=list[HoldingItem], summary="Remove holding")
def remove_position(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[HoldingItem]:
    """Remove a ticker from the current user's portfolio."""
    ticker_upper = ticker.strip().upper()
    (
        db.query(Portfolio)
        .filter(Portfolio.user_id == current_user.id, Portfolio.ticker == ticker_upper)
        .delete(synchronize_session=False)
    )
    db.commit()
    return _holdings_list(db, current_user.id)
