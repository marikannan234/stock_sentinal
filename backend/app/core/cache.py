"""
Global cache utility for Stock Sentinel API.

Features:
  - Thread-safe caching with TTL (time-to-live)
  - Simple key-value storage
  - Automatic expiration handling
  - Used across all API calls to prevent duplicate requests
"""

import threading
import time
from typing import Any, Optional, TypeVar, Generic, Dict

T = TypeVar('T')


class CacheEntry(Generic[T]):
    """Single cache entry with expiration tracking."""
    
    def __init__(self, value: T, ttl_seconds: int):
        self.value = value
        self.expires_at_monotonic = time.monotonic() + ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.monotonic() >= self.expires_at_monotonic


class Cache(Generic[T]):
    """
    Thread-safe TTL cache.
    
    Usage:
        cache = Cache(ttl_seconds=300)
        cache.set('user:1:data', some_data)
        data = cache.get('user:1:data')
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for all entries (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self._storage: Dict[str, CacheEntry[Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache.
        
        Returns None if key doesn't exist or is expired.
        """
        with self._lock:
            entry = self._storage.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                # Clean up expired entry
                del self._storage[key]
                return None
            
            return entry.value
    
    def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses instance default if not provided)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        with self._lock:
            self._storage[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        with self._lock:
            self._storage.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._storage.clear()
    
    def get_or_set(self, key: str, default_factory, ttl_seconds: Optional[int] = None) -> T:
        """
        Get value from cache, or compute and cache a default.
        
        Args:
            key: Cache key
            default_factory: Callable that returns default value if key not found
            ttl_seconds: Optional custom TTL
        
        Returns:
            Cached value or newly computed default
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute default
        value = default_factory()
        self.set(key, value, ttl_seconds)
        return value
    
    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            expired_count = sum(1 for entry in self._storage.values() if entry.is_expired())
            return {
                "total_entries": len(self._storage),
                "expired_entries": expired_count,
                "active_entries": len(self._storage) - expired_count,
            }


# Global stock quote cache (5 second TTL)
stock_quote_cache = Cache(ttl_seconds=5)

# Global stock candle cache (5 second TTL)
stock_candle_cache = Cache(ttl_seconds=5)

# Global indicator cache (10 second TTL)
indicator_cache = Cache(ttl_seconds=10)

# Global news cache (30 second TTL)
news_cache = Cache(ttl_seconds=30)

# Global sentiment cache (60 second TTL)
sentiment_cache = Cache(ttl_seconds=60)
