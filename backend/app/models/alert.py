"""
SQLAlchemy Alert model for Stock Sentinel.

Represents user alerts for stock price conditions.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.db.session import Base


class AlertCondition(str, Enum):
    """Alert condition operators."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    PERCENTAGE_CHANGE = "percentage_change"


class Alert(Base):
    """
    Alert model for stock price monitoring.
    
    Represents a user's alert configuration for a specific stock.
    Tracks when the condition is triggered.
    """
    
    __tablename__ = "alerts"
    
    # Composite unique constraint to prevent duplicate alerts
    __table_args__ = (
        UniqueConstraint("user_id", "stock_symbol", "condition", "target_value", 
                        name="uq_alerts_user_stock_condition"),
        Index("ix_alerts_user_id_active", "user_id", "is_active"),
        Index("ix_alerts_stock_symbol", "stock_symbol"),
        Index("ix_alerts_user_stock", "user_id", "stock_symbol"),
    )
    
    # Primary Key
    id: int = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert Configuration
    stock_symbol: str = Column(String(16), nullable=False, index=True)
    condition: AlertCondition = Column(
        SQLEnum(AlertCondition),
        nullable=False,
        default=AlertCondition.GREATER_THAN
    )
    target_value: float = Column(Float, nullable=False)
    
    # Alert Status
    is_active: bool = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    triggered_at: Optional[datetime] = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, user_id={self.user_id}, symbol={self.stock_symbol}, condition={self.condition}, target={self.target_value})>"
    
    def matches_condition(self, current_price: float, previous_price: Optional[float] = None) -> bool:
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
                raise ValueError(f"previous_price required for percentage_change condition, got {previous_price}")
            percentage_change = ((current_price - previous_price) / previous_price) * 100
            return abs(percentage_change) >= self.target_value
        else:
            raise ValueError(f"Unknown condition: {self.condition}")
