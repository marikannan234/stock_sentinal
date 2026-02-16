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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

