from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "stock_id", name="uq_watchlist_stock"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    watchlist_id: int = Column(
        Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False
    )
    stock_id: int = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    added_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")

