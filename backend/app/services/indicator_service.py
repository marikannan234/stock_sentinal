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
        closes = history["Close"].values
        
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


def calculate_rsi(
    symbol: str,
    period: int = 14,
) -> dict:
    """
    Calculate Relative Strength Index (RSI) for a stock symbol.
    
    RSI is a momentum oscillator that measures the magnitude of recent price changes
    to evaluate overbought/oversold conditions.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: RSI period in days (minimum 2, default 14)
    
    Returns:
        Dictionary with:
        {
            "symbol": str,
            "period": int,
            "rsi": float (0-100),
            "current_price": float
        }
    
    Raises:
        StockNotFoundError: If symbol is invalid or has no data
        ValidationError: If period is invalid or insufficient data
    """
    try:
        # Validate period
        if period < 2:
            raise ValidationError(
                message="Period must be at least 2",
                details={"period": period}
            )
        
        logger.info(f"Calculating RSI - symbol: {symbol}, period: {period}")
        
        # Fetch historical data (need at least period + 1 data points)
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="3mo")  # Fetch 3 months to ensure enough data
        
        # Validate we got data
        if history.empty or len(history) == 0:
            logger.warning(f"No data found for symbol: {symbol}")
            raise StockNotFoundError(symbol)
        
        # Get closing prices
        closes = history['Close'].values
        
        # Validate we have enough data points
        if len(closes) < period + 1:
            logger.warning(
                f"Insufficient data points for RSI calculation",
                extra={
                    "symbol": symbol,
                    "period": period,
                    "available_points": len(closes)
                }
            )
            raise ValidationError(
                message=f"Insufficient historical data. Need at least {period + 1} data points, got {len(closes)}",
                details={
                    "symbol": symbol,
                    "required_period": period,
                    "available_data_points": len(closes)
                }
            )
        
        # Calculate price changes
        deltas = []
        for i in range(1, len(closes)):
            deltas.append(closes[i] - closes[i - 1])
        
        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        # Calculate average gain and average loss for the first period
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate smoothed averages for remaining periods (Wilder's smoothing)
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # Calculate RS and RSI
        if avg_loss == 0:
            # If there are no losses, RSI is 100 (all gains) or 0 (no gains)
            rsi_value = 100.0 if avg_gain > 0 else 0.0
        else:
            rs = avg_gain / avg_loss
            rsi_value = 100 - (100 / (1 + rs))
        
        current_price = float(closes[-1])
        
        logger.info(
            f"RSI calculated successfully",
            extra={
                "symbol": symbol,
                "period": period,
                "rsi": rsi_value,
                "current_price": current_price
            }
        )
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "rsi": round(rsi_value, 2),
            "current_price": round(current_price, 2)
        }
    
    except (StockNotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            f"Error calculating RSI",
            extra={
                "symbol": symbol,
                "period": period,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise ValidationError(
            message=f"Error calculating RSI for {symbol}: {str(e)}",
            details={"symbol": symbol, "error": str(e)}
        )


def calculate_ema(
    symbol: str,
    period: int = 20,
) -> dict:
    """
    Calculate Exponential Moving Average for a stock symbol.
    
    Uses the standard EMA formula:
    EMA_today = (Price_today × k) + (EMA_yesterday × (1 - k))
    where k = 2 / (period + 1)
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        period: EMA period in days (minimum 2, typically 12, 20, or 26)
    
    Returns:
        Dictionary with:
        {
            "symbol": str,
            "period": int,
            "ema": float,
            "current_price": float
        }
    
    Raises:
        StockNotFoundError: If symbol is invalid or has no data
        ValidationError: If period is invalid or insufficient data
    """
    try:
        # Validate period
        if period < 2:
            raise ValidationError(
                message="Period must be at least 2",
                details={"period": period, "minimum": 2}
            )
        if period > 500:
            raise ValidationError(
                message="Period cannot exceed 500",
                details={"period": period, "maximum": 500}
            )
        
        # Fetch 3 months of historical data for EMA calculation
        # Need period + some buffer for initial SMA calculation
        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo")
        
        # Validate data availability
        if data.empty:
            raise StockNotFoundError(symbol)
        
        # Need at least period data points to calculate EMA
        if len(data) < period:
            raise ValidationError(
                message=f"Insufficient data for EMA calculation (need {period}, got {len(data)})",
                details={
                    "symbol": symbol,
                    "period": period,
                    "data_points": len(data),
                    "message": "Try a smaller period or check market status"
                }
            )
        
        # Get close prices
        close_prices = data["Close"].values
        
        # Calculate smoothing constant k = 2 / (period + 1)
        k = 2 / (period + 1)
        
        # Initialize EMA with SMA of first 'period' data points
        initial_ema = sum(close_prices[:period]) / period
        
        # Calculate EMA using iterative formula
        # EMA_today = (Price_today × k) + (EMA_yesterday × (1 - k))
        ema = initial_ema
        for i in range(period, len(close_prices)):
            ema = (close_prices[i] * k) + (ema * (1 - k))
        
        # Get current price (last close price)
        current_price = float(close_prices[-1])
        
        logger.debug(
            f"EMA calculated successfully",
            extra={
                "symbol": symbol,
                "period": period,
                "ema": ema,
                "current_price": current_price,
                "data_points": len(data),
            }
        )
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "ema": round(ema, 2),
            "current_price": current_price,
        }
    
    except (StockNotFoundError, ValidationError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        logger.error(
            f"Error calculating EMA",
            extra={
                "symbol": symbol,
                "period": period,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise ValidationError(
            message=f"Error calculating EMA for {symbol}: {str(e)}",
            details={"symbol": symbol, "error": str(e)}
        )
