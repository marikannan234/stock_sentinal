from functools import lru_cache
import json
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # General
    APP_NAME: str = "StockSentinel API"
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
    JWT_SECRET_KEY: str = "change-me"  # override in real env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs
    FINNHUB_API_KEY: str | None = None

    # Email Configuration
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-app-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM_NAME: str = "Stock Sentinel Alerts"
    
    # Email Features
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    EMAIL_NOTIFICATION_RETRY_COUNT: int = 3

    # Alert Configuration
    ALERT_COOLDOWN_MINUTES: int = 10  # Minutes between duplicate alert sends
    ALERT_DEV_MODE: bool = False  # Skip cooldown for testing (set to True locally)
    ALERT_LOG_COOLDOWN_CHECKS: bool = True  # Log when cooldown is active (verbose)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

