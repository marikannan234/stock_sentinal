from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class Portfolio(Base):
    """One row per (user, ticker). User's stock holdings with quantity and average price."""

    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_portfolio_user_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # Derived from the user's open trades (see app.services.trading_service).
    # Positive = long, negative = short.
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="portfolios")
