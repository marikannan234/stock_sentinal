from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/news", tags=["news"])


class NewsArticle(BaseModel):
    title: str = Field(..., description="Article title/headline")
    source: str = Field(..., description="Publisher/source name")
    url: str = Field(..., description="Canonical URL")
    published_at: str = Field(..., description="ISO8601 timestamp (UTC)")


class NewsResponse(BaseModel):
    ticker: str
    articles: List[NewsArticle]


def _finnhub_company_news(ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
    ticker_upper = ticker.upper().strip()
    if not ticker_upper:
        raise HTTPException(status_code=400, detail="Ticker symbol cannot be empty")

    api_key = settings.FINNHUB_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="FINNHUB_API_KEY is not configured on the server.")

    # Finnhub requires a date range (YYYY-MM-DD). Use last 7 days for "latest" news.
    to_d = date.today()
    from_d = to_d - timedelta(days=7)

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker_upper,
        "from": from_d.isoformat(),
        "to": to_d.isoformat(),
        "token": api_key,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
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
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Unexpected Finnhub response for news.")

    # Sort newest-first and clamp.
    data_sorted = sorted(data, key=lambda x: int(x.get("datetime") or 0), reverse=True)
    return data_sorted[: max(0, min(limit, 25))]  # hard cap for safety


def _map_company_news_item(item: Dict[str, Any]) -> NewsArticle | None:
    headline = item.get("headline")
    source = item.get("source")
    url = item.get("url")
    dt = item.get("datetime")
    if not headline or not source or not url or not dt:
        return None
    try:
        published = datetime.fromtimestamp(int(dt), tz=timezone.utc).isoformat()
    except Exception:
        published = datetime.now(tz=timezone.utc).isoformat()
    return NewsArticle(title=str(headline), source=str(source), url=str(url), published_at=published)


@router.get("/{ticker}", response_model=NewsResponse, summary="Get latest news for ticker")
def get_ticker_news(
    ticker: str = Path(..., description="Stock ticker symbol (e.g., AAPL, TSLA)", min_length=1, max_length=10),
    _: User = Depends(get_current_user),
) -> NewsResponse:
    """
    Fetch latest 5–10 news articles for a ticker from Finnhub company-news endpoint.
    Returns title, source, url, published_at (UTC).
    """
    raw = _finnhub_company_news(ticker, limit=10)
    articles: List[NewsArticle] = []
    for it in raw:
        mapped = _map_company_news_item(it)
        if mapped is not None:
            articles.append(mapped)
        if len(articles) >= 10:
            break
    return NewsResponse(ticker=ticker.upper().strip(), articles=articles)

