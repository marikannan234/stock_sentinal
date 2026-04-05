"""
Technical indicator calculations for real-time price streaming.
Implements SMA, EMA, and RSI calculations.
"""

from typing import List, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculates technical indicators (SMA, EMA, RSI) from price history.
    Maintains a rolling window of prices for efficient computation.
    """

    def __init__(self, max_history: int = 100):
        """
        Args:
            max_history: Maximum number of price points to keep in history
        """
        self.max_history = max_history
        # Per symbol: {symbol: deque([prices])}
        self.price_history: dict = {}

    def add_price(self, symbol: str, price: float) -> None:
        """
        Add a price point to history for a symbol.
        
        Args:
            symbol: Stock symbol
            price: Price value
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.max_history)
        
        self.price_history[symbol].append(price)

    def get_price_history(self, symbol: str) -> List[float]:
        """Get price history for a symbol."""
        if symbol not in self.price_history:
            return []
        return list(self.price_history[symbol])

    def calculate_sma(self, symbol: str, period: int = 20) -> Optional[float]:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            symbol: Stock symbol
            period: Number of periods for SMA (default 20)
        
        Returns:
            SMA value or None if not enough data
        """
        prices = self.get_price_history(symbol)
        
        if len(prices) < period:
            return None
        
        sma = sum(prices[-period:]) / period
        return round(sma, 2)

    def calculate_ema(self, symbol: str, period: int = 12) -> Optional[float]:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            symbol: Stock symbol
            period: Number of periods for EMA (default 12)
        
        Returns:
            EMA value or None if not enough data
        """
        prices = self.get_price_history(symbol)
        
        if len(prices) < period:
            return None
        
        # EMA multiplier
        multiplier = 2.0 / (period + 1)
        
        # Start with SMA as first EMA value
        ema = sum(prices[:period]) / period
        
        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return round(ema, 2)

    def calculate_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Args:
            symbol: Stock symbol
            period: Number of periods for RSI (default 14)
        
        Returns:
            RSI value (0-100) or None if not enough data
        """
        prices = self.get_price_history(symbol)
        
        if len(prices) < period + 1:
            return None
        
        # Calculate gains and losses
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        # Average gains and losses over the period
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            # If no losses, RSI is 100
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)

    def calculate_all(self, symbol: str) -> dict:
        """
        Calculate all indicators for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            dict with sma, ema, rsi values (or None if not enough data)
        """
        return {
            "sma": self.calculate_sma(symbol),
            "ema": self.calculate_ema(symbol),
            "rsi": self.calculate_rsi(symbol),
        }

    def clear_history(self, symbol: str) -> None:
        """Clear price history for a symbol."""
        if symbol in self.price_history:
            del self.price_history[symbol]


# Global indicator calculator instance
indicator_calc = IndicatorCalculator(max_history=100)
