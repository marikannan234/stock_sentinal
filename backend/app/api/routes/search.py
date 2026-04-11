from __future__ import annotations

from typing import Any, Dict, List

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter(prefix="/search", tags=["search"])


class SymbolSearchItem(BaseModel):
  ticker: str = Field(..., description="Ticker symbol (e.g. TSLA)")
  name: str | None = Field(None, description="Company name / description")


def _finnhub_symbol_search(query: str) -> List[Dict[str, Any]]:
  q = query.strip()
  if not q:
    return []

  api_key = settings.FINNHUB_API_KEY
  if not api_key:
    import logging
    logging.getLogger(__name__).warning("FINNHUB_API_KEY not configured")
    return []  # Return empty list instead of raising

  url = "https://finnhub.io/api/v1/search"
  params = {"q": q, "token": api_key}

  try:
    resp = requests.get(url, params=params, timeout=5)  # Reduced timeout to 5 seconds
  except requests.Timeout:
    import logging
    logging.getLogger(__name__).warning(f"Finnhub search timeout for query: {q}")
    return []  # Return empty list on timeout
  except requests.ConnectionError as e:
    import logging
    logging.getLogger(__name__).warning(f"Finnhub search connection error: {e}")
    return []  # Return empty list on connection error
  except requests.RequestException as e:
    import logging
    logging.getLogger(__name__).warning(f"Finnhub search request error: {e}")
    return []  # Return empty list instead of raising

  if resp.status_code == 429:
    import logging
    logging.getLogger(__name__).warning("Finnhub rate limit reached")
    return []  # Return empty list instead of raising
  if resp.status_code == 403:
    import logging
    logging.getLogger(__name__).warning("Finnhub access forbidden (403)")
    return []  # Return empty list instead of raising
  if resp.status_code != 200:
    import logging
    logging.getLogger(__name__).warning(f"Finnhub API error {resp.status_code}")
    return []  # Return empty list instead of raising

  try:
    data = resp.json()
    if not isinstance(data, dict):
      return []
    results = data.get("result") or []
    if not isinstance(results, list):
      return []
    return results
  except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Error parsing Finnhub response: {e}")
    return []  # Return empty list on parse error


@router.get("", response_model=list[SymbolSearchItem], summary="Search symbols by query")
def search_symbols(q: str = Query(..., min_length=1, max_length=64)) -> list[SymbolSearchItem]:
  """
  Proxy Finnhub symbol search.
  Returns up to 8 matching tickers with names.
  """
  raw_results = _finnhub_symbol_search(q)
  items: list[SymbolSearchItem] = []
  for r in raw_results:
    symbol = r.get("symbol") or r.get("displaySymbol")
    description = r.get("description") or r.get("name")
    if not symbol:
      continue
    items.append(
      SymbolSearchItem(
        ticker=str(symbol).upper(),
        name=str(description).strip() or None,
      )
    )
    if len(items) >= 8:
      break
  return items

