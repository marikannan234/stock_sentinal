from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    # General
    APP_NAME: str = "StockSentinel API"
    ENVIRONMENT: str = "local"  # local | staging | production
    DEBUG: bool = True

    # Backend
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://stocksentinel:password@localhost:5432/stocksentinel"

    # Security / JWT
    JWT_SECRET_KEY: str = "change-me"  # override in real env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # External APIs
    FINNHUB_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

