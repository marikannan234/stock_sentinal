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
    raise HTTPException(status_code=500, detail="FINNHUB_API_KEY is not configured on the server.")

  url = "https://finnhub.io/api/v1/search"
  params = {"q": q, "token": api_key}

  try:
    resp = requests.get(url, params=params, timeout=8)
  except requests.RequestException:
    raise HTTPException(status_code=502, detail="Failed to reach Finnhub API.")

  if resp.status_code == 429:
    raise HTTPException(
      status_code=429,
      detail="Finnhub rate limit reached. Please wait a few minutes and try again.",
    )
  if resp.status_code == 403:
    raise HTTPException(
      status_code=502,
      detail="Finnhub access forbidden (403). Check FINNHUB_API_KEY and plan access.",
    )
  if resp.status_code != 200:
    raise HTTPException(status_code=502, detail=f"Finnhub API error (status {resp.status_code}).")

  data = resp.json()
  if not isinstance(data, dict):
    raise HTTPException(status_code=502, detail="Unexpected Finnhub response for symbol search.")
  results = data.get("result") or []
  if not isinstance(results, list):
    raise HTTPException(status_code=502, detail="Unexpected Finnhub response for symbol search.")
  return results


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

