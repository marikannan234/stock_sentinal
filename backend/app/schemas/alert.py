"""
Pydantic schemas for Alert endpoints.

Validation is type-specific. Each alert type requires exactly the parameters it
is evaluated with (see the requirement sets in app.models.alert, which also
drive the database CHECK constraint). Parameters a type does not use are
ignored and stored as NULL, so existing clients that always send e.g.
`target_value` keep working.

| alert_type                              | required                                   |
|-----------------------------------------|--------------------------------------------|
| price, custom                           | condition (>, <, >=, <=), target_value > 0 |
| percentage_change                       | target_value: percent move, 0 < x <= 1000  |
| crash                                   | target_value: percent drop, 0 < x < 100    |
| volume_spike                            | target_value: volume multiple, x >= 1      |
| sma_above / sma_below / sma_crossover   | sma_period 2-500                           |
| ema_above / ema_below / ema_crossover   | ema_period 2-500                           |
| rsi_overbought / rsi_oversold / rsi_crossover | rsi_period 2-100                     |
| strong_buy_signal / strong_sell_signal  | sma_period, ema_period, rsi_period         |
"""

import math
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.alert import (
    EMA_TYPES,
    PRICE_COMPARISON_CONDITIONS,
    PRICE_RULE_TYPES,
    RSI_TYPES,
    SMA_TYPES,
    THRESHOLD_TYPES,
    AlertCondition,
    AlertType,
)

MAX_SMA_PERIOD = 500
MAX_EMA_PERIOD = 500
MAX_RSI_PERIOD = 100


def _parse_enum(enum_class, value, field_name: str):
    """Accept enum members or their values, case-insensitively."""
    if value is None or isinstance(value, enum_class):
        return value
    if isinstance(value, str):
        text = value.strip()
        for member in enum_class:
            if member.value.lower() == text.lower():
                return member
    valid = ", ".join(member.value for member in enum_class)
    raise ValueError(f"Invalid {field_name} {value!r}. Must be one of: {valid}")


class CreateAlertRequest(BaseModel):
    """
    Request schema for creating an alert.

    Examples:
        {"stock_symbol": "AAPL", "alert_type": "price", "condition": ">", "target_value": 150.5}
        {"stock_symbol": "AAPL", "alert_type": "sma_crossover", "sma_period": 50}
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    stock_symbol: str = Field(..., min_length=1, max_length=16, description="Stock ticker symbol (e.g., AAPL)")
    alert_type: AlertType = Field(default=AlertType.PRICE, description="Alert type (see module docstring)")
    condition: Optional[AlertCondition] = Field(default=None, description="Price comparison for price/custom alerts")
    target_value: Optional[float] = Field(default=None, gt=0, description="Threshold; meaning depends on alert_type")
    sma_period: Optional[int] = Field(default=None, ge=2, le=MAX_SMA_PERIOD, description="SMA period in trading days")
    ema_period: Optional[int] = Field(default=None, ge=2, le=MAX_EMA_PERIOD, description="EMA period in trading days")
    rsi_period: Optional[int] = Field(default=None, ge=2, le=MAX_RSI_PERIOD, description="RSI period in trading days")

    @field_validator("stock_symbol", mode="before")
    @classmethod
    def _normalize_symbol(cls, value):
        if not isinstance(value, str):
            raise ValueError("stock_symbol must be a string")
        value = value.strip().upper()
        if not value:
            raise ValueError("stock_symbol cannot be empty")
        return value

    @field_validator("alert_type", mode="before")
    @classmethod
    def _parse_alert_type(cls, value):
        return AlertType.PRICE if value is None else _parse_enum(AlertType, value, "alert_type")

    @field_validator("condition", mode="before")
    @classmethod
    def _parse_condition(cls, value):
        return _parse_enum(AlertCondition, value, "condition")

    @field_validator("target_value")
    @classmethod
    def _finite_target(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("target_value must be a finite number")
        return value

    @model_validator(mode="after")
    def _validate_for_alert_type(self) -> "CreateAlertRequest":
        alert_type = self.alert_type
        label = alert_type.value

        # Drop parameters this alert type does not use.
        if alert_type not in PRICE_RULE_TYPES:
            self.condition = None
        if alert_type not in THRESHOLD_TYPES:
            self.target_value = None
        if alert_type not in SMA_TYPES:
            self.sma_period = None
        if alert_type not in EMA_TYPES:
            self.ema_period = None
        if alert_type not in RSI_TYPES:
            self.rsi_period = None

        if alert_type in PRICE_RULE_TYPES:
            if self.condition is None:
                raise ValueError(f"'condition' is required for {label} alerts (one of >, <, >=, <=)")
            if self.condition not in PRICE_COMPARISON_CONDITIONS:
                raise ValueError(f"'condition' for {label} alerts must be one of >, <, >=, <=")

        if alert_type in THRESHOLD_TYPES and self.target_value is None:
            raise ValueError(f"'target_value' is required for {label} alerts")
        if alert_type == AlertType.PERCENTAGE_CHANGE and self.target_value > 1000:
            raise ValueError("'target_value' for percentage_change is a percent and must be at most 1000")
        if alert_type == AlertType.CRASH and self.target_value >= 100:
            raise ValueError("'target_value' for crash is a percent drop and must be below 100")
        if alert_type == AlertType.VOLUME_SPIKE and self.target_value < 1:
            raise ValueError("'target_value' for volume_spike is a multiple of average volume and must be at least 1")

        for field, types, maximum in (
            ("sma_period", SMA_TYPES, MAX_SMA_PERIOD),
            ("ema_period", EMA_TYPES, MAX_EMA_PERIOD),
            ("rsi_period", RSI_TYPES, MAX_RSI_PERIOD),
        ):
            if alert_type in types and getattr(self, field) is None:
                raise ValueError(f"'{field}' is required for {label} alerts (2-{maximum})")

        return self


class UpdateAlertRequest(BaseModel):
    """Enable or disable an alert. Re-enabling a fired alert re-arms it."""

    is_active: bool = Field(..., description="Whether the alert is active")


class AlertResponse(BaseModel):
    """Alert as returned by the API. Not re-validated against creation rules."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Alert unique identifier")
    user_id: int = Field(..., description="User ID who owns this alert")
    stock_symbol: str
    alert_type: AlertType
    condition: Optional[AlertCondition] = None
    target_value: Optional[float] = None
    sma_period: Optional[int] = None
    ema_period: Optional[int] = None
    rsi_period: Optional[int] = None
    is_active: bool = Field(..., description="Whether the alert is being checked")
    is_triggered: bool = Field(False, description="Whether the alert has fired (alerts fire once, then deactivate)")
    created_at: datetime = Field(..., description="When the alert was created")
    triggered_at: Optional[datetime] = Field(None, description="When the alert last fired")
    last_price: Optional[float] = Field(None, description="Reference price (percent/crash) or previous price (crossovers)")
