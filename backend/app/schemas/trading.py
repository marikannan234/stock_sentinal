"""
Pydantic schemas for user settings, support, and trading features.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


# ============================================
# User Settings Schemas
# ============================================

class UserSettingsBase(BaseModel):
    email_notifications: bool = Field(default=True)
    dark_mode: bool = Field(default=True)
    preferred_currency: str = Field(default="USD", max_length=10)
    two_factor_enabled: bool = Field(default=False)


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    dark_mode: Optional[bool] = None
    preferred_currency: Optional[str] = Field(default=None, max_length=10)
    two_factor_enabled: Optional[bool] = None


class UserSettingsRead(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# User Profile Schemas
# ============================================

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    avatar: Optional[str] = Field(default=None, max_length=500)


class UserProfileRead(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    avatar: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Support Ticket Schemas
# ============================================

class TradeTypeStr(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    CLOSE = "CLOSE"


class SupportTicketBase(BaseModel):
    subject: str = Field(default="Support Request", min_length=1, max_length=255)
    message: str = Field(default="No details provided.", min_length=1, max_length=5000)
    priority: str = Field(default="medium", max_length=50)


class SupportTicketCreate(SupportTicketBase):
    pass


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=50)
    response: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[str] = Field(default=None, max_length=50)


class SupportTicketRead(SupportTicketBase):
    id: int
    user_id: int
    status: str
    response: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# Trade Schemas
# ============================================

class TradeBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0)
    entry_price: float = Field(gt=0)
    trade_type: TradeTypeStr
    notes: Optional[str] = Field(default=None, max_length=500)


class TradeCreate(TradeBase):
    pass


class TradeUpdate(BaseModel):
    current_price: Optional[float] = Field(default=None, gt=0)
    status: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class TradeRead(TradeBase):
    id: int
    user_id: int
    current_price: float
    status: str
    created_at: datetime
    updated_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# Trade History Schemas
# ============================================

class TradeHistoryRead(BaseModel):
    id: int
    user_id: int
    trade_id: Optional[int]
    symbol: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    trade_type: str
    profit_loss: Optional[float]
    profit_loss_percent: Optional[float]
    duration_minutes: Optional[int]
    notes: Optional[str]
    created_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TradeHistorySummary(BaseModel):
    total_trades: int
    total_profit_loss: float
    win_rate: float
    avg_profit_loss: float
    total_invested: float
    best_trade: Optional[float]
    worst_trade: Optional[float]


# ============================================
# Stock Data Schemas
# ============================================

class StockHistoricalData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockIndicators(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_middle: Optional[float] = None


class StockDetailsRead(BaseModel):
    symbol: str
    current_price: float
    day_change: float
    day_change_percent: float
    open: float
    high: float
    low: float
    volume: int
    market_cap: Optional[str]
    dividend_yield: Optional[float]
    pe_ratio: Optional[float]
    indicators: StockIndicators
    historical_data: list[StockHistoricalData]
    timestamp: datetime


# ============================================
# Live Stock Ribbon Schemas
# ============================================

class StockQuote(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    high: float
    low: float
    volume: int
    timestamp: datetime


class LiveStockRibbon(BaseModel):
    stocks: list[StockQuote]
    total_count: int
    timestamp: datetime


# ============================================
# Market Summary Schemas
# ============================================

class StockMoverRead(BaseModel):
    symbol: str
    price: float
    change_percent: float
    volume: int
    market_cap: Optional[str]


class MarketSummary(BaseModel):
    market_time: datetime
    top_gainers: list[StockMoverRead]
    top_losers: list[StockMoverRead]
    most_active: list[StockMoverRead]
    market_status: str  # open, closed, pre, post
