"""
Stock Sentinel API - Main application entry point.

Features:
  - Production-grade logging
  - Global exception handling
  - Request/response middleware
  - CORS configuration
  - Database initialization
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import Base, engine

# Import logging and error handling modules FIRST
from app.core.logging_config import setup_logging, get_logger
from app.core.error_handlers import setup_middleware, setup_exception_handlers

# Import scheduler
from app.services.scheduler import start_scheduler, stop_scheduler

# Then import routes
from app.api.routes import auth as auth_routes
from app.api.routes import health as health_routes
from app.api.routes import indicator as indicator_routes
from app.api.routes import news as news_routes
from app.api.routes import portfolio as portfolio_routes
from app.api.routes import sentiment as sentiment_routes
from app.api.routes import stock as stock_routes
from app.api.routes import watchlist as watchlist_routes
from app.api.routes import search as search_routes
from app.api.routes import alert as alert_routes
from app.api.routes import websocket as websocket_routes
from app.api.routes import user_profile as user_profile_routes
from app.api.routes import support as support_routes
from app.api.routes import trading as trading_routes
from app.api.routes import stocks_extended as stocks_extended_routes


# ============================================
# Setup logging on module import
# ============================================
setup_logging()
logger = get_logger(__name__)


# ============================================
# Application lifespan
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    
    Startup:
      - Initialize database tables
      - Start background scheduler for alert checking
      - Log startup message
    
    Shutdown:
      - Stop background scheduler
      - Clean up resources
      - Log shutdown message
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} (Environment: {settings.ENVIRONMENT})")
    
    # ⚠️ IMPORTANT: Do NOT use Base.metadata.create_all() with Alembic!
    # Alembic is the source of truth for schema. Using create_all() causes:
    # - Duplicate index creation errors
    # - Schema conflicts between code and migrations
    # - Race conditions in production
    # Instead, always use: alembic upgrade head
    # For development: Alembic migrations are automatically applied
    
    # Start background scheduler for alert checking
    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}")
        # Don't fail app startup if scheduler fails, just log the error
    
    logger.info(f"{settings.APP_NAME} started successfully")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # Stop background scheduler
    try:
        stop_scheduler()
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# ============================================
# Create FastAPI application
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time stock market platform with AI-powered insights",
    version="0.1.0",
    debug=settings.DEBUG and settings.ENVIRONMENT != "production",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

logger.info("FastAPI application created")


# ============================================
# Setup middleware (BEFORE routes)
# ============================================
setup_middleware(app)
logger.info("Middleware configured")


# ============================================
# Setup exception handlers (BEFORE routes)
# ============================================
setup_exception_handlers(app)
logger.info("Exception handlers configured")


# ============================================
# Configure CORS
# ============================================
cors_origins = [str(o) for o in settings.BACKEND_CORS_ORIGINS]
if "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with origins: {cors_origins}")


# ============================================
# Register API routes
# ============================================
app.include_router(health_routes.router, prefix="/api", tags=["health"])
app.include_router(auth_routes.router, prefix="/api", tags=["auth"])
app.include_router(indicator_routes.router, prefix="/api", tags=["indicators"])
app.include_router(stock_routes.router, prefix="/api", tags=["stock"])
app.include_router(stocks_extended_routes.router, prefix="/api", tags=["stocks"])
app.include_router(news_routes.router, prefix="/api", tags=["news"])
app.include_router(sentiment_routes.router, prefix="/api", tags=["sentiment"])
app.include_router(watchlist_routes.router, prefix="/api", tags=["watchlist"])
app.include_router(portfolio_routes.router, prefix="/api", tags=["portfolio"])
app.include_router(search_routes.router, prefix="/api", tags=["search"])
app.include_router(alert_routes.router, prefix="/api", tags=["alerts"])
app.include_router(user_profile_routes.router, prefix="/api", tags=["user"])
app.include_router(support_routes.router, prefix="/api", tags=["support"])
app.include_router(trading_routes.router, prefix="/api", tags=["trading"])
app.include_router(websocket_routes.router, tags=["websocket"])

logger.info(f"All routes registered ({settings.APP_NAME} is ready to serve requests)")

