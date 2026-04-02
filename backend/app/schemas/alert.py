"""
Pydantic schemas for Alert endpoints.

Provides request/response models with validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.models.alert import AlertCondition, AlertType


class AlertBase(BaseModel):
    """Base alert schema - Pydantic v2 with proper optional field handling."""
    
    # Configuration for Pydantic v2
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
    
    stock_symbol: str = Field(..., min_length=1, max_length=16, description="Stock ticker symbol (e.g., AAPL)")
    # PYDANTIC V2 FIX: Simple Optional with default None - no field_validator to avoid required flag
    condition: Optional[AlertCondition] = None
    target_value: float = Field(..., gt=0, description="Target value (price or multiplier depending on alert type)")
    alert_type: AlertType = Field(default=AlertType.PRICE, description="Type of alert (price, percentage_change, volume_spike, crash, custom)")
    
    @field_validator("stock_symbol", mode="before")
    @classmethod
    def validate_stock_symbol(cls, v: str) -> str:
        """Ensure stock symbol is uppercase."""
        if not isinstance(v, str):
            raise ValueError("stock_symbol must be a string")
        v = v.strip().upper()
        if not v:
            raise ValueError("stock_symbol cannot be empty")
        return v
    
    @field_validator("target_value", mode="before")
    @classmethod
    def validate_target_value(cls, v: float) -> float:
        """Ensure target value is positive."""
        if not isinstance(v, (int, float)):
            raise ValueError("target_value must be a number")
        if v <= 0:
            raise ValueError("target_value must be greater than 0")
        return float(v)
    
    @field_validator("alert_type", mode="before")
    @classmethod
    def validate_alert_type(cls, v):
        """Normalize alert_type enum value (case-insensitive)."""
        if isinstance(v, AlertType):
            return v
        if isinstance(v, str):
            v = v.strip()
            # Try exact match first
            try:
                return AlertType(v)
            except ValueError:
                pass
            # Try case-insensitive match
            for alert_type in AlertType:
                if alert_type.value.lower() == v.lower():
                    return alert_type
            # Provide helpful error message
            valid_values = [t.value for t in AlertType]
            raise ValueError(f"Invalid alert_type '{v}'. Must be one of: {', '.join(valid_values)}")
        if v is None:
            return AlertType.PRICE
        raise ValueError(f"alert_type must be a string or null, got {type(v).__name__}")
    
    @model_validator(mode="after")
    def validate_condition_requirement_and_normalize(self):
        """
        Normalize and validate condition:
        1. Convert string condition to AlertCondition enum if needed
        2. Require condition only for PRICE alerts
        """
        # Normalize condition from string to enum if needed
        if isinstance(self.condition, str):
            v = self.condition.strip()
            # Try exact match first
            try:
                condition = AlertCondition(v)
            except ValueError:
                # Try case-insensitive match
                found = False
                condition = None
                for cond in AlertCondition:
                    if cond.value.lower() == v.lower():
                        condition = cond
                        found = True
                        break
                if not found:
                    valid_values = [c.value for c in AlertCondition]
                    raise ValueError(f"Invalid condition '{v}'. Must be one of: {', '.join(valid_values)}")
            # Use object.__setattr__ to bypass validation
            object.__setattr__(self, 'condition', condition)
        
        # PRICE alerts MUST have a condition
        if self.alert_type == AlertType.PRICE and self.condition is None:
            raise ValueError("'condition' field is REQUIRED for PRICE alerts (must be one of: >, <, >=, <=)")
        
        # Other alert types don't need condition (it's optional)
        # PERCENTAGE_CHANGE: uses percentage value in target_value
        # VOLUME_SPIKE: no condition needed (automatic detection)
        # CRASH: no condition needed (automatic detection)
        # CUSTOM: condition is optional (user-defined)
        
        return self


class CreateAlertRequest(AlertBase):
    """
    Request schema for creating a new alert.
    
    Example:
        {
            "stock_symbol": "AAPL",
            "condition": ">",
            "target_value": 150.50
        }
    """
    pass


class UpdateAlertRequest(BaseModel):
    """
    Request schema for updating an alert.
    
    Only supports toggling active status.
    """
    
    is_active: bool = Field(..., description="Whether the alert is active")


class AlertResponse(AlertBase):
    """
    Response schema for alert data.
    
    Includes all alert fields with metadata.
    """
    
    id: int = Field(..., description="Alert unique identifier")
    user_id: int = Field(..., description="User ID who owns this alert")
    is_active: bool = Field(..., description="Whether alert is currently active")
    created_at: datetime = Field(..., description="When the alert was created")
    triggered_at: Optional[datetime] = Field(None, description="When the alert was last triggered (if any)")
    last_price: Optional[float] = Field(None, description="Last recorded price (used for percentage change tracking)")
    
    class Config:
        from_attributes = True
        use_enum_values = False  # Keep enum objects, don't convert to strings
    
    def __repr__(self) -> str:
        return f"<AlertResponse(id={self.id}, symbol={self.stock_symbol}, condition={self.condition}, value={self.target_value}, active={self.is_active})>"


class AlertTriggeredResponse(BaseModel):
    """
    Response schema when an alert is triggered.
    
    Includes alert info and the price that triggered it.
    """
    
    alert_id: int = Field(..., description="ID of the triggered alert")
    stock_symbol: str = Field(..., description="Stock symbol")
    current_price: float = Field(..., description="Current stock price")
    condition: AlertCondition = Field(..., description="Condition that was met")
    target_value: float = Field(..., description="Target value from alert")
    triggered_at: datetime = Field(..., description="When the alert was triggered")
    
    class Config:
        from_attributes = True
