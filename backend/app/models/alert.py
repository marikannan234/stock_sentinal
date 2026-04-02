"""
SQLAlchemy Alert model for Stock Sentinel.

Represents user alerts for stock price conditions.
Uses SQLAlchemy 2.0 style with proper typing.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Index, String, UniqueConstraint
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
    CUSTOM = "custom"                         # Custom rule (placeholder)


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
    )
    
    # ============================================================================
    # PRIMARY KEY
    # ============================================================================
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
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
        SQLEnum(AlertCondition),
        nullable=True,  # Allow NULL for non-PRICE alert types
        default=None
    )
    
    target_value: Mapped[float] = mapped_column(
        nullable=False
    )
    
    # ============================================================================
    # ALERT CONFIGURATION - NEW FIELDS FOR ADVANCED ALERTS
    # ============================================================================
    
    alert_type: Mapped[AlertType] = mapped_column(
        SQLEnum(AlertType),
        nullable=False,
        default=AlertType.PRICE,
        index=True  # Index for alert type filtering
    )
    
    last_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Used to track previous price for percentage change and crash detection
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
        # Tracks if alert has been triggered; reset when condition becomes false (re-arm logic)
    )
    
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
        # Used for cooldown mechanism - prevents alert from triggering too frequently
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
    
    def matches_condition(
        self,
        current_price: float,
        previous_price: Optional[float] = None
    ) -> bool:
        """
        Check if current price matches the alert condition.
        
        Args:
            current_price: Current stock price
            previous_price: Previous stock price (required for percentage_change)
            
        Returns:
            True if condition is met, False otherwise
            
        Raises:
            ValueError: If condition type is invalid or previous_price missing for percentage_change
        """
        if self.condition == AlertCondition.GREATER_THAN:
            return current_price > self.target_value
        elif self.condition == AlertCondition.LESS_THAN:
            return current_price < self.target_value
        elif self.condition == AlertCondition.GREATER_THAN_OR_EQUAL:
            return current_price >= self.target_value
        elif self.condition == AlertCondition.LESS_THAN_OR_EQUAL:
            return current_price <= self.target_value
        elif self.condition == AlertCondition.PERCENTAGE_CHANGE:
            if previous_price is None or previous_price == 0:
                raise ValueError(
                    f"previous_price required for percentage_change condition, "
                    f"got {previous_price}"
                )
            percentage_change = ((current_price - previous_price) / previous_price) * 100
            return abs(percentage_change) >= self.target_value
        else:
            raise ValueError(f"Unknown condition: {self.condition}")
    
    def check_price_alert(self, current_price: float) -> bool:
        """
        Check simple price threshold alert.
        
        Args:
            current_price: Current stock price
            
        Returns:
            True if price meets condition
        """
        return self.matches_condition(current_price)
    
    def check_percentage_change_alert(self, current_price: float) -> bool:
        """
        Check percentage change alert.
        
        Compares current price against last_price.
        Triggers if percentage change exceeds target_value.
        
        Args:
            current_price: Current stock price
            
        Returns:
            True if percentage change exceeds threshold
        """
        if self.last_price is None or self.last_price == 0:
            return False
        
        percentage_change = abs(((current_price - self.last_price) / self.last_price) * 100)
        return percentage_change >= self.target_value
    
    def check_volume_spike_alert(self, current_volume: float, avg_volume: float) -> bool:
        """
        Check volume spike alert.
        
        Triggers if current volume exceeds (avg_volume * target_value).
        target_value should be a multiplier (e.g., 1.5 for 150% of average).
        
        Args:
            current_volume: Current trading volume
            avg_volume: Average trading volume
            
        Returns:
            True if volume spike detected
        """
        if avg_volume == 0:
            return False
        
        threshold_volume = avg_volume * self.target_value
        return current_volume > threshold_volume
    
    def check_crash_alert(self, current_price: float) -> bool:
        """
        Check crash alert - percentage drop detection.
        
        Triggers if percentage drop exceeds target_value (as negative threshold).
        target_value should be positive (e.g., 5.0 for 5% drop).
        
        Args:
            current_price: Current stock price
            
        Returns:
            True if price drop exceeds threshold
        """
        if self.last_price is None or self.last_price == 0:
            return False
        
        percentage_change = ((current_price - self.last_price) / self.last_price) * 100
        return percentage_change <= -(self.target_value)
    
    def check_custom_alert(self, current_price: float) -> bool:
        """
        Check custom alert - basic implementation.
        
        Currently delegates to price threshold check.
        Can be extended with more complex logic.
        
        Args:
            current_price: Current stock price
            
        Returns:
            True if custom condition met
        """
        return self.matches_condition(current_price)
    
    def check_alert(self, current_price: float, avg_volume: Optional[float] = None, current_volume: Optional[float] = None) -> bool:
        """
        Check alert based on its type.
        
        Dispatches to appropriate check method based on alert_type.
        
        Args:
            current_price: Current stock price
            avg_volume: Average volume (required for volume_spike)
            current_volume: Current volume (required for volume_spike)
            
        Returns:
            True if alert condition is met
        """
        if self.alert_type == AlertType.PRICE:
            return self.check_price_alert(current_price)
        elif self.alert_type == AlertType.PERCENTAGE_CHANGE:
            return self.check_percentage_change_alert(current_price)
        elif self.alert_type == AlertType.VOLUME_SPIKE:
            if avg_volume is None or current_volume is None:
                return False
            return self.check_volume_spike_alert(current_volume, avg_volume)
        elif self.alert_type == AlertType.CRASH:
            return self.check_crash_alert(current_price)
        elif self.alert_type == AlertType.CUSTOM:
            return self.check_custom_alert(current_price)
        else:
            return False


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
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
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
        SQLEnum(AlertType),
        nullable=False
    )
    
    price_at_trigger: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
        # Stock price when alert was triggered
    )
    
    target_value: Mapped[float] = mapped_column(
        Float,
        nullable=False
        # Target value that triggered the alert
    )
    
    condition: Mapped[Optional[AlertCondition]] = mapped_column(
        SQLEnum(AlertCondition),
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
