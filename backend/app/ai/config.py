from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """
    Configuration for AI-related components.

    Values are loaded from environment variables with the prefix `AI_`.
    """

    # Sentiment
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"

    # Prediction
    PREDICTION_BACKEND: Literal["prophet", "lstm"] = "prophet"
    PREDICTION_DEFAULT_HORIZON_DAYS: int = 5

    class Config:
        env_prefix = "AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()


ai_settings = get_ai_settings()

