"""
News Service Module

Provides comprehensive news fetching and caching:
- Global market news
- Stock-specific news
- Real-time news from Finnhub and NewsAPI
- Intelligent caching to avoid repeated API calls

Features:
- 5-minute cache TTL
- Error handling and fallback
- Structured news format
- Async support
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import threading
import requests

from app.config import settings
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ============================================
# Cache Configuration
# ============================================
NEWS_CACHE_TTL_SECONDS = 5 * 60  # 5 minutes
GLOBAL_NEWS_CACHE_KEY = "global_news"


# ============================================
# Cache Data Structure
# ============================================
@dataclass(frozen=True)
class _CacheEntry:
    """Thread-safe cache entry with expiration."""
    expires_at_monotonic: float
    value: Any


# ============================================
# In-Memory Cache (Thread-Safe)
# ============================================
_cache_lock = threading.Lock()
_cache: Dict[str, _CacheEntry] = {}


def _cache_get(key: str) -> Optional[Any]:
    """Get cached value if not expired."""
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        if entry.expires_at_monotonic <= now:
            _cache.pop(key, None)
            return None
        return entry.value


def _cache_set(key: str, value: Any) -> None:
    """Set cache entry with TTL."""
    expires = time.monotonic() + NEWS_CACHE_TTL_SECONDS
    with _cache_lock:
        _cache[key] = _CacheEntry(expires_at_monotonic=expires, value=value)


def _cache_clear(key: Optional[str] = None) -> None:
    """Clear specific or all cache entries."""
    with _cache_lock:
        if key:
            _cache.pop(key, None)
        else:
            _cache.clear()


# ============================================
# News Article Model
# ============================================
class NewsArticle:
    """Structured news article."""
    
    def __init__(
        self,
        title: str,
        source: str,
        url: str,
        summary: Optional[str] = None,
        image: Optional[str] = None,
        published_at: Optional[str] = None,
    ):
        self.title = title
        self.source = source
        self.url = url
        self.summary = summary
        self.image = image
        self.published_at = published_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "summary": self.summary,
            "image": self.image,
            "published_at": self.published_at,
        }


# ============================================
# Finnhub News Fetcher
# ============================================
def _fetch_finnhub_company_news(
    symbol: str,
    days_back: int = 7,
    limit: int = 20,
) -> List[NewsArticle]:
    """
    Fetch company-specific news from Finnhub.
    
    Args:
        symbol: Stock ticker symbol
        days_back: Number of days to look back
        limit: Maximum number of articles
    
    Returns:
        List of NewsArticle objects
    """
    symbol = symbol.upper().strip()
    
    if not settings.FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not configured")
        return []
    
    try:
        to_date = date.today()
        from_date = to_date - timedelta(days=days_back)
        
        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "token": settings.FINNHUB_API_KEY,
        }
        
        logger.info(f"Fetching Finnhub news for {symbol}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for item in data[:limit]:
            try:
                article = NewsArticle(
                    title=item.get("headline", ""),
                    source=item.get("source", "Finnhub"),
                    url=item.get("url", ""),
                    summary=item.get("summary", ""),
                    image=item.get("image", None),
                    published_at=_format_timestamp(item.get("datetime")),
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing Finnhub article: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(articles)} articles from Finnhub for {symbol}")
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Finnhub API error for {symbol}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching Finnhub news: {e}")
        return []


# ============================================
# Global News Fetcher
# ============================================
def _fetch_global_market_news(limit: int = 30) -> List[NewsArticle]:
    """
    Fetch global market news from Finnhub general news endpoint.
    
    Args:
        limit: Maximum number of articles
    
    Returns:
        List of NewsArticle objects
    """
    if not settings.FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not configured")
        return []
    
    try:
        url = "https://finnhub.io/api/v1/news"
        params = {
            "category": "general",
            "token": settings.FINNHUB_API_KEY,
            "minId": 0,
        }
        
        logger.info("Fetching global market news from Finnhub")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for item in data[:limit]:
            try:
                article = NewsArticle(
                    title=item.get("headline", ""),
                    source=item.get("source", "Finnhub"),
                    url=item.get("url", ""),
                    summary=item.get("summary", ""),
                    image=item.get("image", None),
                    published_at=_format_timestamp(item.get("datetime")),
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing global news article: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(articles)} global news articles")
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Finnhub global news API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching global news: {e}")
        return []


# ============================================
# Public API Functions
# ============================================
def get_stock_news(symbol: str, use_cache: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get news for a specific stock with optional caching.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        use_cache: Whether to use cached results
        limit: Maximum number of articles to return
    
    Returns:
        List of news articles as dictionaries
    
    Raises:
        ValidationError: If symbol is invalid
    """
    symbol = symbol.upper().strip()
    
    if not symbol:
        raise ValidationError(
            message="Stock symbol cannot be empty",
            details={"symbol": symbol}
        )
    
    if len(symbol) > 10:
        raise ValidationError(
            message="Invalid stock symbol",
            details={"symbol": symbol}
        )
    
    cache_key = f"stock_news:{symbol}"
    
    # Check cache
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info(f"Returning cached news for {symbol}")
            return cached[:limit]
    
    # Fetch fresh news
    articles = _fetch_finnhub_company_news(symbol, limit=limit)
    
    # Convert to dict
    result = [article.to_dict() for article in articles]
    
    # Cache result
    _cache_set(cache_key, result)
    
    return result


def get_global_news(use_cache: bool = True, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Get global market news with optional caching.
    
    Args:
        use_cache: Whether to use cached results
        limit: Maximum number of articles to return
    
    Returns:
        List of news articles as dictionaries
    """
    cache_key = GLOBAL_NEWS_CACHE_KEY
    
    # Check cache
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info("Returning cached global news")
            return cached[:limit]
    
    # Fetch fresh news
    articles = _fetch_global_market_news(limit=limit)
    
    # Convert to dict
    result = [article.to_dict() for article in articles]
    
    # Cache result
    _cache_set(cache_key, result)
    
    return result


# ============================================
# Utility Functions
# ============================================
def _format_timestamp(timestamp: Optional[int]) -> Optional[str]:
    """
    Convert Unix timestamp to ISO 8601 format.
    
    Args:
        timestamp: Unix timestamp or None
    
    Returns:
        ISO 8601 formatted datetime string or None
    """
    if not timestamp:
        return None
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.isoformat() + "Z"
    except (ValueError, OSError, TypeError):
        return None


def clear_cache(symbol: Optional[str] = None) -> None:
    """
    Clear cache for a symbol or all caches.
    
    Args:
        symbol: Stock symbol to clear cache for, or None to clear all
    """
    if symbol:
        cache_key = f"stock_news:{symbol.upper()}"
        _cache_clear(cache_key)
        logger.info(f"Cleared cache for {symbol}")
    else:
        _cache_clear()
        logger.info("Cleared all news caches")
