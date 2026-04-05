from __future__ import annotations

from dataclasses import dataclass
import re
import threading
import time
from typing import List, Literal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.news_service import get_stock_news
from app.models.user import User

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

_CACHE_TTL_SECONDS = 10 * 60  # 10 minutes


SentimentLabel = Literal["bullish", "neutral", "bearish"]
ArticleSentimentLabel = Literal["positive", "neutral", "negative"]


class SentimentArticle(BaseModel):
    title: str
    source: str
    url: str
    published_at: str
    sentiment: ArticleSentimentLabel
    score: float = Field(..., description="Article sentiment score normalized to [0,1]")


class SentimentResponse(BaseModel):
    ticker: str
    overall_sentiment: SentimentLabel
    score: float = Field(..., description="Overall sentiment score normalized to [0,1]")
    articles: List[SentimentArticle]


# ---- Simple in-memory cache (per process) ----
@dataclass(frozen=True)
class _CacheEntry:
    expires_at_monotonic: float
    value: SentimentResponse


_cache_lock = threading.Lock()
_cache: dict[str, _CacheEntry] = {}


def _cache_get(ticker: str) -> SentimentResponse | None:
    now = time.monotonic()
    with _cache_lock:
        entry = _cache.get(ticker)
        if not entry:
            return None
        if entry.expires_at_monotonic <= now:
            _cache.pop(ticker, None)
            return None
        return entry.value


def _cache_set(ticker: str, value: SentimentResponse) -> None:
    expires = time.monotonic() + _CACHE_TTL_SECONDS
    with _cache_lock:
        _cache[ticker] = _CacheEntry(expires_at_monotonic=expires, value=value)


# ---- Lightweight sentiment scoring (rule-based) ----
_POS_WORDS = {
    "beats",
    "beat",
    "surge",
    "surges",
    "soar",
    "soars",
    "soared",
    "rally",
    "rallies",
    "rallied",
    "growth",
    "record",
    "strong",
    "upside",
    "upgrade",
    "upgrades",
    "upgraded",
    "profit",
    "profits",
    "bull",
    "bullish",
    "outperform",
    "buy",
    "raises",
    "raise",
    "raised",
    "guidance",
    "wins",
    "win",
    "won",
}
_NEG_WORDS = {
    "miss",
    "misses",
    "missed",
    "drop",
    "drops",
    "dropped",
    "plunge",
    "plunges",
    "plunged",
    "slump",
    "slumps",
    "slumped",
    "weak",
    "downgrade",
    "downgrades",
    "downgraded",
    "lawsuit",
    "probe",
    "fraud",
    "loss",
    "losses",
    "bear",
    "bearish",
    "sell",
    "cuts",
    "cut",
    "cutting",
    "warning",
    "warns",
    "warned",
    "recall",
    "bankruptcy",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if t]


def _raw_sentiment_score(text: str) -> float:
    """
    Returns score in [-1, 1] using a tiny lexicon.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    pos = sum(1 for t in tokens if t in _POS_WORDS)
    neg = sum(1 for t in tokens if t in _NEG_WORDS)
    denom = max(pos + neg, 1)
    return (pos - neg) / denom


def _to_label(score_raw: float) -> ArticleSentimentLabel:
    if score_raw > 0.15:
        return "positive"
    if score_raw < -0.15:
        return "negative"
    return "neutral"


def _overall_label(score_raw: float) -> SentimentLabel:
    if score_raw > 0.15:
        return "bullish"
    if score_raw < -0.15:
        return "bearish"
    return "neutral"


def _normalize_01(score_raw: float) -> float:
    # Map [-1, 1] -> [0, 1]
    v = (score_raw + 1.0) / 2.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return float(v)


@router.get("/{ticker}", response_model=SentimentResponse, summary="Get news-based sentiment for ticker")
async def get_ticker_sentiment(
    ticker: str = Path(..., description="Stock ticker symbol (e.g., AAPL, TSLA)", min_length=1, max_length=10),
    _: User = Depends(get_current_user),
) -> SentimentResponse:
    """
    Combines:
    - News fetch (Finnhub company-news via news service)
    - Lightweight rule-based sentiment over article headlines
    Cached per ticker for 10 minutes (in-memory, per process).
    """
    ticker_upper = ticker.upper().strip()
    cached = _cache_get(ticker_upper)
    if cached is not None:
        return cached

    # Use service layer to get news
    raw_news = get_stock_news(ticker_upper, limit=10)
    articles: List[SentimentArticle] = []
    raw_scores: List[float] = []

    for it in raw_news:
        title = it.get("title") or ""
        source = it.get("source") or ""
        url = it.get("url") or ""
        published_at = it.get("published_at")
        if not title or not source or not url or not published_at:
            continue

        score_raw = _raw_sentiment_score(str(title))
        raw_scores.append(score_raw)

        articles.append(
            SentimentArticle(
                title=str(title),
                source=str(source),
                url=str(url),
                published_at=str(published_at),
                sentiment=_to_label(score_raw),
                score=round(_normalize_01(score_raw), 2),
            )
        )
        if len(articles) >= 10:
            break

    avg_raw = sum(raw_scores) / len(raw_scores) if raw_scores else 0.0
    response = SentimentResponse(
        ticker=ticker_upper,
        overall_sentiment=_overall_label(avg_raw),
        score=round(_normalize_01(avg_raw), 2),
        articles=articles,
    )
    _cache_set(ticker_upper, response)
    return response

