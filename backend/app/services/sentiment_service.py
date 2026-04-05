"""
Sentiment Analysis Service Module

Provides AI-based sentiment analysis for financial news:
- Article-level sentiment scoring
- Overall sentiment analysis for stocks
- Investment recommendations
- Confidence scoring

Features:
- TextBlob-based NLP sentiment analysis
- VADER sentiment scoring
- Rule-based keywords for financial context
- Investment insights generation
- Caching and performance optimization
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple, Any
from enum import Enum

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    logging.warning("TextBlob not installed. Install with: pip install textblob")

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk
    # Download required VADER lexicon
    try:
        nltk.data.find('sentiment/vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    HAS_VADER = True
except ImportError:
    HAS_VADER = False
    logging.warning("VADER/NLTK not installed. Install with: pip install nltk")

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ============================================
# Sentiment Types
# ============================================
SentimentLabel = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
RecommendationLabel = Literal["BULLISH", "BEARISH", "NEUTRAL"]


# ============================================
# Sentiment Analysis Models
# ============================================
@dataclass
class ArticleSentiment:
    """Sentiment for a single article."""
    title: str
    source: str
    sentiment: SentimentLabel
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0


@dataclass
class SentimentInsight:
    """Investment insight based on sentiment analysis."""
    sentiment_score: float  # 0.0 to 1.0
    sentiment_label: RecommendationLabel
    recommendation: str
    confidence: float  # 0.0 to 1.0
    analysis_count: int


# ============================================
# Financial Keywords (Rule-Based Sentiment)
# ============================================
POSITIVE_KEYWORDS = {
    "beat", "beats", "surge", "surges", "soar", "soars", "soared",
    "rally", "rallies", "rallied", "gains", "gain", "recovery",
    "growth", "strong", "upgrade", "upgrades", "outperform",
    "profit", "profits", "revenue", "guidance", "raise", "raises",
    "bull", "bullish", "bullish", "positive", "optimistic",
    "record", "breakthrough", "innovation", "success", "winner",
    "expansion", "momentum", "upward", "outperform", "buying",
    "beat expectations", "exceeds", "exceed", "upside",
    "analyst upgrade", "target raise", "initiates coverage buy",
}

NEGATIVE_KEYWORDS = {
    "miss", "misses", "missed", "down", "decline", "declines",
    "loss", "losses", "drop", "drops", "crash", "plunge",
    "plunges", "weak", "weakness", "downgrade", "downgrades",
    "downside", "negative", "pessimistic", "bear", "bearish",
    "recession", "bankruptcy", "scandal", "fraud", "lawsuit",
    "risk", "warning", "concern", "concerns", "problem",
    "unfavorable", "disappointing", "sells", "sell-off",
    "missed estimates", "below expectations", "disappoints",
    "analyst downgrade", "target cut", "discontinued",
}

NEUTRAL_KEYWORDS = {
    "report", "reports", "statement", "announces", "announces",
    "update", "updates", "meeting", "conference", "event",
    "news", "today", "yesterday", "company", "stock",
}


# ============================================
# VADER Sentiment Analyzer (More accurate for financial text)
# ============================================
class SentimentAnalyzer:
    """Multi-method sentiment analyzer for financial news."""
    
    def __init__(self):
        """Initialize sentiment analyzer with available libraries."""
        self.use_vader = HAS_VADER
        self.use_textblob = HAS_TEXTBLOB
        
        if self.use_vader:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize VADER: {e}")
                self.use_vader = False
        
        if not self.use_textblob and not self.use_vader:
            logger.warning("No sentiment analysis library available. Using rule-based analysis.")
    
    def analyze_text(self, text: str) -> Tuple[SentimentLabel, float, float]:
        """
        Analyze sentiment of text using best available method.
        
        Args:
            text: Text to analyze
        
        Returns:
            Tuple of (sentiment_label, score, confidence)
            - sentiment_label: "POSITIVE", "NEGATIVE", or "NEUTRAL"
            - score: 0.0 to 1.0 (0 = negative, 0.5 = neutral, 1.0 = positive)
            - confidence: 0.0 to 1.0 (how confident we are)
        """
        if not text or not isinstance(text, str):
            return "NEUTRAL", 0.5, 0.0
        
        # Try VADER first (better for financial text)
        if self.use_vader:
            return self._analyze_vader(text)
        
        # Fall back to TextBlob
        if self.use_textblob:
            return self._analyze_textblob(text)
        
        # Fall back to rule-based analysis
        return self._analyze_rule_based(text)
    
    def _analyze_vader(self, text: str) -> Tuple[SentimentLabel, float, float]:
        """Analyze using VADER (Valence Aware Dictionary and sEntiment Reasoner)."""
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores['compound']  # -1 to 1
            
            # Convert compound score to 0-1 range
            score = (compound + 1) / 2
            
            # Determine sentiment label
            if compound >= 0.05:
                sentiment = "POSITIVE"
                confidence = scores['pos']
            elif compound <= -0.05:
                sentiment = "NEGATIVE"
                confidence = scores['neg']
            else:
                sentiment = "NEUTRAL"
                confidence = scores['neu']
            
            return sentiment, score, confidence
        except Exception as e:
            logger.warning(f"VADER analysis failed: {e}")
            return "NEUTRAL", 0.5, 0.3
    
    def _analyze_textblob(self, text: str) -> Tuple[SentimentLabel, float, float]:
        """Analyze using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert polarity to 0-1 range
            score = (polarity + 1) / 2
            
            # More objective text (low subjectivity) = higher confidence
            confidence = 1.0 - subjectivity
            
            # Determine sentiment label
            if polarity > 0.1:
                sentiment = "POSITIVE"
            elif polarity < -0.1:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"
            
            return sentiment, score, confidence
        except Exception as e:
            logger.warning(f"TextBlob analysis failed: {e}")
            return "NEUTRAL", 0.5, 0.3
    
    def _analyze_rule_based(self, text: str) -> Tuple[SentimentLabel, float, float]:
        """
        Analyze using rule-based keywords (fallback method).
        
        This is basic but works well for financial news headlines.
        """
        text_lower = text.lower()
        
        # Count keyword matches
        positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
        neutral_count = sum(1 for word in NEUTRAL_KEYWORDS if word in text_lower)
        
        total_matches = positive_count + negative_count
        
        if total_matches == 0:
            # No keywords found - default to neutral
            return "NEUTRAL", 0.5, 0.1
        
        # Calculate score
        positive_ratio = positive_count / (positive_count + negative_count)
        
        # Map to 0-1 score
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            score = 0.5 + (positive_ratio / 2)  # 0.5 to 1.0
            confidence = positive_count / (positive_count + total_matches)
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            score = (1.0 - positive_ratio) / 2  # 0.0 to 0.5
            confidence = negative_count / (negative_count + total_matches)
        else:
            sentiment = "NEUTRAL"
            score = 0.5
            confidence = 0.3
        
        return sentiment, score, confidence


# ============================================
# Global Analyzer Instance
# ============================================
_analyzer = SentimentAnalyzer()


# ============================================
# Public API Functions
# ============================================
def analyze_article(title: str, summary: Optional[str] = None) -> ArticleSentiment:
    """
    Analyze sentiment of a news article.
    
    Args:
        title: Article title (primary text to analyze)
        summary: Article summary (secondary text to analyze)
    
    Returns:
        ArticleSentiment object with sentiment and confidence
    """
    # Combine title and summary for analysis
    text_to_analyze = title
    if summary:
        text_to_analyze = f"{title} {summary}"
    
    sentiment, score, confidence = _analyzer.analyze_text(text_to_analyze)
    
    return ArticleSentiment(
        title=title,
        source="",
        sentiment=sentiment,
        score=score,
        confidence=confidence,
    )


def analyze_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze sentiment for multiple articles.
    
    Args:
        articles: List of articles with 'title' and optional 'summary'
    
    Returns:
        List of articles with added 'sentiment' and 'sentiment_score' fields
    """
    analyzed = []
    
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        source = article.get("source", "")
        
        sentiment, score, confidence = _analyzer.analyze_text(f"{title} {summary}" if summary else title)
        
        # Add sentiment data to article
        article_with_sentiment = {
            **article,
            "sentiment": sentiment,
            "sentiment_score": round(score, 3),
            "sentiment_confidence": round(confidence, 3),
        }
        
        analyzed.append(article_with_sentiment)
    
    return analyzed


def generate_insight(articles: List[Dict[str, Any]]) -> SentimentInsight:
    """
    Generate investment insight from news articles.
    
    Logic:
    - Majority POSITIVE → BULLISH recommendation
    - Majority NEGATIVE → BEARISH recommendation
    - Mixed → NEUTRAL recommendation
    
    Args:
        articles: List of articles (should already have sentiment analysis)
    
    Returns:
        SentimentInsight with recommendation and confidence
    """
    if not articles:
        return SentimentInsight(
            sentiment_score=0.5,
            sentiment_label="NEUTRAL",
            recommendation="No news available for analysis",
            confidence=0.0,
            analysis_count=0,
        )
    
    # Count sentiments
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0.0
    
    for article in articles:
        sentiment = article.get("sentiment", "NEUTRAL")
        score = article.get("sentiment_score", 0.5)
        
        if sentiment == "POSITIVE":
            positive_count += 1
        elif sentiment == "NEGATIVE":
            negative_count += 1
        else:
            neutral_count += 1
        
        total_score += score
    
    count = len(articles)
    
    # Calculate overall metrics
    average_score = total_score / count
    positive_ratio = positive_count / count
    negative_ratio = negative_count / count
    
    # Determine recommendation
    if positive_ratio > 0.6:
        recommendation_label = "BULLISH"
        recommendation_text = (
            f"Strong positive sentiment. {positive_count} out of {count} articles are positive. "
            "This could be a good opportunity to consider buying, but always do your own research."
        )
        confidence = positive_ratio
    elif negative_ratio > 0.6:
        recommendation_label = "BEARISH"
        recommendation_text = (
            f"Strong negative sentiment. {negative_count} out of {count} articles are negative. "
            "High risk alert - be cautious before investing."
        )
        confidence = negative_ratio
    elif positive_ratio > negative_ratio:
        recommendation_label = "BULLISH"
        recommendation_text = (
            f"Slightly positive sentiment. {positive_count} positive vs {negative_count} negative articles. "
            "Cautiously bullish - monitor the situation."
        )
        confidence = positive_ratio * 0.8  # Lower confidence for mixed signals
    elif negative_ratio > positive_ratio:
        recommendation_label = "BEARISH"
        recommendation_text = (
            f"Slightly negative sentiment. {negative_count} negative vs {positive_count} positive articles. "
            "Mixed signals with bearish lean - exercise caution."
        )
        confidence = negative_ratio * 0.8  # Lower confidence for mixed signals
    else:
        recommendation_label = "NEUTRAL"
        recommendation_text = (
            f"Mixed sentiment. {positive_count} positive, {negative_count} negative, {neutral_count} neutral. "
            "Wait and watch - no clear direction yet."
        )
        confidence = 0.5
    
    return SentimentInsight(
        sentiment_score=round(average_score, 3),
        sentiment_label=recommendation_label,
        recommendation=recommendation_text,
        confidence=round(confidence, 3),
        analysis_count=count,
    )


def get_sentiment_summary(
    articles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Get complete sentiment analysis summary for articles.
    
    Args:
        articles: List of news articles
    
    Returns:
        Dictionary with sentiment analysis and insights
    """
    # Analyze articles
    analyzed_articles = analyze_articles(articles)
    
    # Generate insight
    insight = generate_insight(analyzed_articles)
    
    return {
        "articles": analyzed_articles,
        "sentiment_score": insight.sentiment_score,
        "sentiment_label": insight.sentiment_label,
        "recommendation": insight.recommendation,
        "confidence": insight.confidence,
        "analysis_count": insight.analysis_count,
    }
