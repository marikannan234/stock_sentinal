from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.db.session import Base


class Stock(Base):
    __tablename__ = "stocks"
    __table_args__ = (UniqueConstraint("ticker", name="uq_stocks_ticker"),)

    id: int = Column(Integer, primary_key=True, index=True)
    ticker: str = Column(String(16), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    exchange: str = Column(String(64), nullable=True)
    sector: str = Column(String(128), nullable=True)
    currency: str = Column(String(8), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

