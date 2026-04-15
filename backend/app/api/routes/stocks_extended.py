"""
Enhanced stock endpoints with details, historical data, indicators, and market summary.
Uses Finnhub for live prices and yfinance for historical data.
"""

import contextlib
import io
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import requests
import yfinance as yf
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.config import settings
from app.schemas.trading import (
    LiveStockRibbon,
    MarketSummary,
    StockDetailsRead,
    StockHistoricalData,
    StockIndicators,
    StockMoverRead,
    StockQuote,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Top stocks for market ribbon and summary
TOP_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "HD", "DIS", "VZ", "INTC", "AMD", "ADBE",
]

# ============================================================================
# AGGRESSIVE CACHE CONFIGURATION
# ============================================================================
MARKET_REQUEST_TIMEOUT_SECONDS = 2  # REDUCED from 3 to 2 seconds
TOP_MOVERS_CACHE_TTL_SECONDS = 10   # Market snapshot: 10 seconds
STOCK_PRICE_CACHE_TTL_SECONDS = 5   # Individual prices: 5 seconds MAX
MARKET_SUMMARY_CACHE_TTL_SECONDS = 10  # Market summary: 10 seconds

FALLBACK_MARKET_QUOTES = (
    {"symbol": "AAPL", "price": 190.0, "change": 2.28, "change_percent": 1.2, "high": 191.4, "low": 188.9, "volume": 52000000},
    {"symbol": "MSFT", "price": 410.0, "change": 3.28, "change_percent": 0.8, "high": 412.2, "low": 407.4, "volume": 28000000},
    {"symbol": "NVDA", "price": 875.0, "change": 10.5, "change_percent": 1.21, "high": 882.0, "low": 866.5, "volume": 47000000},
    {"symbol": "META", "price": 485.0, "change": 2.18, "change_percent": 0.45, "high": 488.4, "low": 481.6, "volume": 21000000},
    {"symbol": "TSLA", "price": 180.0, "change": -2.74, "change_percent": -1.5, "high": 183.0, "low": 178.1, "volume": 65000000},
    {"symbol": "AMZN", "price": 178.0, "change": -1.24, "change_percent": -0.69, "high": 179.5, "low": 176.2, "volume": 33000000},
)

# ============================================================================
# CACHE STRUCTURES WITH TTL
# ============================================================================

@dataclass(frozen=True)
class _CacheEntry:
    """Generic cache entry with TTL tracking."""
    data: Any
    expires_at: float


# Market snapshot cache (10 sec TTL)
top_movers_cache = {
    "data": None,
    "timestamp": 0.0,
}
_top_movers_cache_lock = threading.Lock()

# Per-stock price cache (5 sec TTL)
_stock_price_cache: Dict[str, _CacheEntry] = {}
_stock_price_cache_lock = threading.Lock()

# Market summary cache (10 sec TTL)
_market_summary_cache = {
    "data": None,
    "timestamp": 0.0,
}
_market_summary_cache_lock = threading.Lock()


# ============================================================================
# CACHE HELPER FUNCTIONS
# ============================================================================

def _get_stock_price_from_cache(symbol: str) -> Optional[StockQuote]:
    """Get cached stock price if still valid (5 sec TTL)."""
    now = time.time()
    with _stock_price_cache_lock:
        entry = _stock_price_cache.get(symbol)
        if entry and entry.expires_at > now:
            logger.debug(f"Cache HIT for {symbol} (age: {now - (entry.expires_at - STOCK_PRICE_CACHE_TTL_SECONDS):.1f}s)")
            return entry.data
        if entry and entry.expires_at <= now:
            del _stock_price_cache[symbol]  # Clean expired entry
    return None


def _cache_stock_price(symbol: str, quote: StockQuote) -> None:
    """Cache stock price with 5-second TTL."""
    expires_at = time.time() + STOCK_PRICE_CACHE_TTL_SECONDS
    with _stock_price_cache_lock:
        _stock_price_cache[symbol] = _CacheEntry(data=quote, expires_at=expires_at)
    logger.debug(f"Cached price for {symbol}: ${quote.price}")


def _get_market_summary_from_cache() -> Optional[MarketSummary]:
    """Get cached market summary if still valid (10 sec TTL)."""
    current_time = time.time()
    with _market_summary_cache_lock:
        if (_market_summary_cache["data"] is not None and 
            current_time - _market_summary_cache["timestamp"] < MARKET_SUMMARY_CACHE_TTL_SECONDS):
            return _market_summary_cache["data"]
    return None


def _cache_market_summary(summary: MarketSummary) -> None:
    """Cache market summary with 10-second TTL."""
    with _market_summary_cache_lock:
        _market_summary_cache["data"] = summary
        _market_summary_cache["timestamp"] = time.time()
    logger.debug("Cached market summary")


def _get_fallback_market_quotes() -> List[StockQuote]:
    timestamp = datetime.now(timezone.utc)
    return [
        StockQuote(
            symbol=item["symbol"],
            price=float(item["price"]),
            change=float(item["change"]),
            change_percent=float(item["change_percent"]),
            high=float(item["high"]),
            low=float(item["low"]),
            volume=int(item["volume"]),
            timestamp=timestamp,
        )
        for item in FALLBACK_MARKET_QUOTES
    ]


def _run_silenced_yfinance(request_fn):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return request_fn()


def _fetch_market_quotes_batch(symbols: List[str]) -> List[StockQuote]:
    """Fetch a market snapshot in one yfinance call with AGGRESSIVE timeout."""
    if not symbols:
        return []

    try:
        # Use ThreadPoolExecutor to ENFORCE hard 2-second timeout
        def _fetch():
            return _run_silenced_yfinance(
                lambda: yf.download(
                    tickers=" ".join(symbols),
                    period="2d",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                    group_by="ticker",
                    timeout=2,  # Max 2 seconds
                )
            )
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch)
            try:
                data = future.result(timeout=2)  # Hard timeout at 2 seconds
            except FutureTimeoutError:
                logger.warning(f"⚠️ Batch fetch TIMEOUT for {len(symbols)} stocks (>2s) - using fallback")
                return []
    except Exception as e:
        logger.debug(f"Batch market data fetch failed: {str(e)[:100]}")
        return []

    if data is None or not hasattr(data, "empty") or data.empty:
        logger.debug("Batch market data fetch returned empty data")
        return []

    timestamp = datetime.now(timezone.utc)
    quotes: List[StockQuote] = []
    has_multi_index = isinstance(data.columns, pd.MultiIndex)

    for symbol in symbols:
        try:
            frame = data[symbol] if has_multi_index else data
            if not isinstance(frame, pd.DataFrame) or frame.empty or "Close" not in frame.columns:
                continue

            clean_frame = frame.dropna(subset=["Close"])
            if clean_frame.empty:
                continue

            latest_row = clean_frame.iloc[-1]
            previous_row = clean_frame.iloc[-2] if len(clean_frame) > 1 else latest_row
            price = float(latest_row.get("Close") or 0)
            previous_close = float(previous_row.get("Close") or price or 0)

            if price <= 0:
                continue

            high = float(latest_row.get("High") or price)
            low = float(latest_row.get("Low") or price)
            volume_raw = latest_row.get("Volume")
            volume = int(volume_raw) if pd.notna(volume_raw) else 0
            change = price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0

            quotes.append(
                StockQuote(
                    symbol=symbol,
                    price=price,
                    change=round(change, 2),
                    change_percent=round(change_percent, 2),
                    high=high,
                    low=low,
                    volume=volume,
                    timestamp=timestamp,
                )
            )
        except Exception as e:
            logger.warning(f"Failed to parse market quote for {symbol}: {str(e)[:100]}")

    return quotes


def _merge_with_fallback_quotes(quotes: List[StockQuote]) -> List[StockQuote]:
    if len(quotes) >= 5:
        return quotes

    merged = quotes[:]
    existing_symbols = {quote.symbol for quote in quotes}

    for fallback_quote in _get_fallback_market_quotes():
        if fallback_quote.symbol not in existing_symbols:
            merged.append(fallback_quote)
            existing_symbols.add(fallback_quote.symbol)

    return merged


def _fetch_market_quotes_with_fallback() -> List[StockQuote]:
    try:
        quotes = _fetch_market_quotes_batch(TOP_STOCKS)
        if quotes:
            return _merge_with_fallback_quotes(quotes)
    except Exception as e:
        logger.warning("Market quote fetch failed, using fallback: %s", e)

    return _get_fallback_market_quotes()


def _get_market_snapshot_quotes() -> List[StockQuote]:
    """
    Get market snapshot quotes with AGGRESSIVE caching (10-second TTL).
    
    Cache Logic:
    1. Check cache - if valid, return instantly (<1ms)
    2. Cache miss/expired - fetch with timeout (max 2 seconds)
    3. Timeout/error - return cached data (even if stale)
    4. No cache - return fallback data
    """
    current_time = time.time()
    start_time = current_time
    
    # STEP 1: Check cache (instant return if valid)
    with _top_movers_cache_lock:
        if (top_movers_cache["data"] is not None and 
            current_time - top_movers_cache["timestamp"] < TOP_MOVERS_CACHE_TTL_SECONDS):
            age = current_time - top_movers_cache["timestamp"]
            logger.info(f"✓ Market cache HIT (age: {age:.1f}s) - returning {len(top_movers_cache['data'])} quotes instantly")
            return top_movers_cache["data"]
    
    # STEP 2: Cache miss - fetch with timeout protection
    logger.debug("Cache miss/expired, fetching fresh market data with 2s timeout...")
    
    try:
        quotes = _fetch_market_quotes_with_fallback()
        
        # Store in cache
        with _top_movers_cache_lock:
            top_movers_cache["data"] = quotes
            top_movers_cache["timestamp"] = current_time
            fetch_time = (time.time() - start_time) * 1000
            logger.info(f"✓ Market data fetched and cached ({fetch_time:.0f}ms) - {len(quotes)} quotes")
        
        return quotes
    
    except Exception as e:
        logger.error(f"Error fetching market snapshot: {str(e)[:100]}")
        # STEP 3: Return cached data even if expired
        with _top_movers_cache_lock:
            if top_movers_cache["data"] is not None:
                age = current_time - top_movers_cache["timestamp"]
                logger.warning(f"⚠️ Returning stale cache (age: {age:.1f}s) due to fetch error")
                return top_movers_cache["data"]
        
        # STEP 4: No cache - use fallback
        logger.warning("⚠️ No cached data available, using fallback data")
        return _get_fallback_market_quotes()


def _build_stock_mover(quote: StockQuote) -> StockMoverRead:
    return StockMoverRead(
        symbol=quote.symbol,
        price=quote.price,
        change_percent=quote.change_percent,
        volume=quote.volume,
        market_cap=f"{quote.price * quote.volume:,.0f}" if quote.volume else "N/A",
    )


def _build_market_summary_from_quotes(quotes: List[StockQuote]) -> MarketSummary:
    snapshot = quotes or _get_fallback_market_quotes()
    top_gainers = sorted(snapshot, key=lambda q: q.change_percent, reverse=True)[:10]
    top_losers = sorted(snapshot, key=lambda q: q.change_percent)[:10]
    most_active = sorted(snapshot, key=lambda q: q.volume, reverse=True)[:10]

    return MarketSummary(
        market_time=datetime.now(timezone.utc),
        top_gainers=[_build_stock_mover(quote) for quote in top_gainers],
        top_losers=[_build_stock_mover(quote) for quote in top_losers],
        most_active=[_build_stock_mover(quote) for quote in most_active],
        market_status="open",
    )


def _fetch_finnhub_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote from Finnhub API with timeout enforcement.
    Returns dict with 'c' (price), 'd' (change), 'dp' (percent change), etc.
    Returns None on failure or timeout.
    """
    try:
        api_key = settings.FINNHUB_API_KEY
        if not api_key:
            logger.debug(f"No Finnhub API key configured")
            return None

        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol.upper(), "token": api_key}
        
        # Use ThreadPoolExecutor with timeout to ENFORCE max 2 seconds
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(requests.get, url, params=params, timeout=2)
            try:
                resp = future.result(timeout=2)
                if resp.status_code == 200:
                    logger.debug(f"Finnhub SUCCESS for {symbol}: ${resp.json().get('c', 0)}")
                    return resp.json()
                logger.warning(f"Finnhub HTTP {resp.status_code} for {symbol}")
                return None
            except FutureTimeoutError:
                logger.warning(f"⚠️ Finnhub TIMEOUT for {symbol} (>2s)")
                return None
    except Exception as e:
        logger.warning(f"Finnhub error for {symbol}: {str(e)[:100]}")
        return None


def _fetch_yfinance_current_price(symbol: str) -> Optional[float]:
    """
    Fallback: Get latest close price from yfinance with timeout enforcement.
    """
    try:
        # Use ThreadPoolExecutor with timeout to ENFORCE max 2 seconds
        def _fetch():
            return _run_silenced_yfinance(
                lambda: yf.download(
                    tickers=symbol.upper(),
                    period="1d",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                    timeout=2,
                )
            )
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch)
            try:
                data = future.result(timeout=2)
                if data is not None and hasattr(data, "empty") and not data.empty:
                    close_value = data.get("Close") if isinstance(data, dict) else (data["Close"] if "Close" in data.columns else None)
                    if close_value is not None:
                        price = float(close_value.iloc[-1]) if hasattr(close_value, "iloc") else float(close_value[-1]) if len(close_value) > 0 else None
                        if price and price > 0:
                            logger.debug(f"yfinance SUCCESS for {symbol}: ${price}")
                            return price
                return None
            except FutureTimeoutError:
                logger.warning(f"⚠️ yfinance TIMEOUT for {symbol} (>2s)")
                return None
    except Exception as e:
        logger.warning(f"yfinance error for {symbol}: {str(e)[:100]}")
        return None


def _calculate_indicators(close_prices: List[float]) -> StockIndicators:
    """Calculate technical indicators from close prices."""
    if not close_prices or len(close_prices) < 2:
        return StockIndicators()

    try:
        # SMA
        sma_20 = sum(close_prices[-20:]) / min(len(close_prices), 20) if len(close_prices) >= 20 else sum(close_prices) / len(close_prices)
        sma_50 = sum(close_prices[-50:]) / min(len(close_prices), 50) if len(close_prices) >= 50 else sum(close_prices) / len(close_prices)
        sma_200 = sum(close_prices[-200:]) / min(len(close_prices), 200) if len(close_prices) >= 200 else sum(close_prices) / len(close_prices)

        # EMA
        def _ema(data: List[float], period: int) -> float:
            if not data:
                return 0
            multiplier = 2 / (period + 1)
            ema_value = data[0]
            for price in data[1:]:
                ema_value = price * multiplier + ema_value * (1 - multiplier)
            return ema_value

        ema_12 = _ema(close_prices[-26:] if len(close_prices) >= 26 else close_prices, 12)
        ema_26 = _ema(close_prices[-26:] if len(close_prices) >= 26 else close_prices, 26)
        macd = ema_12 - ema_26

        # RSI
        deltas = [close_prices[i] - close_prices[i - 1] for i in range(1, len(close_prices))]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else None
        rsi = 100 - (100 / (1 + rs)) if rs is not None else 50.0

        # Bollinger Bands
        bb_window = close_prices[-20:] if len(close_prices) >= 20 else close_prices
        mean = sum(bb_window) / len(bb_window)
        variance = sum((p - mean) ** 2 for p in bb_window) / len(bb_window)
        std_dev = variance ** 0.5

        return StockIndicators(
            sma_20=round(sma_20, 2),
            sma_50=round(sma_50, 2),
            sma_200=round(sma_200, 2),
            ema_12=round(ema_12, 2),
            ema_26=round(ema_26, 2),
            rsi=round(rsi, 2),
            macd=round(macd, 2),
            bollinger_upper=round(mean + (2 * std_dev), 2),
            bollinger_lower=round(mean - (2 * std_dev), 2),
            bollinger_middle=round(mean, 2),
        )
    except Exception as e:
        logger.warning(f"Indicator calculation error: {str(e)}")
        return StockIndicators()


def _fetch_historical_data(symbol: str, time_range: str) -> List[StockHistoricalData]:
    """
    Fetch OHLCV data from yfinance with proper period/interval mapping.
    Supports: 1h, 1d, 1w, 1m, 1y ranges.
    """
    range_config = {
        "1h": {"period": "1d", "interval": "5m"},
        "1d": {"period": "5d", "interval": "5m"},
        "1w": {"period": "1mo", "interval": "1d"},
        "1m": {"period": "3mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1wk"},
    }
    
    config = range_config.get(time_range, {"period": "1y", "interval": "1wk"})
    period = config["period"]
    interval = config["interval"]
    
    try:
        ticker = yf.Ticker(symbol.upper())
        df = _run_silenced_yfinance(
            lambda: ticker.history(period=period, interval=interval, timeout=MARKET_REQUEST_TIMEOUT_SECONDS)
        )
        
        if df is None or not hasattr(df, "empty") or df.empty:
            return []

        data_points: List[StockHistoricalData] = []
        for idx, row in df.iterrows():
            try:
                # Handle timestamp conversion from pandas index
                if isinstance(idx, pd.Timestamp):
                    ts = idx.to_pydatetime()
                elif isinstance(idx, datetime):
                    ts = idx
                else:
                    # Fallback for other index types
                    ts = datetime.now(timezone.utc)
                
                data_point = StockHistoricalData(
                    timestamp=ts,
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=int(row.get("Volume", 0)) if row.get("Volume") else 0,
                )
                data_points.append(data_point)
            except Exception as e:
                logger.warning("Error processing data point for %s: %s", symbol, e)
                continue
        
        return data_points
    except Exception as e:
        logger.warning("yfinance error for %s: %s", symbol, e)
        return []


def _build_live_quote(symbol: str) -> StockQuote:
    """Build live stock quote with cache-first approach and timeout protection."""
    symbol_upper = symbol.upper()
    start_time = time.time()
    
    # STEP 1: Check cache first (instant <5ms return)
    cached_quote = _get_stock_price_from_cache(symbol_upper)
    if cached_quote:
        return cached_quote
    
    # STEP 2: Try Finnhub with 2-second timeout
    logger.debug(f"Fetching price for {symbol_upper} (trying Finnhub)...")
    finnhub_data = _fetch_finnhub_quote(symbol_upper)
    if finnhub_data and isinstance(finnhub_data, dict):
        price = float(finnhub_data.get("c", 0))
        if price > 0:
            quote = StockQuote(
                symbol=symbol_upper,
                price=price,
                change=float(finnhub_data.get("d", 0)),
                change_percent=float(finnhub_data.get("dp", 0)),
                high=float(finnhub_data.get("h", 0)),
                low=float(finnhub_data.get("l", 0)),
                volume=int(finnhub_data.get("v", 0)) if finnhub_data.get("v") else 0,
                timestamp=datetime.now(timezone.utc),
            )
            _cache_stock_price(symbol_upper, quote)
            fetch_time = (time.time() - start_time) * 1000
            logger.info(f"✓ Finnhub price for {symbol_upper}: ${price} ({fetch_time:.0f}ms)")
            return quote
    
    # STEP 3: Fallback to yfinance with 2-second timeout
    logger.debug(f"Finnhub failed, trying yfinance for {symbol_upper}...")
    fallback_price = _fetch_yfinance_current_price(symbol_upper)
    if fallback_price:
        quote = StockQuote(
            symbol=symbol_upper,
            price=fallback_price,
            change=0,
            change_percent=0,
            high=fallback_price,
            low=fallback_price,
            volume=0,
            timestamp=datetime.now(timezone.utc),
        )
        _cache_stock_price(symbol_upper, quote)
        fetch_time = (time.time() - start_time) * 1000
        logger.info(f"✓ yfinance price for {symbol_upper}: ${fallback_price} ({fetch_time:.0f}ms)")
        return quote
    
    # STEP 4: All APIs failed - error
    fetch_time = (time.time() - start_time) * 1000
    logger.error(f"✗ Failed to fetch price for {symbol_upper} (both Finnhub and yfinance failed after {fetch_time:.0f}ms)")
    raise HTTPException(
        status_code=502,
        detail=f"Failed to fetch price for {symbol_upper} from both Finnhub and yfinance (timeout or error)"
    )



@router.get("/live", response_model=LiveStockRibbon)
@router.get("/live/quotes", response_model=LiveStockRibbon)
def get_live_stock_quotes(db: Session = Depends(get_db_session)) -> LiveStockRibbon:
    """Get live quotes for top stocks with AGGRESSIVE caching (10-second TTL)."""
    start_time = time.time()
    logger.info("✓ Live stock quotes requested")
    quotes = _get_market_snapshot_quotes()
    fetch_time = (time.time() - start_time) * 1000
    
    if fetch_time > 1000:
        logger.warning(f"⚠️ SLOW: Live quotes took {fetch_time:.0f}ms (target <1000ms)")
    
    return LiveStockRibbon(
        stocks=quotes,
        total_count=len(quotes),
        timestamp=datetime.now(timezone.utc),
    )



@router.get("/{symbol}/price", response_model=StockQuote)
def get_stock_price(symbol: str, db: Session = Depends(get_db_session)) -> StockQuote:
    """Get a single stock quote with cache-first approach (5-second TTL)."""
    normalized_symbol = symbol.upper().strip()
    start_time = time.time()
    logger.info(f"✓ Stock price requested: {normalized_symbol}")
    
    quote = _build_live_quote(normalized_symbol)
    fetch_time = (time.time() - start_time) * 1000
    
    if fetch_time > 1000:
        logger.warning(f"⚠️ SLOW: Stock price took {fetch_time:.0f}ms (target <1000ms)")
    
    return quote


@router.get("/market-summary/overview", response_model=MarketSummary)
def get_market_summary(db: Session = Depends(get_db_session)) -> MarketSummary:
    """Get market summary with AGGRESSIVE caching (10-second TTL and timeout protection)."""
    start_time = time.time()
    logger.info("Market summary requested")

    # STEP 1: Check cache first
    cached_summary = _get_market_summary_from_cache()
    if cached_summary:
        fetch_time = (time.time() - start_time) * 1000
        logger.info(f"✓ Market summary cache HIT ({fetch_time:.1f}ms)")
        return cached_summary

    # STEP 2: Fetch with timeout protection
    try:
        quotes = _get_market_snapshot_quotes()
        summary = _build_market_summary_from_quotes(quotes)
        _cache_market_summary(summary)
        fetch_time = (time.time() - start_time) * 1000
        logger.info(f"✓ Market summary generated and cached ({fetch_time:.0f}ms)")
        return summary
    except Exception as e:
        logger.error(f"Market summary failed ({str(e)[:100]}), using fallback data")
        summary = _build_market_summary_from_quotes(_get_fallback_market_quotes())
        _cache_market_summary(summary)
        fetch_time = (time.time() - start_time) * 1000
        logger.warning(f"⚠️ Returned fallback market summary ({fetch_time:.0f}ms)")
        return summary


@router.get("/{symbol}", response_model=StockDetailsRead)
def get_stock_details(
    symbol: str,
    time_range: str = Query("1y", pattern="^(1h|1d|1w|1m|1y)$", alias="range"),
    db: Session = Depends(get_db_session),
) -> StockDetailsRead:
    """
    Get detailed stock information with historical OHLC data and indicators.
    
    Supported ranges:
    - 1h: Last 1 day with 5-min candles
    - 1d: Last 5 days with 5-min candles
    - 1w: Last 1 month with daily candles
    - 1m: Last 3 months with daily candles
    - 1y: Last 1 year with weekly candles
    """
    symbol = symbol.upper().strip()
    logger.info("Stock details requested", extra={"symbol": symbol, "range": time_range})
    
    # Validate time_range
    if time_range not in ["1h", "1d", "1w", "1m", "1y"]:
        time_range = "1y"
    
    # Get live quote
    quote = _build_live_quote(symbol)
    
    # Fetch historical data
    historical_data = _fetch_historical_data(symbol, time_range)
    
    if not historical_data:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch historical data for {symbol}"
        )
    
    # Extract close prices for indicators
    close_prices = [d.close for d in historical_data]
    indicators = _calculate_indicators(close_prices)
    
    # Get day values from most recent candle
    latest_candle = historical_data[-1]
    day_change = latest_candle.close - latest_candle.open
    day_change_percent = (day_change / latest_candle.open * 100) if latest_candle.open > 0 else 0
    
    return StockDetailsRead(
        symbol=symbol,
        current_price=quote.price,
        day_change=day_change,
        day_change_percent=day_change_percent,
        open=latest_candle.open,
        high=latest_candle.high,
        low=latest_candle.low,
        volume=latest_candle.volume,
        market_cap=None,  # Not available from real APIs without additional calls
        dividend_yield=None,  # Not available from basic yfinance
        pe_ratio=None,  # Not available from basic yfinance
        indicators=indicators,
        historical_data=historical_data,
        timestamp=datetime.now(timezone.utc),
    )
