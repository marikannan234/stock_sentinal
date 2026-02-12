from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: str = Column(String(255), nullable=False)
    base_currency: str = Column(String(8), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    positions = relationship(
        "PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan"
    )


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "stock_id", name="uq_portfolio_stock"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    portfolio_id: int = Column(
        Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: int = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)

    quantity: float = Column(Float, nullable=False)
    average_price: float = Column(Float, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    portfolio = relationship("Portfolio", back_populates="positions")

