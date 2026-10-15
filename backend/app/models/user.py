from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.portfolio import Portfolio
    from app.models.trading import SupportTicket, Trade, TradeHistory, UserSettings


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="users_email_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp_phone: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Paper-trading cash. Only app.services.trading_service changes it.
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=lambda: settings.PAPER_TRADING_STARTING_CASH,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    portfolios: Mapped[list["Portfolio"]] = relationship(
        "Portfolio",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    settings: Mapped["UserSettings | None"] = relationship(
        "UserSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    support_tickets: Mapped[list["SupportTicket"]] = relationship(
        "SupportTicket",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    trade_history: Mapped[list["TradeHistory"]] = relationship(
        "TradeHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
