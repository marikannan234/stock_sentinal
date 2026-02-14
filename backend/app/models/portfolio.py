from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.db.session import Base


class Portfolio(Base):
    """One row per (user, ticker). User's stock holdings with quantity and average price."""

    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_portfolio_user_ticker"),)

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: str = Column(String(16), nullable=False, index=True)
    quantity: float = Column(Float, nullable=False)
    average_price: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
