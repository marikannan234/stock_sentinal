from decimal import Decimal
from functools import lru_cache
import json
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator, Field
from typing import List, Optional


class Settings(BaseSettings):
    # General
    APP_NAME: str = "StockSentinel API"
    FRONTEND_URL: str | None = None  # Optional absolute frontend URL used in notification links
    ENVIRONMENT: str = "local"  # local | staging | production
    DEBUG: bool = True

    # Backend - comma-separated URLs or JSON array, e.g. "http://localhost:3000" or ["http://localhost:3000"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):  # type: ignore
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["http://localhost:3000"]  # default for local dev
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [u.strip() for u in v.split(",") if u.strip()]
        return ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel"

    # Security / JWT
    # ✅ CRITICAL FIX: JWT_SECRET_KEY MUST be provided via environment variable
    # No default value; will fail loudly if not set (protecting against accidental deployment with default)
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="Must be at least 32 characters; set via JWT_SECRET_KEY env var")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs
    FINNHUB_API_KEY: str | None = None

    # Paper trading: cash every new account starts with (existing accounts
    # were backfilled to this value by migration 0006).
    PAPER_TRADING_STARTING_CASH: Decimal = Field(default=Decimal("100000.00"), ge=0)

    # Email Configuration
    # ✅ CRITICAL FIX: Email credentials MUST be provided via environment variables
    # No default values; will fail if not set (protecting against credential exposure)
    MAIL_USERNAME: str = Field(..., description="SMTP email username; set via MAIL_USERNAME env var")
    MAIL_PASSWORD: str = Field(..., description="SMTP email password; set via MAIL_PASSWORD env var")
    MAIL_FROM: str = Field(..., description="Email from address; set via MAIL_FROM env var")
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM_NAME: str = "Stock Sentinel Alerts"
    
    # Email Features
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    EMAIL_NOTIFICATION_RETRY_COUNT: int = 3

    # Telegram Bot API notifications. Disabled until configured by the operator.
    ENABLE_TELEGRAM_NOTIFICATIONS: bool = False
    TELEGRAM_BOT_TOKEN: str | None = None

    # Deprecated, no effect: alerts are one-shot (they deactivate when they
    # fire and are re-armed by re-enabling them), so there is no cooldown.
    # Kept so existing .env files that still set these keep loading.
    ALERT_COOLDOWN_MINUTES: int = 10
    ALERT_DEV_MODE: bool = False
    ALERT_LOG_COOLDOWN_CHECKS: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

