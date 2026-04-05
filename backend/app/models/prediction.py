from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feature_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    actual_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_return: Mapped[float | None] = mapped_column(Float, nullable=True)
