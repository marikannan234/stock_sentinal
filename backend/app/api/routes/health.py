from fastapi import APIRouter

from app.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health check")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

