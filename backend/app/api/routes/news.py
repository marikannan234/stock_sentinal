"""
News Routes Module

Comprehensive news API endpoints:
- GET /news/global - Global market news
- GET /news/{symbol} - Stock-specific news
- GET /news/{symbol}/sentiment - News with sentiment analysis
- POST /news/sentiment/analyze - Analyze sentiment of articles
- POST /news/cache/clear - Clear news cache

Features:
- Real-time news fetching from Finnhub
- AI-powered sentiment analysis using VADER and TextBlob
- Investment insights generation
- 5-minute intelligent caching
- Production-grade error handling and logging
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.exceptions import ValidationError
from app.models.user import User
from app.services.news_service import (
    get_stock_news,
    get_global_news,
    clear_cache,
)
from app.services.sentiment_service import (
    analyze_articles,
    generate_insight,
    get_sentiment_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


# ============================================
# Request/Response Models
# ============================================
class NewsArticle(BaseModel):
    """Single news article."""
    title: str = Field(..., description="Article title/headline")
    source: str = Field(..., description="Publisher/source name")
    url: str = Field(..., description="Canonical URL")
    summary: Optional[str] = Field(None, description="Article summary")
    image: Optional[str] = Field(None, description="Article image URL")
    published_at: Optional[str] = Field(None, description="ISO8601 timestamp (UTC)")


class NewsResponse(BaseModel):
    """Response with news articles."""
    articles: List[NewsArticle]
    count: int


class ArticleWithSentiment(NewsArticle):
    """News article with sentiment analysis."""
    sentiment: str = Field(..., description="POSITIVE, NEGATIVE, or NEUTRAL")
    sentiment_score: float = Field(..., description="Sentiment score 0.0-1.0")
    sentiment_confidence: float = Field(..., description="Confidence 0.0-1.0")


class SentimentInsight(BaseModel):
    """Investment insight from sentiment analysis."""
    sentiment_score: float = Field(..., description="Overall sentiment 0.0-1.0")
    sentiment_label: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    recommendation: str = Field(..., description="Investment recommendation")
    confidence: float = Field(..., description="Confidence 0.0-1.0")
    analysis_count: int = Field(..., description="Number of articles analyzed")


class NewsWithSentimentResponse(BaseModel):
    """Complete response with news and sentiment analysis."""
    articles: List[ArticleWithSentiment]
    sentiment_analysis: SentimentInsight
    count: int


class AnalyzeSentimentRequest(BaseModel):
    """Request to analyze sentiment of articles."""
    articles: List[Dict[str, Any]] = Field(..., description="List of articles to analyze")


# ============================================
# Global News Endpoint
# ============================================
@router.get(
    "/",
    response_model=NewsResponse,
    summary="Get global market news",
    description="Fetch latest financial and economic news from around the world.",
)
async def get_global_news_endpoint(
    limit: int = Query(30, ge=1, le=100, description="Number of articles to return"),
) -> NewsResponse:
    """
    Get global market news.
    
    Features:
    - Stock market news
    - Economic news (inflation, interest rates, recession)
    - Company news affecting markets
    - 5-minute intelligent cache
    
    Returns:
        NewsResponse with articles list
    """
    try:
        logger.info(f"Fetching global news (limit: {limit})")
        
        articles = get_global_news(use_cache=True, limit=limit)
        
        # Convert to Pydantic models
        news_articles = [
            NewsArticle(
                title=article["title"],
                source=article["source"],
                url=article["url"],
                summary=article.get("summary"),
                image=article.get("image"),
                published_at=article.get("published_at"),
            )
            for article in articles
        ]
        
        logger.info(f"Successfully retrieved {len(news_articles)} global news articles")
        
        return NewsResponse(
            articles=news_articles,
            count=len(news_articles),
        )
    
    except Exception as e:
        logger.error(f"Error fetching global news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch global news")


# ============================================
# Stock-Specific News Endpoint
# ============================================
@router.get(
    "/{symbol}",
    response_model=NewsResponse,
    summary="Get stock-specific news",
    description="Fetch latest news for a specific stock symbol.",
)
async def get_stock_news_endpoint(
    symbol: str = Path(..., min_length=1, max_length=10, description="Stock ticker symbol (e.g., AAPL)"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),

) -> NewsResponse:
    """
    Get news for a specific stock.
    
    Features:
    - Company-specific updates
    - Earnings announcements
    - Analyst opinions
    - 5-minute intelligent cache
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, TSLA)
        limit: Maximum number of articles to return
    
    Returns:
        NewsResponse with articles for the stock
    """
    try:
        logger.info(f"Fetching news for {symbol} (limit: {limit})")
        
        articles = get_stock_news(symbol=symbol, use_cache=True, limit=limit)
        
        # Convert to Pydantic models
        news_articles = [
            NewsArticle(
                title=article["title"],
                source=article["source"],
                url=article["url"],
                summary=article.get("summary"),
                image=article.get("image"),
                published_at=article.get("published_at"),
            )
            for article in articles
        ]
        
        logger.info(f"Successfully retrieved {len(news_articles)} articles for {symbol}")
        
        return NewsResponse(
            articles=news_articles,
            count=len(news_articles),
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error for symbol {symbol}: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except Exception as e:
        logger.error(f"Error fetching news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news for {symbol}")


# ============================================
# Stock News with Sentiment Analysis Endpoint
# ============================================
@router.get(
    "/{symbol}/sentiment",
    response_model=NewsWithSentimentResponse,
    summary="Get stock news with sentiment analysis",
    description="Fetch news with AI-powered sentiment and investment insights.",
)
async def get_stock_news_with_sentiment(
    symbol: str = Path(..., min_length=1, max_length=10, description="Stock ticker symbol"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
) -> NewsWithSentimentResponse:
    """
    Get stock news with AI sentiment analysis and investment recommendations.
    
    Features:
    - Fetches latest news for the stock
    - Analyzes sentiment of each article (POSITIVE/NEGATIVE/NEUTRAL)
    - Generates overall investment insight (BULLISH/BEARISH/NEUTRAL)
    - Provides confidence scores
    - 5-minute intelligent cache
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, TSLA)
        limit: Maximum number of articles to return
    
    Returns:
        NewsWithSentimentResponse with articles and sentiment analysis
    """
    try:
        logger.info(f"Fetching news with sentiment for {symbol} (limit: {limit})")
        
        # Get articles
        articles = get_stock_news(symbol=symbol, use_cache=True, limit=limit)
        
        if not articles:
            logger.warning(f"No news found for {symbol}")
            return NewsWithSentimentResponse(
                articles=[],
                sentiment_analysis=SentimentInsight(
                    sentiment_score=0.5,
                    sentiment_label="NEUTRAL",
                    recommendation="No news available for analysis",
                    confidence=0.0,
                    analysis_count=0,
                ),
                count=0,
            )
        
        # Analyze sentiment
        sentiment_summary = get_sentiment_summary(articles)
        
        # Build response articles with sentiment
        response_articles = [
            ArticleWithSentiment(
                title=article["title"],
                source=article["source"],
                url=article["url"],
                summary=article.get("summary"),
                image=article.get("image"),
                published_at=article.get("published_at"),
                sentiment=sentiment_summary["articles"][idx]["sentiment"],
                sentiment_score=sentiment_summary["articles"][idx]["sentiment_score"],
                sentiment_confidence=sentiment_summary["articles"][idx]["sentiment_confidence"],
            )
            for idx, article in enumerate(articles)
        ]
        
        logger.info(
            f"Successfully analyzed {len(response_articles)} articles for {symbol}. "
            f"Overall sentiment: {sentiment_summary['sentiment_label']}"
        )
        
        return NewsWithSentimentResponse(
            articles=response_articles,
            sentiment_analysis=SentimentInsight(
                sentiment_score=sentiment_summary["sentiment_score"],
                sentiment_label=sentiment_summary["sentiment_label"],
                recommendation=sentiment_summary["recommendation"],
                confidence=sentiment_summary["confidence"],
                analysis_count=sentiment_summary["analysis_count"],
            ),
            count=len(response_articles),
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error for symbol {symbol}: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")


# ============================================
# Manual Sentiment Analysis Endpoint
# ============================================
@router.post(
    "/sentiment/analyze",
    response_model=SentimentInsight,
    summary="Analyze sentiment of articles",
    description="Analyze sentiment and generate investment insight from a list of articles.",
)
async def analyze_sentiment_endpoint(
    request: AnalyzeSentimentRequest,
    current_user: User = Depends(get_current_user),
) -> SentimentInsight:
    """
    Analyze sentiment of provided articles and generate investment insight.
    
    This endpoint allows you to submit articles for sentiment analysis without
    needing to fetch them from our API first.
    
    Args:
        request: List of articles with title and optional summary
    
    Returns:
        SentimentInsight with overall sentiment and recommendation
    """
    try:
        if not request.articles:
            raise ValidationError(
                message="Articles list cannot be empty",
                details={"articles": []}
            )
        
        logger.info(f"Analyzing sentiment for {len(request.articles)} articles")
        
        # Analyze articles
        analyzed = analyze_articles(request.articles)
        
        # Generate insight
        insight = generate_insight(analyzed)
        
        logger.info(f"Sentiment analysis complete. Label: {insight.sentiment_label}")
        
        return SentimentInsight(
            sentiment_score=insight.sentiment_score,
            sentiment_label=insight.sentiment_label,
            recommendation=insight.recommendation,
            confidence=insight.confidence,
            analysis_count=insight.analysis_count,
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error in sentiment analysis: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")


# ============================================
# Cache Management Endpoint
# ============================================
@router.post(
    "/cache/clear",
    summary="Clear news cache",
    description="Clear cached news for a symbol or all caches.",
)
async def clear_news_cache(
    symbol: Optional[str] = Query(
        None,
        description="Stock symbol to clear cache for. If not provided, clears all cache.",
    ),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Clear news cache.
    
    Args:
        symbol: Optional stock symbol. If provided, only clears cache for that symbol.
                If not provided, clears all news caches.
    
    Returns:
        Status message
    """
    try:
        if symbol:
            clear_cache(symbol=symbol)
            logger.info(f"Cleared news cache for {symbol}")
            return {"message": f"Cache cleared for {symbol}"}
        else:
            clear_cache()
            logger.info("Cleared all news caches")
            return {"message": "All news caches cleared"}
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

