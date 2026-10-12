from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.models.watchlist import Watchlist
from app.api.routes.search import _finnhub_symbol_search

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistTickersResponse(BaseModel):
    tickers: list[str] = Field(description="List of ticker symbols in the watchlist")


class WatchlistAddBody(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=16, description="Stock ticker symbol (e.g. AAPL)")


@router.get("", response_model=WatchlistTickersResponse, summary="Get my watchlist")
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WatchlistTickersResponse:
    """Return all tickers in the current user's watchlist."""
    rows = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.ticker).all()
    return WatchlistTickersResponse(tickers=[r.ticker.upper() for r in rows])


@router.post("", response_model=WatchlistTickersResponse, status_code=status.HTTP_201_CREATED, summary="Add ticker to watchlist")
def add_to_watchlist(
    body: WatchlistAddBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WatchlistTickersResponse:
    """Add a ticker to the current user's watchlist. Duplicates per user are prevented."""
    ticker_upper = body.ticker.strip().upper()
    if not ticker_upper:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticker cannot be empty")

    # Do not persist arbitrary strings as watchlist symbols. Require an exact
    # symbol match from the market symbol provider before adding it.
    matches = _finnhub_symbol_search(ticker_upper)
    valid_symbols = {
        str(item.get("symbol") or item.get("displaySymbol") or "").strip().upper()
        for item in matches
    }
    if ticker_upper not in valid_symbols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{ticker_upper} is not a recognized ticker. Search and choose a valid symbol.",
        )

    existing = db.query(Watchlist).filter(Watchlist.user_id == current_user.id, Watchlist.ticker == ticker_upper).first()
    if existing:
        # Already in watchlist; return current list
        rows = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.ticker).all()
        return WatchlistTickersResponse(tickers=[r.ticker.upper() for r in rows])

    db.add(Watchlist(user_id=current_user.id, ticker=ticker_upper))
    db.commit()

    rows = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.ticker).all()
    return WatchlistTickersResponse(tickers=[r.ticker.upper() for r in rows])


@router.delete("/{ticker}", response_model=WatchlistTickersResponse, summary="Remove ticker from watchlist")
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> WatchlistTickersResponse:
    """Remove a ticker from the current user's watchlist."""
    ticker_upper = ticker.strip().upper()
    deleted = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.ticker == ticker_upper)
        .delete(synchronize_session=False)
    )
    db.commit()

    rows = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).order_by(Watchlist.ticker).all()
    return WatchlistTickersResponse(tickers=[r.ticker.upper() for r in rows])
