"""
Price streamer - fetches current stock prices and broadcasts to WebSocket clients.
Handles caching and error handling gracefully.
Calculates real-time technical indicators (SMA, EMA, RSI).
With rate limiting and timeouts to prevent server overload.
"""

import asyncio
import yfinance as yf
from datetime import datetime
from typing import Optional
import logging
from app.ws.indicators import indicator_calc
import time

logger = logging.getLogger(__name__)


class PriceStreamer:
    """
    Fetches and streams stock prices with rate limiting.
    Uses caching to avoid excessive API calls.
    Implements backoff strategy on errors.
    """

    def __init__(self, update_interval: int = 2):
        """
        Args:
            update_interval: Seconds between price updates (default 2 seconds, minimum 1)
        """
        # Enforce minimum interval to prevent hammering APIs
        self.update_interval = max(2, update_interval)
        self._price_cache: dict = {}
        self._background_tasks = {}
        self._last_fetch_time: dict = {}  # Track last fetch time per symbol

    async def get_latest_price(self, symbol: str) -> Optional[dict]:
        """
        Fetch latest price for a symbol using yfinance with timeout and error handling.
        
        Returns:
            dict with price, timestamp, or None if failed
        """
        try:
            # Check if we've fetched this symbol recently (rate limit)
            now = time.time()
            last_fetch = self._last_fetch_time.get(symbol, 0)
            if now - last_fetch < 1:  # Don't fetch same symbol more than once per second
                return None
            
            self._last_fetch_time[symbol] = now
            
            # Add timeout to yfinance call
            ticker = yf.Ticker(symbol)
            
            # Use asyncio timeout instead of signal
            hist = await asyncio.wait_for(
                asyncio.to_thread(ticker.history, "1d"),
                timeout=5
            )
            
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
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching price for {symbol}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {e}")
            return None

    async def stream_price(self, symbol: str, callback):
        """
        Stream prices for a symbol at regular intervals with error handling.
        Calls callback with price data and indicators each update.
        
        Args:
            symbol: Stock symbol
            callback: Async function to call with price data
        """
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                price_data = await self.get_latest_price(symbol)
                
                if price_data:
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Add price to indicator history
                    indicator_calc.add_price(symbol, price_data["price"])
                    
                    # Calculate indicators
                    indicators = indicator_calc.calculate_all(symbol)
                    
                    # Merge indicators into price data
                    price_data.update(indicators)
                    
                    await callback(symbol, price_data)
                else:
                    consecutive_errors += 1
                    if consecutive_errors <= 1:
                        logger.debug(f"No price data for {symbol}")
                
                # Implement backoff on consecutive errors
                if consecutive_errors > 3:
                    # Exponential backoff: sleep longer with more errors
                    sleep_time = self.update_interval * (2 ** min(consecutive_errors - 3, 3))
                    logger.warning(f"Backoff for {symbol}: sleeping {sleep_time}s after {consecutive_errors} errors")
                    await asyncio.sleep(sleep_time)
                else:
                    # Normal interval
                    await asyncio.sleep(self.update_interval)
                
                # Stop streaming if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Stopping stream for {symbol} after {consecutive_errors} consecutive errors")
                    break
            
            except asyncio.CancelledError:
                logger.info(f"Price stream cancelled for {symbol}")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Unexpected error in price stream for {symbol}: {e}")
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


# Global price streamer instance with 2-second update interval
streamer = PriceStreamer(update_interval=2)
