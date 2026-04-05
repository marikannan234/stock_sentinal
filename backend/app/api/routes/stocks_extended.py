"""
Enhanced stock endpoints with details, historical data, indicators, and market summary.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
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

SAMPLE_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TESLA", "META", "NFLX", "TSLA", "JPM",
    "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "VZ", "INTC", "AMD",
    "ADBE", "CSCO", "PYPL", "UBER", "SPOT", "SQ", "MSTR", "COIN", "RIOT", "MARA",
    "CRM", "SNOWFLAKE", "PALANTIR", "DATADOG", "OKTA", "ZM", "TWLO", "SNAP", "PINS", "RBLX",
    "GOOG", "APPL", "MRNA", "BIONTECH", "MODERNA", "PFE", "JNRX", "AZN", "ELY", "W",
]


def _rng_for_symbol(symbol: str) -> random.Random:
    return random.Random(hash(symbol.upper()) % (2**32))


def _calculate_indicators(historical_data: List[float]) -> StockIndicators:
    if not historical_data:
        return StockIndicators()

    latest_price = historical_data[-1]
    sma_20 = sum(historical_data[-20:]) / min(len(historical_data), 20)
    sma_50 = sum(historical_data[-50:]) / min(len(historical_data), 50)
    sma_200 = sum(historical_data[-200:]) / min(len(historical_data), 200)

    def _ema(data: List[float], period: int) -> float:
        multiplier = 2 / (period + 1)
        ema_value = data[0]
        for price in data[1:]:
            ema_value = price * multiplier + ema_value * (1 - multiplier)
        return ema_value

    ema_12 = _ema(historical_data, 12)
    ema_26 = _ema(historical_data, 26)
    macd = ema_12 - ema_26

    deltas = [historical_data[i] - historical_data[i - 1] for i in range(1, len(historical_data))]
    gains = [delta if delta > 0 else 0 for delta in deltas[-14:]]
    losses = [-delta if delta < 0 else 0 for delta in deltas[-14:]]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rs = avg_gain / avg_loss if avg_loss else None
    rsi = 100 - (100 / (1 + rs)) if rs is not None else 100.0

    std_window = historical_data[-20:] if len(historical_data) >= 20 else historical_data
    mean = sum(std_window) / len(std_window)
    variance = sum((price - mean) ** 2 for price in std_window) / len(std_window)
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


def _generate_historical_data(current_price: float, days: int, rng: random.Random) -> List[float]:
    prices = [current_price]
    for _ in range(days):
        change = rng.uniform(-0.05, 0.08)
        next_price = max(prices[-1] * (1 + change), 1.0)
        prices.append(next_price)
    return prices[::-1]


def _build_live_quote(symbol: str) -> StockQuote:
    rng = _rng_for_symbol(symbol)
    price = round(rng.uniform(50, 500), 2)
    change_percent = round(rng.uniform(-10, 15), 2)
    change_amount = round(price * (change_percent / 100), 2)
    high = round(price * 1.02, 2)
    low = round(price * 0.98, 2)
    volume = rng.randint(1_000_000, 100_000_000)
    return StockQuote(
        symbol=symbol,
        price=price,
        change=change_amount,
        change_percent=change_percent,
        high=high,
        low=low,
        volume=volume,
        timestamp=datetime.utcnow(),
    )


@router.get("/live", response_model=LiveStockRibbon)
@router.get("/live/quotes", response_model=LiveStockRibbon)
def get_live_stock_quotes(db: Session = Depends(get_db_session)) -> LiveStockRibbon:
    """Get live quotes for top stocks."""
    logger.info("Live stock quotes requested")
    quotes = [_build_live_quote(symbol) for symbol in SAMPLE_STOCKS[:50]]
    return LiveStockRibbon(
        stocks=quotes,
        total_count=len(quotes),
        timestamp=datetime.utcnow(),
    )


@router.get("/{symbol}/price", response_model=StockQuote)
def get_stock_price(symbol: str, db: Session = Depends(get_db_session)) -> StockQuote:
    """Get a single stock quote for frontend price widgets."""
    normalized_symbol = symbol.upper().strip()
    logger.info("Single stock price requested", extra={"symbol": normalized_symbol})
    return _build_live_quote(normalized_symbol)


@router.get("/market-summary/overview", response_model=MarketSummary)
def get_market_summary(db: Session = Depends(get_db_session)) -> MarketSummary:
    """Get market summary with top gainers, losers, and most active stocks."""
    logger.info("Market summary requested")

    all_quotes = [_build_live_quote(symbol) for symbol in SAMPLE_STOCKS]
    top_gainers = sorted(all_quotes, key=lambda quote: quote.change_percent, reverse=True)[:10]
    top_losers = sorted(all_quotes, key=lambda quote: quote.change_percent)[:10]
    most_active = sorted(all_quotes, key=lambda quote: quote.volume, reverse=True)[:10]

    return MarketSummary(
        market_time=datetime.utcnow(),
        top_gainers=[
            StockMoverRead(
                symbol=quote.symbol,
                price=quote.price,
                change_percent=quote.change_percent,
                volume=quote.volume,
                market_cap=f"{quote.price * quote.volume:,.0f}",
            )
            for quote in top_gainers
        ],
        top_losers=[
            StockMoverRead(
                symbol=quote.symbol,
                price=quote.price,
                change_percent=quote.change_percent,
                volume=quote.volume,
                market_cap=f"{quote.price * quote.volume:,.0f}",
            )
            for quote in top_losers
        ],
        most_active=[
            StockMoverRead(
                symbol=quote.symbol,
                price=quote.price,
                change_percent=quote.change_percent,
                volume=quote.volume,
                market_cap=f"{quote.price * quote.volume:,.0f}",
            )
            for quote in most_active
        ],
        market_status="open",
    )


@router.get("/{symbol}", response_model=StockDetailsRead)
def get_stock_details(
    symbol: str,
    time_range: str = Query("1y", pattern="^(1d|1w|1m|3m|6m|1y)$", alias="range"),
    db: Session = Depends(get_db_session),
) -> StockDetailsRead:
    """Get detailed stock information with historical data and indicators."""
    symbol = symbol.upper().strip()
    logger.info("Stock details requested", extra={"symbol": symbol, "range": time_range})

    range_days = {
        "1d": 1,
        "1w": 7,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
    }
    days = range_days.get(time_range, 365)

    rng = _rng_for_symbol(symbol)
    current_price = round(rng.uniform(50, 500), 2)
    day_change_percent = round(rng.uniform(-10, 15), 2)
    day_change = round(current_price * (day_change_percent / 100), 2)
    day_open = round(current_price - day_change, 2)
    day_high = round(max(current_price, day_open) * 1.02, 2)
    day_low = round(min(current_price, day_open) * 0.98, 2)
    day_volume = rng.randint(1_000_000, 100_000_000)

    all_prices = _generate_historical_data(current_price, 365, rng)
    price_window = all_prices[-days:] if days < len(all_prices) else all_prices
    indicators = _calculate_indicators(price_window)

    base_time = datetime.utcnow() - timedelta(days=max(days - 1, 0))
    historical_data = [
        StockHistoricalData(
            timestamp=base_time + timedelta(days=index),
            open=round(price * 0.99, 2),
            high=round(price * 1.02, 2),
            low=round(price * 0.98, 2),
            close=round(price, 2),
            volume=rng.randint(1_000_000, 100_000_000),
        )
        for index, price in enumerate(price_window)
    ]

    return StockDetailsRead(
        symbol=symbol,
        current_price=current_price,
        day_change=day_change,
        day_change_percent=day_change_percent,
        open=day_open,
        high=day_high,
        low=day_low,
        volume=day_volume,
        market_cap=f"{current_price * rng.uniform(1e9, 1e12):,.0f}",
        dividend_yield=round(rng.uniform(0, 5), 2),
        pe_ratio=round(rng.uniform(10, 50), 2),
        indicators=indicators,
        historical_data=historical_data,
        timestamp=datetime.utcnow(),
    )
