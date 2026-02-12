from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from app.config import settings
import threading
import time
from typing import Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

router = APIRouter(prefix="/stock", tags=["stock"])

_CACHE_TTL_SECONDS = 5 * 60


@dataclass(frozen=True)
class _CacheEntry:
    expires_at_monotonic: float
    value: StockDataResponse


_cache_lock = threading.Lock()
_stock_cache: Dict[str, _CacheEntry] = {}


def _cache_get(ticker: str) -> Optional[StockDataResponse]:
    now = time.monotonic()
    with _cache_lock:
        entry = _stock_cache.get(ticker)
        if not entry:
            return None
        if entry.expires_at_monotonic <= now:
            _stock_cache.pop(ticker, None)
            return None
        return entry.value


def _cache_set(ticker: str, value: StockDataResponse) -> None:
    expires = time.monotonic() + _CACHE_TTL_SECONDS
    with _cache_lock:
        _stock_cache[ticker] = _CacheEntry(expires_at_monotonic=expires, value=value)


def _is_rate_limited_error(exc: Exception) -> bool:
    """
    Best-effort detection of Yahoo Finance throttling.
    yfinance may surface this in different exception shapes/messages.
    """
    msg = str(exc).lower()
    if "429" in msg or "too many requests" in msg or "rate limit" in msg:
        return True
    # Some underlying HTTP libraries expose status_code / response
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) == 429:
        return True
    return False


class PriceDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDataResponse(BaseModel):
    ticker: str
    name: str | None
    currency: str | None
    period_days: int
    data_points: List[PriceDataPoint]


@router.get("/{ticker}", response_model=StockDataResponse, summary="Get stock price data")
def get_stock_data(
    ticker: str = Path(..., description="Stock ticker symbol (e.g., AAPL, TSLA)", min_length=1, max_length=10)
) -> StockDataResponse:
    """
    Fetch the last 30 days of daily price data for a given stock ticker.
    
    Returns OHLCV (Open, High, Low, Close, Volume) data points.
    """
    # Normalize ticker to uppercase
    ticker_upper = ticker.upper().strip()
    
    if not ticker_upper:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")

    cached = _cache_get(ticker_upper)
    if cached is not None:
        return cached
    
    try:
        api_key = settings.FINNHUB_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="FINNHUB_API_KEY is not configured on the server.",
            )

        base_url = "https://finnhub.io/api/v1/stock/candle"

        def fetch_candles(days: int) -> dict:
            now = int(time.time())
            start = now - days * 24 * 60 * 60
            params = {
                "symbol": ticker_upper,
                "resolution": "D",
                "from": start,
                "to": now,
                "token": api_key,
            }
            try:
                print("Fetching stock data from Finnhub for", ticker_upper)
                resp = requests.get(base_url, params=params, timeout=10)
            except Exception as exc:
                # Network/requests-level error or timeout
                raise HTTPException(
                    status_code=502,
                    detail="Failed to fetch stock data from Finnhub.",
                )

            if resp.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Finnhub rate limit reached. Please wait a few minutes and try again. "
                        "If this persists, reduce request frequency."
                    ),
                )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Finnhub API error (status {resp.status_code}).",
                )

            return resp.json()

        data = fetch_candles(30)

        if data.get("s") != "ok" or not data.get("t"):
            # Small delay then retry with a longer window
            time.sleep(1)
            data = fetch_candles(90)

        if data.get("s") != "ok" or not data.get("t"):
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for ticker '{ticker_upper}'. The ticker may be invalid or delisted.",
            )

        timestamps = data.get("t", [])
        opens = data.get("o", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        closes = data.get("c", [])
        volumes = data.get("v", [])

        # Convert Finnhub response to list of PriceDataPoint
        data_points: List[PriceDataPoint] = []
        for ts, o, h, l, c, v in zip(
            timestamps, opens, highs, lows, closes, volumes
        ):
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
            data_points.append(
                PriceDataPoint(
                    date=date_str,
                    open=float(o),
                    high=float(h),
                    low=float(l),
                    close=float(c),
                    volume=int(v),
                )
            )
        
        # Use simple defaults; Finnhub has per-symbol metadata but we avoid extra calls.
        name = ticker_upper
        currency = "USD"
        
        response = StockDataResponse(
            ticker=ticker_upper,
            name=name,
            currency=currency,
            period_days=30,
            data_points=data_points,
        )

        _cache_set(ticker_upper, response)
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle yfinance errors and other unexpected errors
        if _is_rate_limited_error(e):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Yahoo Finance rate limit reached. Please wait a few minutes and try again. "
                    "If this persists, reduce request frequency."
                ),
            )

        error_msg = str(e)
        if "No data found" in error_msg or "symbol may be delisted" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker_upper}' not found or has no available data."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stock data for '{ticker_upper}': {error_msg}"
        )
