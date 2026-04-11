"""
Enhanced stock endpoints with details, historical data, indicators, and market summary.
Uses Finnhub for live prices and yfinance for historical data.
"""

import logging
from datetime import datetime, timedelta
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


def _fetch_finnhub_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch live quote from Finnhub API.
    Returns dict with 'c' (price), 'd' (change), 'dp' (percent change), etc.
    Returns None on failure.
    """
    try:
        api_key = settings.FINNHUB_API_KEY
        if not api_key:
            logger.warning("FINNHUB_API_KEY not configured")
            return None

        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": symbol.upper(), "token": api_key}
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Finnhub price for {symbol}: ${data.get('c')}")
            return data
        else:
            logger.warning(f"Finnhub returned {resp.status_code} for {symbol}")
            return None
    except Exception as e:
        logger.warning(f"Finnhub error for {symbol}: {str(e)}")
        return None


def _fetch_yfinance_current_price(symbol: str) -> Optional[float]:
    """
    Fallback: Get latest close price from yfinance.
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        return None
    except Exception as e:
        logger.warning(f"yfinance fallback error for {symbol}: {str(e)}")
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
    
    print(f"Fetching yfinance data for {symbol}: range={time_range}, period={period}, interval={interval}")
    
    try:
        ticker = yf.Ticker(symbol.upper())
        df = ticker.history(period=period, interval=interval)
        
        if df is None or df.empty:
            print(f"yfinance returned empty data for {symbol}")
            return []
        
        print(f"yfinance data points: {len(df)}")
        
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
                    ts = datetime.utcnow()
                
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
                logger.warning(f"Error processing data point: {str(e)}")
                continue
        
        return data_points
    except Exception as e:
        logger.warning(f"yfinance error for {symbol}: {str(e)}")
        return []


def _build_live_quote(symbol: str) -> StockQuote:
    """Build live stock quote, trying Finnhub first, falling back to yfinance."""
    symbol_upper = symbol.upper()
    
    # Try Finnhub
    finnhub_data = _fetch_finnhub_quote(symbol_upper)
    if finnhub_data:
        price = float(finnhub_data.get("c", 0))
        if price > 0:
            return StockQuote(
                symbol=symbol_upper,
                price=price,
                change=float(finnhub_data.get("d", 0)),
                change_percent=float(finnhub_data.get("dp", 0)),
                high=float(finnhub_data.get("h", 0)),
                low=float(finnhub_data.get("l", 0)),
                volume=int(finnhub_data.get("v", 0)) if finnhub_data.get("v") else 0,
                timestamp=datetime.utcnow(),
            )
    
    # Fallback to yfinance
    print(f"Finnhub failed, falling back to yfinance for {symbol_upper}")
    fallback_price = _fetch_yfinance_current_price(symbol_upper)
    if fallback_price:
        return StockQuote(
            symbol=symbol_upper,
            price=fallback_price,
            change=0,
            change_percent=0,
            high=fallback_price,
            low=fallback_price,
            volume=0,
            timestamp=datetime.utcnow(),
        )
    
    # If both fail, raise error
    raise HTTPException(
        status_code=502,
        detail=f"Failed to fetch price for {symbol_upper} from both Finnhub and yfinance"
    )



@router.get("/live", response_model=LiveStockRibbon)
@router.get("/live/quotes", response_model=LiveStockRibbon)
def get_live_stock_quotes(db: Session = Depends(get_db_session)) -> LiveStockRibbon:
    """Get live quotes for top stocks from Finnhub."""
    logger.info("Live stock quotes requested")
    quotes = []
    
    for symbol in TOP_STOCKS:
        try:
            quote = _build_live_quote(symbol)
            quotes.append(quote)
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {symbol}: {str(e)}")
            continue
    
    return LiveStockRibbon(
        stocks=quotes,
        total_count=len(quotes),
        timestamp=datetime.utcnow(),
    )


@router.get("/{symbol}/price", response_model=StockQuote)
def get_stock_price(symbol: str, db: Session = Depends(get_db_session)) -> StockQuote:
    """Get a single stock quote from Finnhub with yfinance fallback."""
    normalized_symbol = symbol.upper().strip()
    logger.info("Single stock price requested", extra={"symbol": normalized_symbol})
    return _build_live_quote(normalized_symbol)


@router.get("/market-summary/overview", response_model=MarketSummary)
def get_market_summary(db: Session = Depends(get_db_session)) -> MarketSummary:
    """Get market summary with top gainers, losers, and most active stocks."""
    logger.info("Market summary requested")
    
    quotes = []
    for symbol in TOP_STOCKS:
        try:
            quote = _build_live_quote(symbol)
            quotes.append(quote)
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {symbol}: {str(e)}")
            continue
    
    if not quotes:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch market data from any source"
        )
    
    top_gainers = sorted(quotes, key=lambda q: q.change_percent, reverse=True)[:10]
    top_losers = sorted(quotes, key=lambda q: q.change_percent)[:10]
    most_active = sorted(quotes, key=lambda q: q.volume, reverse=True)[:10]

    return MarketSummary(
        market_time=datetime.utcnow(),
        top_gainers=[
            StockMoverRead(
                symbol=q.symbol,
                price=q.price,
                change_percent=q.change_percent,
                volume=q.volume,
                market_cap=f"{q.price * q.volume:,.0f}" if q.volume else "N/A",
            )
            for q in top_gainers
        ],
        top_losers=[
            StockMoverRead(
                symbol=q.symbol,
                price=q.price,
                change_percent=q.change_percent,
                volume=q.volume,
                market_cap=f"{q.price * q.volume:,.0f}" if q.volume else "N/A",
            )
            for q in top_losers
        ],
        most_active=[
            StockMoverRead(
                symbol=q.symbol,
                price=q.price,
                change_percent=q.change_percent,
                volume=q.volume,
                market_cap=f"{q.price * q.volume:,.0f}" if q.volume else "N/A",
            )
            for q in most_active
        ],
        market_status="open",
    )


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
        timestamp=datetime.utcnow(),
    )
