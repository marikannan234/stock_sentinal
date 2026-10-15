"""
SQLAlchemy Alert model for Stock Sentinel.

Represents user alerts for stock price conditions.
Uses SQLAlchemy 2.0 style with proper typing.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SQLEnum, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class AlertCondition(str, Enum):
    """Alert condition operators."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    PERCENTAGE_CHANGE = "percentage_change"


class AlertType(str, Enum):
    """Alert type for different monitoring strategies."""
    PRICE = "price"                           # Simple price threshold
    PERCENTAGE_CHANGE = "percentage_change"   # Percentage change from last price
    VOLUME_SPIKE = "volume_spike"             # Volume exceeds threshold
    CRASH = "crash"                           # Sudden price drop detection
    SMA_ABOVE = "sma_above"                   # Price above SMA
    SMA_BELOW = "sma_below"                   # Price below SMA
    SMA_CROSSOVER = "sma_crossover"           # Price crosses SMA
    EMA_ABOVE = "ema_above"                   # Price above EMA
    EMA_BELOW = "ema_below"                   # Price below EMA
    EMA_CROSSOVER = "ema_crossover"           # Price crosses EMA
    RSI_OVERBOUGHT = "rsi_overbought"         # RSI > 70
    RSI_OVERSOLD = "rsi_oversold"             # RSI < 30
    RSI_CROSSOVER = "rsi_crossover"           # RSI crosses 30/70 thresholds
    STRONG_BUY_SIGNAL = "strong_buy_signal"   # Combined: Price > SMA, Price > EMA, RSI < 30
    STRONG_SELL_SIGNAL = "strong_sell_signal" # Combined: Price < SMA, Price < EMA, RSI > 70
    CUSTOM = "custom"                         # Custom rule (placeholder)


# Which fields each alert type needs. Used by the API schema (validation) and
# by the database CHECK constraint below, so the two cannot disagree.
PRICE_RULE_TYPES = frozenset({AlertType.PRICE, AlertType.CUSTOM})  # condition + target price
THRESHOLD_TYPES = frozenset({
    AlertType.PRICE,
    AlertType.CUSTOM,
    AlertType.PERCENTAGE_CHANGE,  # target_value = percent move
    AlertType.VOLUME_SPIKE,       # target_value = multiple of average volume
    AlertType.CRASH,              # target_value = percent drop
})
COMBINED_TYPES = frozenset({AlertType.STRONG_BUY_SIGNAL, AlertType.STRONG_SELL_SIGNAL})
SMA_TYPES = frozenset({AlertType.SMA_ABOVE, AlertType.SMA_BELOW, AlertType.SMA_CROSSOVER}) | COMBINED_TYPES
EMA_TYPES = frozenset({AlertType.EMA_ABOVE, AlertType.EMA_BELOW, AlertType.EMA_CROSSOVER}) | COMBINED_TYPES
RSI_TYPES = frozenset({AlertType.RSI_OVERBOUGHT, AlertType.RSI_OVERSOLD, AlertType.RSI_CROSSOVER}) | COMBINED_TYPES
PRICE_COMPARISON_CONDITIONS = frozenset({
    AlertCondition.GREATER_THAN,
    AlertCondition.LESS_THAN,
    AlertCondition.GREATER_THAN_OR_EQUAL,
    AlertCondition.LESS_THAN_OR_EQUAL,
})


def _requires(column: str, types: frozenset) -> str:
    names = ", ".join(f"'{t.name}'" for t in sorted(types, key=lambda t: t.name))
    return f"(alert_type NOT IN ({names}) OR {column} IS NOT NULL)"


ALERT_PARAMETERS_CHECK = " AND ".join([
    _requires("target_value", THRESHOLD_TYPES),
    _requires("condition", PRICE_RULE_TYPES),
    _requires("sma_period", SMA_TYPES),
    _requires("ema_period", EMA_TYPES),
    _requires("rsi_period", RSI_TYPES),
])


def _varchar_enum(enum_class) -> SQLEnum:
    # The columns are VARCHAR(50) in the database (migration 0001), not native
    # PostgreSQL enum types; values are stored by enum name.
    return SQLEnum(enum_class, native_enum=False, length=50)


class Alert(Base):
    """
    Alert model for stock price monitoring.
    
    Represents a user's alert configuration for a specific stock.
    Tracks when the condition is triggered.
    
    Proper indexing strategy:
    - Single column indexes defined via index=True in mapped_column()
    - Composite indexes defined in __table_args__
    - No duplicate index definitions
    """
    
    __tablename__ = "alerts"
    
    # Define all constraints and composite indexes in __table_args__
    # Do NOT re-index columns already indexed via mapped_column(index=True)
    __table_args__ = (
        # Unique constraint: prevent duplicate alerts for same user/stock/alert_type/condition/value
        UniqueConstraint(
            "user_id", "stock_symbol", "alert_type", "condition", "target_value",
            name="uq_alerts_user_stock_type_condition"
        ),
        # Composite indexes for common query patterns (user + active status)
        Index("ix_alerts_user_id_active", "user_id", "is_active"),
        # Composite index for finding alerts by user and stock
        Index("ix_alerts_user_stock", "user_id", "stock_symbol"),
        # Index for alert type filtering
        Index("ix_alerts_alert_type", "alert_type"),
        # Each alert type must carry the parameters it is evaluated with
        CheckConstraint(ALERT_PARAMETERS_CHECK, name="ck_alerts_type_parameters"),
    )
    
    # ============================================================================
    # PRIMARY KEY
    # ============================================================================
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ============================================================================
    # FOREIGN KEYS
    # ============================================================================
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Single column index
    )
    
    # ============================================================================
    # ALERT CONFIGURATION
    # ============================================================================
    stock_symbol: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        # NOTE: NOT indexed here because we want to avoid implicit index name conflicts
        # Instead, composite index via __table_args__ is used for multi-column queries
        # If you need a single-column index on stock_symbol, uncomment below:
        # index=True
    )
    
    condition: Mapped[Optional[AlertCondition]] = mapped_column(
        _varchar_enum(AlertCondition),
        nullable=True,  # Only PRICE and CUSTOM alerts use a condition
        default=None
    )
    
    # Required for THRESHOLD_TYPES; indicator alerts are defined by their
    # periods instead (enforced by ck_alerts_type_parameters).
    target_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # ============================================================================
    # ALERT CONFIGURATION - NEW FIELDS FOR ADVANCED ALERTS
    # ============================================================================
    
    alert_type: Mapped[AlertType] = mapped_column(
        _varchar_enum(AlertType),
        nullable=False,
        default=AlertType.PRICE,
        # Indexed by ix_alerts_alert_type in __table_args__; index=True here
        # would declare a second index with the same name.
    )
    
    last_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # PERCENTAGE_CHANGE / CRASH: reference price recorded when the alert
        #   was armed (first check after creation or re-enable).
        # SMA_CROSSOVER / EMA_CROSSOVER: price at the previous check.
    )
    
    sma_period: Mapped[Optional[int]] = mapped_column(
        nullable=True
        # SMA period in days for SMA-based alerts (SMA_ABOVE, SMA_BELOW, SMA_CROSSOVER)
        # Must be provided for SMA alert types, ignored for others
    )
    
    ema_period: Mapped[Optional[int]] = mapped_column(
        nullable=True
        # EMA period in days for EMA-based alerts (EMA_ABOVE, EMA_BELOW, EMA_CROSSOVER)
        # Also required for combined signal alerts (STRONG_BUY_SIGNAL, STRONG_SELL_SIGNAL)
    )
    
    last_ema: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Used to track previous EMA for EMA crossover detection
    )
    
    rsi_period: Mapped[Optional[int]] = mapped_column(
        nullable=True
        # RSI period in days for RSI-based alerts (RSI_OVERBOUGHT, RSI_OVERSOLD, RSI_CROSSOVER)
        # Also required for combined signal alerts (STRONG_BUY_SIGNAL, STRONG_SELL_SIGNAL)
        # Must be provided for RSI alert types, ignored for others
    )
    
    last_rsi: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Used to track previous RSI for RSI crossover detection
    )
    
    # ============================================================================
    # ALERT STATUS
    # ============================================================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
        # NOTE: is_active is indexed in composite index via __table_args__
        # Single column index created implicitly by composite index usage
    )
    
    is_triggered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True  # Index for efficient filtering of triggered alerts
        # True once the alert has fired. Alerts are one-shot: firing also sets
        # is_active=False; re-enabling the alert clears this flag.
    )
    
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
        # When the alert last fired
    )
    
    # ============================================================================
    # TIMESTAMPS
    # ============================================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True  # Single column index for time-based queries
    )
    
    triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
        # Not indexed - triggered_at is sparse (many NULLs)
    )
    
    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    user: Mapped["User"] = relationship(
        "User",
        back_populates="alerts"
    )
    
    # ============================================================================
    # METHODS
    # ============================================================================
    
    def __repr__(self) -> str:
        return (
            f"<Alert("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"symbol={self.stock_symbol}, "
            f"type={self.alert_type.value}, "
            f"condition={self.condition}, "
            f"target={self.target_value}"
            f")>"
        )


class AlertHistory(Base):
    """
    Alert history/audit trail for tracking when alerts are triggered.
    
    Stores a record every time an alert triggers, including:
    - When it triggered
    - Stock price at triggering time
    - Triggering message/details
    
    Enables:
    - Alert audit trail
    - Alert frequency analysis
    - Debugging alert behavior
    - User notifications history
    """
    
    __tablename__ = "alert_history"
    
    __table_args__ = (
        Index("ix_alert_history_alert_id", "alert_id"),
        Index("ix_alert_history_user_id", "user_id"),
        Index("ix_alert_history_triggered_at", "triggered_at"),
        Index("ix_alert_history_alert_user", "alert_id", "user_id"),
    )
    
    # ============================================================================
    # PRIMARY KEY
    # ============================================================================
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ============================================================================
    # FOREIGN KEYS
    # ============================================================================
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False
        # Index defined in __table_args__ to avoid duplication
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
        # Index defined in __table_args__ to avoid duplication
    )
    
    # ============================================================================
    # TRIGGER DETAILS
    # ============================================================================
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
        # Index defined in __table_args__ to avoid duplication
    )
    
    stock_symbol: Mapped[str] = mapped_column(
        String(16),
        nullable=False
    )
    
    alert_type: Mapped[AlertType] = mapped_column(
        _varchar_enum(AlertType),
        nullable=False
    )
    
    price_at_trigger: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Stock price when alert was triggered
    )
    
    target_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Alert's target value (NULL for indicator alerts)
    )
    
    condition: Mapped[Optional[AlertCondition]] = mapped_column(
        _varchar_enum(AlertCondition),
        nullable=True
    )
    
    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False
        # Human-readable message describing the trigger (e.g., "AAPL price > $150")
    )
    
    email_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
        # Whether email notification was sent for this trigger
    )
    
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
        # When email was sent (NULL if email_sent=False)
    )
    
    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    alert: Mapped["Alert"] = relationship(
        "Alert",
        foreign_keys=[alert_id],
        lazy="joined"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined"
    )
    
    # ============================================================================
    # METHODS
    # ============================================================================
    
    def __repr__(self) -> str:
        return (
            f"<AlertHistory("
            f"id={self.id}, "
            f"alert_id={self.alert_id}, "
            f"symbol={self.stock_symbol}, "
            f"price={self.price_at_trigger}, "
            f"triggered_at={self.triggered_at}"
            f")>"
        )
