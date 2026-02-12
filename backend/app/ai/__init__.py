"""
AI module package for StockSentinel.

This package exposes high-level, reusable services for:
- Sentiment analysis over news headlines using FinBERT.
- Short-horizon stock price prediction (next 5 days) using time-series models.
"""

from .sentiment_service import SentimentService  # noqa: F401
from .prediction_service import PredictionService  # noqa: F401

__all__ = ["SentimentService", "PredictionService"]

