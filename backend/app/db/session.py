from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import Pool

from app.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# ✅ FIX: Proper database connection pooling configuration
# Prevents connection leaks, stale connections, and thread pool exhaustion
engine = create_engine(
    settings.DATABASE_URL,
    # Connection health check on checkout
    pool_pre_ping=True,
    # Pool size for connection pooling (production: 20-50)
    pool_size=20,
    # Additional overflow connections beyond pool_size
    max_overflow=10,
    # Recycle connections after 1 hour to prevent stale connections
    pool_recycle=3600,
    # Don't echo SQL in production
    echo=False,
)


@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set connection timeout to prevent hangs."""
    if "postgresql" in settings.DATABASE_URL.lower():
        # PostgreSQL statement timeout (5 minutes for safety)
        dbapi_conn.set_isolation_level(0)
        cur = dbapi_conn.cursor()
        cur.execute("SET statement_timeout = 300000")
        cur.close()
        dbapi_conn.set_isolation_level(1)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a database session with proper error handling.
    Ensures session is always cleaned up, even on exception.
    
    CRITICAL: Prevents connection pool leaks and stale connections.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Log and rollback on any exception
        logger.error(
            f"Database error, rolling back transaction: {e}",
            exc_info=True,
            extra={"error_type": type(e).__name__}
        )
        db.rollback()
        raise  # Re-raise so caller knows there was an error
    finally:
        # Always close, even if error occurred
        try:
            db.close()
        except Exception as e:
            logger.warning(
                f"Error closing database session: {e}",
                exc_info=True
            )

