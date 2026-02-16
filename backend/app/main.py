from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth as auth_routes
from app.api.routes import health as health_routes
from app.api.routes import news as news_routes
from app.api.routes import portfolio as portfolio_routes
from app.api.routes import sentiment as sentiment_routes
from app.api.routes import stock as stock_routes
from app.api.routes import watchlist as watchlist_routes
from app.api.routes import search as search_routes
from app.config import settings
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for small projects / dev). In production,
    # prefer proper migrations (e.g. Alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


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


app.include_router(health_routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(stock_routes.router, prefix="/api")
app.include_router(news_routes.router, prefix="/api")
app.include_router(sentiment_routes.router, prefix="/api")
app.include_router(watchlist_routes.router, prefix="/api")
app.include_router(portfolio_routes.router, prefix="/api")
app.include_router(search_routes.router, prefix="/api")

