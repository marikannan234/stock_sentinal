"""
Fast dashboard API routes.

Each section is isolated so one slow upstream source never blocks the others.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routes.portfolio import PortfolioSummaryResponse, get_portfolio_summary
from app.api.routes.stocks_extended import (
    _build_market_summary_from_quotes,
    _get_fallback_market_quotes,
    get_live_stock_quotes,
    get_market_summary,
)
from app.models.user import User
from app.schemas.trading import LiveStockRibbon, MarketSummary
from app.services.news_service import GLOBAL_NEWS_CACHE_KEY, _cache_get, get_global_news

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DASHBOARD_SECTION_TIMEOUT_SECONDS = 0.9
DASHBOARD_FALLBACK_NEWS = (
    {
        "title": "Large-cap tech remains steady while live headlines refresh.",
        "source": "Stock Sentinel",
        "url": "https://example.com/stock-sentinel/fallback-tech",
        "summary": "Fallback dashboard news while the live market feed refreshes.",
    },
    {
        "title": "US equities hold mixed footing ahead of the next macro update.",
        "source": "Stock Sentinel",
        "url": "https://example.com/stock-sentinel/fallback-macro",
        "summary": "Dashboard fallback content keeps the news rail populated during API delays.",
    },
    {
        "title": "Momentum names continue to dominate intraday attention.",
        "source": "Stock Sentinel",
        "url": "https://example.com/stock-sentinel/fallback-momentum",
        "summary": "Fallback headline used when live market news is temporarily unavailable.",
    },
)

_news_refresh_lock = threading.Lock()
_news_refresh_in_progress = False


def _fallback_portfolio_summary() -> PortfolioSummaryResponse:
    return PortfolioSummaryResponse(
        total_invested=0.0,
        current_value=0.0,
        total_pl=0.0,
        percent_pl=0.0,
        day_pl=0.0,
        day_percent=0.0,
        buying_power=0.0,
    )


def _fallback_live_ribbon() -> LiveStockRibbon:
    fallback_quotes = _get_fallback_market_quotes()
    return LiveStockRibbon(
        stocks=fallback_quotes,
        total_count=len(fallback_quotes),
        timestamp=fallback_quotes[0].timestamp,
    )


def _fallback_market_summary() -> MarketSummary:
    return _build_market_summary_from_quotes(_get_fallback_market_quotes())


def _fallback_news(limit: int) -> list[dict]:
    timestamp = datetime.utcnow().isoformat() + "Z"
    fallback_articles = []

    for article in DASHBOARD_FALLBACK_NEWS:
        fallback_articles.append(
            {
                **article,
                "published_at": timestamp,
                "image": None,
            }
        )

    return fallback_articles[:limit]


def _refresh_news_cache(limit: int) -> None:
    global _news_refresh_in_progress

    try:
        get_global_news(use_cache=False, limit=max(limit, 6))
    except Exception as e:
        logger.debug("Dashboard news refresh failed: %s", e)
    finally:
        with _news_refresh_lock:
            _news_refresh_in_progress = False


def _schedule_news_refresh(limit: int) -> None:
    global _news_refresh_in_progress

    with _news_refresh_lock:
        if _news_refresh_in_progress:
            return
        _news_refresh_in_progress = True

    threading.Thread(target=_refresh_news_cache, args=(limit,), daemon=True).start()


def _get_dashboard_portfolio(current_user: User, db: Session) -> PortfolioSummaryResponse:
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_portfolio_summary, current_user=current_user, db=db)
            return future.result(timeout=DASHBOARD_SECTION_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        logger.debug("Dashboard portfolio section timed out; returning fallback data")
        return _fallback_portfolio_summary()
    except Exception as e:
        logger.error("Error fetching dashboard portfolio summary: %s", e)
        return _fallback_portfolio_summary()


def _get_dashboard_market(db: Session) -> MarketSummary:
    try:
        return get_market_summary(db=db)
    except Exception as e:
        logger.error("Error fetching dashboard market summary: %s", e)
        return _fallback_market_summary()


def _get_dashboard_ribbon(db: Session) -> LiveStockRibbon:
    try:
        return get_live_stock_quotes(db=db)
    except Exception as e:
        logger.error("Error fetching dashboard live ribbon: %s", e)
        return _fallback_live_ribbon()


def _get_dashboard_news(limit: int) -> list[dict]:
    cached_news = _cache_get(GLOBAL_NEWS_CACHE_KEY)
    if isinstance(cached_news, list) and cached_news:
        return cached_news[:limit]

    _schedule_news_refresh(limit)
    return _fallback_news(limit)


@router.get("/portfolio", response_model=PortfolioSummaryResponse, summary="Get dashboard portfolio section")
def get_dashboard_portfolio_section(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> PortfolioSummaryResponse:
    return _get_dashboard_portfolio(current_user=current_user, db=db)


@router.get("/market", response_model=MarketSummary, summary="Get dashboard market section")
def get_dashboard_market_section(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> MarketSummary:
    return _get_dashboard_market(db=db)


@router.get("/news", summary="Get dashboard news section")
def get_dashboard_news_section(
    limit: int = Query(3, ge=1, le=20, description="Number of news items"),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    return _get_dashboard_news(limit)


@router.get("/ribbon", response_model=LiveStockRibbon, summary="Get dashboard ribbon section")
def get_dashboard_ribbon_section(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> LiveStockRibbon:
    return _get_dashboard_ribbon(db=db)


@router.get("/data", summary="Get combined dashboard data")
async def get_dashboard_data(
    news_limit: int = Query(3, ge=1, le=20, description="Number of news items"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    return {
        "portfolio": _get_dashboard_portfolio(current_user=current_user, db=db),
        "market": _get_dashboard_market(db=db),
        "ribbon": _get_dashboard_ribbon(db=db),
        "news": _get_dashboard_news(news_limit),
    }
