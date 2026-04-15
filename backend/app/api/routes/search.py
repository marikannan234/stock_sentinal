from __future__ import annotations

import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])

# ============================================================================
# SEARCH CACHING - 30 second TTL
# ============================================================================
SEARCH_CACHE_TTL_SECONDS = 30

@dataclass(frozen=True)
class _SearchCacheEntry:
    results: List[Dict[str, Any]]
    expires_at: float


_search_cache: Dict[str, _SearchCacheEntry] = {}
_search_cache_lock = threading.Lock()


def _get_search_from_cache(query: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached search results if still valid (30 sec TTL)."""
    now = time.time()
    with _search_cache_lock:
        entry = _search_cache.get(query)
        if entry and entry.expires_at > now:
            logger.debug(f"Search cache HIT for '{query}'")
            return entry.results
        if entry and entry.expires_at <= now:
            del _search_cache[query]  # Clean expired
    return None


def _cache_search_results(query: str, results: List[Dict[str, Any]]) -> None:
    """Cache search results with 30-second TTL."""
    expires_at = time.time() + SEARCH_CACHE_TTL_SECONDS
    with _search_cache_lock:
        _search_cache[query] = _SearchCacheEntry(results=results, expires_at=expires_at)
    logger.debug(f"Cached search results for '{query}' ({len(results)} results)")


class SymbolSearchItem(BaseModel):
  ticker: str = Field(..., description="Ticker symbol (e.g. TSLA)")
  name: str | None = Field(None, description="Company name / description")


def _finnhub_symbol_search(query: str) -> List[Dict[str, Any]]:
  """Search Finnhub with AGGRESSIVE timeout (2 seconds max)."""
  q = query.strip()
  if not q:
    return []

  api_key = settings.FINNHUB_API_KEY
  if not api_key:
    logger.warning("FINNHUB_API_KEY not configured")
    return []

  url = "https://finnhub.io/api/v1/search"
  params = {"q": q, "token": api_key}

  try:
    # Use ThreadPoolExecutor to enforce hard 2-second timeout
    def _fetch():
      return requests.get(url, params=params, timeout=2)
    
    with ThreadPoolExecutor(max_workers=1) as executor:
      future = executor.submit(_fetch)
      try:
        resp = future.result(timeout=2)  # Hard timeout
      except FutureTimeoutError:
        logger.warning(f"⚠️ Finnhub search TIMEOUT for '{q}' (>2s)")
        return []
  except requests.ConnectionError as e:
    logger.warning(f"Finnhub search connection error: {str(e)[:100]}")
    return []
  except requests.RequestException as e:
    logger.warning(f"Finnhub search request error: {str(e)[:100]}")
    return []

  if resp.status_code == 429:
    logger.warning("Finnhub rate limit reached")
    return []
  if resp.status_code == 403:
    logger.warning("Finnhub access forbidden (403)")
    return []
  if resp.status_code != 200:
    logger.warning(f"Finnhub API error {resp.status_code}")
    return []

  try:
    data = resp.json()
    if not isinstance(data, dict):
      return []
    results = data.get("result") or []
    if not isinstance(results, list):
      return []
    logger.debug(f"Finnhub returned {len(results)} results for '{q}'")
    return results
  except Exception as e:
    logger.warning(f"Error parsing Finnhub response: {str(e)[:100]}")
    return []


@router.get("", response_model=list[SymbolSearchItem], summary="Search symbols by query")
def search_symbols(q: str = Query(..., min_length=1, max_length=64)) -> list[SymbolSearchItem]:
  """
  Search symbols with AGGRESSIVE caching (30-second TTL and 2-second timeout).
  Returns up to 8 matching tickers with names.
  """
  start_time = time.time()
  
  # STEP 1: Check cache first
  cached_results = _get_search_from_cache(q)
  if cached_results is not None:
    items: list[SymbolSearchItem] = []
    for r in cached_results:
      symbol = r.get("symbol") or r.get("displaySymbol")
      description = r.get("description") or r.get("name")
      if not symbol:
        continue
      items.append(SymbolSearchItem(ticker=str(symbol).upper(), name=str(description).strip() or None))
      if len(items) >= 8:
        break
    fetch_time = (time.time() - start_time) * 1000
    logger.info(f"✓ Search cache HIT for '{q}' ({fetch_time:.1f}ms)")
    return items

  # STEP 2: Fetch from Finnhub with timeout protection
  logger.debug(f"Search cache miss for '{q}', fetching from Finnhub...")
  raw_results = _finnhub_symbol_search(q)
  
  # Cache the results for future requests
  _cache_search_results(q, raw_results)
  
  items: list[SymbolSearchItem] = []
  for r in raw_results:
    symbol = r.get("symbol") or r.get("displaySymbol")
    description = r.get("description") or r.get("name")
    if not symbol:
      continue
    items.append(SymbolSearchItem(ticker=str(symbol).upper(), name=str(description).strip() or None))
    if len(items) >= 8:
      break
  
  fetch_time = (time.time() - start_time) * 1000
  logger.info(f"✓ Search results for '{q}': {len(items)} items ({fetch_time:.0f}ms)")
  
  if fetch_time > 1000:
    logger.warning(f"⚠️ SLOW: Search took {fetch_time:.0f}ms (target <1000ms)")
  
  return items

