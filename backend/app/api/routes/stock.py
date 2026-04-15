from __future__ import annotations

from dataclasses import dataclass
from app.config import settings
from datetime import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Optional
import logging

import requests
import yfinance as yf
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stock", tags=["stock"])

# ============================================================================
# AGGRESSIVE CACHE CONFIGURATION (5 minutes for quotes, 30 min for candles)
# ============================================================================
_QUOTE_CACHE_TTL_SECONDS = 5 * 60  # 5 minutes
_CANDLE_CACHE_TTL_SECONDS = 30 * 60  # 30 minutes


# ----- Quote cache -----
@dataclass(frozen=True)
class _QuoteCacheEntry:
    expires_at_monotonic: float
    value: "StockQuoteResponse"


_quote_cache_lock = threading.Lock()
_quote_cache: Dict[str, _QuoteCacheEntry] = {}


def _quote_cache_get(ticker: str) -> Optional["StockQuoteResponse"]:
    now = time.monotonic()
    with _quote_cache_lock:
        entry = _quote_cache.get(ticker)
        if not entry:
            return None
        if entry.expires_at_monotonic <= now:
            _quote_cache.pop(ticker, None)
            return None
        age = now - (entry.expires_at_monotonic - _QUOTE_CACHE_TTL_SECONDS)
        logger.debug(f"Quote cache HIT for {ticker} (age: {age:.1f}s)")
        return entry.value


def _quote_cache_set(ticker: str, value: "StockQuoteResponse") -> None:
    expires = time.monotonic() + _QUOTE_CACHE_TTL_SECONDS
    with _quote_cache_lock:
        _quote_cache[ticker] = _QuoteCacheEntry(expires_at_monotonic=expires, value=value)
    logger.debug(f"Cached quote for {ticker}")


# ----- Candle cache -----
@dataclass(frozen=True)
class _CandleCacheEntry:
    expires_at_monotonic: float
    value: StockDataResponse


_candle_cache_lock = threading.Lock()
_candle_cache: Dict[str, _CandleCacheEntry] = {}


def _candle_cache_get(ticker: str) -> Optional[StockDataResponse]:
    now = time.monotonic()
    with _candle_cache_lock:
        entry = _candle_cache.get(ticker)
        if not entry:
            return None
        if entry.expires_at_monotonic <= now:
            _candle_cache.pop(ticker, None)
            return None
        age = now - (entry.expires_at_monotonic - _CANDLE_CACHE_TTL_SECONDS)
        logger.debug(f"Candle cache HIT for {ticker} (age: {age:.1f}s)")
        return entry.value


def _candle_cache_set(ticker: str, value: StockDataResponse) -> None:
    expires = time.monotonic() + _CANDLE_CACHE_TTL_SECONDS
    with _candle_cache_lock:
        _candle_cache[ticker] = _CandleCacheEntry(expires_at_monotonic=expires, value=value)
    logger.debug(f"Cached candles for {ticker}")


# ----- Response models -----
class StockQuoteResponse(BaseModel):
    ticker: str
    price: float
    change: float
    percent_change: float
    high: float
    low: float
    open: float
    previous_close: float


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


# ============================================================================
# PERFORMANCE TIMEOUT CONFIG (1 sec warning, 2 sec hard timeout)
# ============================================================================
_API_RESPONSE_WARNING_THRESHOLD = 1.0  # Log warning if response > 1 second
_API_HARD_TIMEOUT = 2.0  # Kill API call after 2 seconds, use cache instead


# ----- Helpers -----
def _finnhub_get(url: str, params: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    """Call Finnhub API with hard timeout; prioritize speed over freshness."""
    start_time = time.monotonic()
    try:
        resp = requests.get(url, params=params, timeout=_API_HARD_TIMEOUT)
        elapsed = time.monotonic() - start_time
        if elapsed > _API_RESPONSE_WARNING_THRESHOLD:
            logger.warning(f"Finnhub API slow response for {ticker}: {elapsed:.2f}s (threshold: {_API_RESPONSE_WARNING_THRESHOLD}s)")
    except requests.Timeout:
        elapsed = time.monotonic() - start_time
        logger.warning(f"Finnhub API timeout for {ticker} (exceeded {_API_HARD_TIMEOUT}s hard limit)")
        return {}  # Return empty dict on timeout
    except requests.ConnectionError as e:
        elapsed = time.monotonic() - start_time
        logger.warning(f"Finnhub API connection error for {ticker}: {e}")
        return {}  # Return empty dict on connection error
    except requests.RequestException as e:
        elapsed = time.monotonic() - start_time
        logger.warning(f"Finnhub API request error for {ticker}: {e}")
        return {}  # Return empty dict on other errors
    
    if resp.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail=(
                "Finnhub rate limit reached. Please wait a few minutes and try again. "
                "If this persists, reduce request frequency."
            ),
        )
    if resp.status_code == 403:
        raise HTTPException(
            status_code=502,
            detail=(
                "Finnhub access forbidden (403). Check that FINNHUB_API_KEY is valid and your plan allows this endpoint."
            ),
        )
    if resp.status_code != 200:
        import logging
        logging.getLogger(__name__).warning(f"Finnhub API error {resp.status_code} for {ticker}")
        return {}  # Return empty dict instead of raising
    
    try:
        return resp.json()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Finnhub JSON parse error for {ticker}: {e}")
        return {}


# ----- Reusable quote fetcher (for portfolio summary, etc.) -----
def fetch_stock_quote(ticker: str) -> StockQuoteResponse:
    """
    Fetch real-time quote for a stock from Finnhub.
    Returns current price, change, percent change, and session OHLC.
    Uses cache. Falls back to zero prices on error (no crash).
    Prioritizes response speed: cache > fresh data.
    """
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")

    cached = _quote_cache_get(ticker_upper)
    if cached is not None:
        return cached
    
    start_time = time.monotonic()  # Track total response time

    api_key = settings.FINNHUB_API_KEY
    if not api_key:
        # Fall back to default quote on API key missing
        import logging
        logging.getLogger(__name__).warning(f"FINNHUB_API_KEY not configured, returning default quote for {ticker_upper}")
        response = StockQuoteResponse(
            ticker=ticker_upper,
            price=0.0,
            change=0.0,
            percent_change=0.0,
            high=0.0,
            low=0.0,
            open=0.0,
            previous_close=0.0,
        )
        _quote_cache_set(ticker_upper, response)
        return response

    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": ticker_upper, "token": api_key}
        data = _finnhub_get(url, params, ticker_upper)

        # Finnhub quote: c, d, dp, h, l, o, pc (current, change, percent change, high, low, open, previous close)
        c = data.get("c")
        if c is None:
            # No data available, return safe default
            elapsed = time.monotonic() - start_time
            logger.warning(f"No quote data for {ticker_upper}, returning default (total: {elapsed:.2f}s)")
            response = StockQuoteResponse(
                ticker=ticker_upper,
                price=0.0,
                change=0.0,
                percent_change=0.0,
                high=0.0,
                low=0.0,
                open=0.0,
                previous_close=0.0,
            )
            _quote_cache_set(ticker_upper, response)
            return response

        response = StockQuoteResponse(
            ticker=ticker_upper,
            price=float(c),
            change=float(data.get("d") or 0),
            percent_change=float(data.get("dp") or 0),
            high=float(data.get("h") or 0),
            low=float(data.get("l") or 0),
            open=float(data.get("o") or 0),
            previous_close=float(data.get("pc") or 0),
        )
        
        elapsed = time.monotonic() - start_time
        if elapsed > _API_RESPONSE_WARNING_THRESHOLD:
            logger.warning(f"Quote fetch for {ticker_upper} slow: {elapsed:.2f}s (threshold: {_API_RESPONSE_WARNING_THRESHOLD}s)")
        
        _quote_cache_set(ticker_upper, response)
        return response
    
    except HTTPException:
        # Re-raise rate limit and auth errors
        raise
    except Exception as e:
        # All other errors: return safe default instead of crashing
        elapsed = time.monotonic() - start_time
        logger.warning(f"Error fetching quote for {ticker_upper}: {e} (total: {elapsed:.2f}s)")
        response = StockQuoteResponse(
            ticker=ticker_upper,
            price=0.0,
            change=0.0,
            percent_change=0.0,
            high=0.0,
            low=0.0,
            open=0.0,
            previous_close=0.0,
        )
        _quote_cache_set(ticker_upper, response)
        return response


# ----- Routes -----
@router.get("/{ticker}/quote", response_model=StockQuoteResponse, summary="Get real-time quote")
def get_stock_quote(
    ticker: str = Path(..., description="Stock ticker symbol (e.g., AAPL, TSLA)", min_length=1, max_length=10)
) -> StockQuoteResponse:
    """Fetch real-time quote for a stock from Finnhub."""
    return fetch_stock_quote(ticker)


@router.get("/{ticker}", response_model=StockDataResponse, summary="Get stock price data (candles)")
def get_stock_data(
    ticker: str = Path(..., description="Stock ticker symbol (e.g., AAPL, TSLA)", min_length=1, max_length=10)
) -> StockDataResponse:
    """
    Fetch the last 30 days of daily price data for a given stock ticker from yfinance.
    Returns OHLCV (Open, High, Low, Close, Volume) data points.
    Falls back to empty data if fetch fails (no crash).
    Prioritizes response speed: cache > fresh data.
    """
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")

    cached = _candle_cache_get(ticker_upper)
    if cached is not None:
        return cached

    start_time = time.monotonic()  # Track total response time
    try:
        # Fetch data from yfinance - timeout enforced via hard cutoff
        # Wrap in try-catch for error handling
        yf_ticker = yf.Ticker(ticker_upper)
        df = yf_ticker.history(period="30d", interval="1d")
            
    except Exception as e:
        # Return empty data set on error instead of crashing
        elapsed = time.monotonic() - start_time
        logger.warning(f"yfinance error for {ticker_upper}: {e} (total: {elapsed:.2f}s)")
        response = StockDataResponse(
            ticker=ticker_upper,
            name=ticker_upper,
            currency="USD",
            period_days=0,
            data_points=[],
        )
        _candle_cache_set(ticker_upper, response)
        return response

    if df is None or df.empty:
        # Return empty data set instead of 404 error
        response = StockDataResponse(
            ticker=ticker_upper,
            name=ticker_upper,
            currency="USD",
            period_days=0,
            data_points=[],
        )
        _candle_cache_set(ticker_upper, response)
        return response

    # yfinance DataFrame: index is DatetimeIndex, columns are Open, High, Low, Close, Volume
    data_points: List[PriceDataPoint] = []
    try:
        for idx, row in df.iterrows():
            if isinstance(idx, datetime):
                date_str = idx.strftime("%Y-%m-%d")
            else:
                date_str = str(idx)[:10]
            data_points.append(
                PriceDataPoint(
                    date=date_str,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,  # NaN check for missing volume
                )
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Error parsing yfinance data for {ticker_upper}: {e}")
        # Return what we have so far
        pass

    response = StockDataResponse(
        ticker=ticker_upper,
        name=ticker_upper,
        currency="USD",
        period_days=30,
        data_points=data_points,
    )
    
    elapsed = time.monotonic() - start_time
    if elapsed > _API_RESPONSE_WARNING_THRESHOLD:
        logger.warning(f"Candle fetch for {ticker_upper} slow: {elapsed:.2f}s (threshold: {_API_RESPONSE_WARNING_THRESHOLD}s)")
    
    _candle_cache_set(ticker_upper, response)
    return response
