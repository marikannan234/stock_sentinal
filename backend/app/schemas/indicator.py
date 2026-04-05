"""
Technical Indicators API Schemas

Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field


# ============================================================================
# Response Schemas
# ============================================================================

class SMAResponse(BaseModel):
    """Response schema for SMA calculation result"""
    
    symbol: str = Field(description="Stock symbol")
    period: int = Field(description="SMA period in days")
    sma: float = Field(description="Simple Moving Average value")
    current_price: float = Field(description="Current stock price")


class RSIResponse(BaseModel):
    """Response schema for RSI calculation result"""
    
    symbol: str = Field(description="Stock symbol")
    period: int = Field(description="RSI period in days")
    rsi: float = Field(description="Relative Strength Index value (0-100)")
    current_price: float = Field(description="Current stock price")


class EMAResponse(BaseModel):
    """Response schema for EMA calculation result"""
    
    symbol: str = Field(description="Stock symbol")
    period: int = Field(description="EMA period in days")
    ema: float = Field(description="Exponential Moving Average value")
    current_price: float = Field(description="Current stock price")
