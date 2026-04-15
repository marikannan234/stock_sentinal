"""
Health check endpoint for monitoring and uptime checking.

PRODUCTION-GRADE health endpoint with:
✅ Timestamp for monitoring
✅ Service information
✅ Environment details
✅ Ready for load balancers and monitoring systems
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Health check")
def health_check() -> dict:
    """
    Health check endpoint returning:
    - status: "ok" indicates service is healthy
    - timestamp: ISO 8601 timestamp for monitoring
    - service: Service name
    - environment: Current environment (dev/staging/prod)
    - uptime_check: Boolean indicating service is running
    
    Returns 200 OK when healthy.
    Used by: Load balancers, monitoring systems, Kubernetes liveness probes
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",  # Could be from app version
        "healthy": True,
        "uptime_check": True,  # Indicates service is responsive
    }


@router.get("/ping", summary="Quick ping check")
def ping() -> dict:
    """
    Lightweight ping/pong for rapid checks.
    Returns immediately with minimal payload.
    """
    return {"pong": True, "timestamp": datetime.now(timezone.utc).isoformat()}


