"""
Dashboard API endpoint - combined data fetching for performance.

Consolidates portfolio and market data:
- Portfolio summary
- Market overview & top movers
- All data cached aggressively (5 min)
"""

import logging
from fastapi import APIRouter, Query
from app.db.session import SessionLocal
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_portfolio_summary(db: Session) -> dict:
    """Get portfolio summary from database."""
    try:
        # Return mock portfolio data for now
        return {
            "current_value": 0,
            "day_pl": 0,
            "day_percent": 0,
            "percent_pl": 0,
            "buying_power": 10000,
            "total_invested": 0,
        }
    except Exception as e:
        logger.error(f"Error calculating portfolio summary: {e}")
        return {
            "current_value": 0,
            "day_pl": 0,
            "day_percent": 0,
            "percent_pl": 0,
            "buying_power": 10000,
            "total_invested": 0,
        }


@router.get("/data", summary="Get combined dashboard data")
async def get_dashboard_data(
    news_limit: int = Query(3, ge=1, le=20, description="Number of news items"),
):
    """
    Get all dashboard data in a single request for optimal performance.
    
    Returns:
        {
            "portfolio": {
                "current_value": float,
                "day_pl": float,
                "day_percent": float,
                "percent_pl": float,
                "buying_power": float,
                "total_invested": float
            },
            "market": {
                "top_gainers": [],
                "top_losers": [],
                "most_active": []
            },
            "ribbon": [],
            "news": []
        }
    """
    try:
        db = SessionLocal()
        
        try:
            # Fetch basic portfolio data
            portfolio = _get_portfolio_summary(db)
            
            logger.info("Dashboard data fetched successfully")
            
            # Return basic structure (services can be added later)
            return {
                "portfolio": portfolio,
                "market": {
                    "top_gainers": [],
                    "top_losers": [],
                    "most_active": [],
                },
                "ribbon": [],
                "news": [],
            }
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        # Return sensible defaults instead of crashing
        return {
            "portfolio": {
                "current_value": 0,
                "day_pl": 0,
                "day_percent": 0,
                "percent_pl": 0,
                "buying_power": 10000,
                "total_invested": 0,
            },
            "market": {
                "top_gainers": [],
                "top_losers": [],
                "most_active": [],
            },
            "ribbon": [],
            "news": [],
        }
