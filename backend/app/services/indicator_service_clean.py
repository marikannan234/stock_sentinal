"""
Technical Indicators Service Module

Provides simple calculations for technical indicators:
- Simple Moving Average (SMA)

Features:
- Clean, simple implementation using yfinance
- Standard error handling using app.core.exceptions
- No caching (can be added later if needed)
"""

import logging

import yfinance as yf
import numpy as np

from app.core.exceptions import ValidationError, StockNotFoundError

logger = logging.getLogger(__name__)


def calculate_sma(
    symbol: str,
    period: int = 14,
) -> dict:
    """
    Calculate Simple Moving Average for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: SMA period in days (minimum 2)
    
    Returns:
        Dictionary with:
        {
            "symbol": str,
            "period": int,
            "sma": float,
            "current_price": float
        }
    
    Raises:
        StockNotFoundError: If symbol is invalid or has no data
        ValidationError: If period is invalid
    """
    try:
        # Validate period
        if period < 2:
            raise ValidationError(
                message="Period must be at least 2",
                details={"period": period}
            )
        
        logger.info(f"Calculating SMA - symbol: {symbol}, period: {period}")
        
        # Fetch historical data (1 month should be sufficient for SMA)
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1mo")
        
        # Validate we got data
        if history.empty or len(history) == 0:
            logger.warning(f"No data found for symbol: {symbol}")
            raise StockNotFoundError(symbol)
        
        # Get closing prices
        closes = history['Close'].values
        
        # Validate we have enough data points
        if len(closes) < period:
            logger.warning(
                f"Insufficient data points for SMA calculation",
                extra={
                    "symbol": symbol,
                    "period": period,
                    "available_points": len(closes)
                }
            )
            raise ValidationError(
                message=f"Insufficient historical data. Need at least {period} data points, got {len(closes)}",
                details={
                    "symbol": symbol,
                    "required_period": period,
                    "available_data_points": len(closes)
                }
            )
        
        # Calculate SMA: average of last N closing prices
        last_prices = closes[-period:]
        sma_value = float(sum(last_prices) / len(last_prices))
        current_price = float(closes[-1])
        
        logger.info(
            f"SMA calculated successfully",
            extra={
                "symbol": symbol,
                "period": period,
                "sma": sma_value,
                "current_price": current_price
            }
        )
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "sma": round(sma_value, 2),
            "current_price": round(current_price, 2)
        }
    
    except (StockNotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            f"Error calculating SMA",
            extra={
                "symbol": symbol,
                "period": period,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise ValidationError(
            message=f"Error calculating SMA for {symbol}: {str(e)}",
            details={"symbol": symbol, "error": str(e)}
        )
