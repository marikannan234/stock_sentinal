from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.db.session import Base


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id: int = Column(Integer, primary_key=True, index=True)
    stock_id: int = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)

    generated_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    horizon_days: int = Column(Integer, nullable=False)
    target_date: datetime = Column(DateTime, nullable=False)

    predicted_price: float = Column(Float, nullable=False)
    predicted_return: float = Column(Float, nullable=True)
    confidence: float = Column(Float, nullable=True)

    model_version: str = Column(String(64), nullable=True)
    feature_snapshot: dict | None = Column(JSONB, nullable=True)

    actual_price: float | None = Column(Float, nullable=True)
    actual_return: float | None = Column(Float, nullable=True)

