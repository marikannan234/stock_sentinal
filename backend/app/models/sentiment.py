from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.db.session import Base


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id: int = Column(Integer, primary_key=True, index=True)
    stock_id: int = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    source: str = Column(String(32), nullable=False)  # e.g. twitter, news, reddit
    window_start: datetime = Column(DateTime, nullable=False)
    window_end: datetime = Column(DateTime, nullable=False)
    sentiment_score: float = Column(Float, nullable=False)  # -1..1
    confidence: float = Column(Float, nullable=True)  # 0..1
    mentions_count: int = Column(Integer, nullable=True)
    raw_sample_count: int = Column(Integer, nullable=True)
    extra_data: dict | None = Column(JSONB, nullable=True)  # extra info
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

