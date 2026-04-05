"""
Price streamer - fetches current stock prices and broadcasts to WebSocket clients.
Handles caching and error handling gracefully.
Calculates real-time technical indicators (SMA, EMA, RSI).
"""

import asyncio
import yfinance as yf
from datetime import datetime
from typing import Optional
import logging
from app.ws.indicators import indicator_calc

logger = logging.getLogger(__name__)


class PriceStreamer:
    """
    Fetches and streams stock prices.
    Uses caching to avoid excessive API calls.
    """

    def __init__(self, update_interval: int = 3):
        """
        Args:
            update_interval: Seconds between price updates (default 3 seconds)
        """
        self.update_interval = update_interval
        self._price_cache: dict = {}
        self._background_tasks = {}

    async def get_latest_price(self, symbol: str) -> Optional[dict]:
        """
        Fetch latest price for a symbol using yfinance.
        
        Returns:
            dict with price, timestamp, or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Get latest price
            latest = hist.iloc[-1]
            current_time = datetime.utcnow().isoformat() + "Z"
            
            return {
                "price": round(float(latest["Close"]), 2),
                "high": round(float(latest["High"]), 2),
                "low": round(float(latest["Low"]), 2),
                "volume": int(latest["Volume"]),
                "timestamp": current_time,
            }
        
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    async def stream_price(self, symbol: str, callback):
        """
        Stream prices for a symbol at regular intervals.
        Calls callback with price data and indicators each update.
        
        Args:
            symbol: Stock symbol
            callback: Async function to call with price data
        """
        while True:
            try:
                price_data = await self.get_latest_price(symbol)
                
                if price_data:
                    # Add price to indicator history
                    indicator_calc.add_price(symbol, price_data["price"])
                    
                    # Calculate indicators
                    indicators = indicator_calc.calculate_all(symbol)
                    
                    # Merge indicators into price data
                    price_data.update(indicators)
                    
                    await callback(symbol, price_data)
                else:
                    logger.warning(f"Failed to get price for {symbol}")
                
                await asyncio.sleep(self.update_interval)
            
            except asyncio.CancelledError:
                logger.info(f"Price stream cancelled for {symbol}")
                break
            except Exception as e:
                logger.error(f"Error in price stream for {symbol}: {e}")
                await asyncio.sleep(self.update_interval)

    async def start_streaming(self, symbol: str, callback, task_name: Optional[str] = None):
        """
        Start background price streaming for a symbol.
        
        Args:
            symbol: Stock symbol
            callback: Async callback function
            task_name: Optional name for tracking the task
        """
        name = task_name or f"stream_{symbol}"
        
        if name not in self._background_tasks:
            task = asyncio.create_task(self.stream_price(symbol, callback))
            self._background_tasks[name] = task
            logger.info(f"Started streaming {symbol}")

    async def stop_streaming(self, task_name: str):
        """Stop a background streaming task."""
        if task_name in self._background_tasks:
            self._background_tasks[task_name].cancel()
            try:
                await self._background_tasks[task_name]
            except asyncio.CancelledError:
                pass
            del self._background_tasks[task_name]
            logger.info(f"Stopped streaming {task_name}")

    def get_active_streams(self) -> list:
        """Get list of active streaming tasks."""
        return list(self._background_tasks.keys())


# Global price streamer instance
streamer = PriceStreamer(update_interval=3)
