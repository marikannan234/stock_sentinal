"""
Shared pytest fixtures.

By default tests run against an in-memory SQLite database, so they need no
running Postgres. Set TEST_DATABASE_URL to a *disposable* PostgreSQL database
to run the same suite against the real schema: it is wiped and rebuilt with
`alembic upgrade head`, and the row-locking tests (skipped on SQLite) run too.

Settings are forced through environment variables *before* the app is
imported, because `app.config.settings` is built at import time.
"""

import os
import tempfile
from decimal import Decimal
from pathlib import Path

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
USING_POSTGRES = bool(TEST_DATABASE_URL)
STARTING_CASH = Decimal("10000.00")

_tmp_dir = tempfile.mkdtemp(prefix="stocksentinel-tests-")
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DEBUG": "false",
        "JWT_SECRET_KEY": "test-secret-key-that-is-at-least-32-characters",
        "MAIL_USERNAME": "test@example.com",
        "MAIL_PASSWORD": "test-password",
        "MAIL_FROM": "test@example.com",
        "ENABLE_EMAIL_NOTIFICATIONS": "false",
        "PAPER_TRADING_STARTING_CASH": str(STARTING_CASH),
        # The app's own engine is created at import time with QueuePool
        # arguments, so it needs a file-based URL. Tests use their own engine.
        "DATABASE_URL": TEST_DATABASE_URL or f"sqlite:///{_tmp_dir}/unused.db",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.api.deps import get_db_session  # noqa: E402
from app.db.session import Base  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app import models as _models  # noqa: E402,F401  (registers every table on Base.metadata)
from app.services import trading_service  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]

requires_postgres = pytest.mark.skipif(
    not USING_POSTGRES,
    reason="needs TEST_DATABASE_URL (row locking is a no-op on SQLite)",
)


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture(scope="session")
def engine():
    if not USING_POSTGRES:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        yield engine
        engine.dispose()
        return

    from alembic import command
    from alembic.config import Config

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(engine):
    if USING_POSTGRES:
        tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    else:
        Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    yield factory
    if not USING_POSTGRES:
        Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


class FakeMarket:
    """Stands in for the live quote source. Unknown symbols have no price."""

    def __init__(self):
        self.prices: dict[str, Decimal] = {}
        self.calls: list[str] = []

    def set(self, symbol: str, price: str) -> None:
        self.prices[symbol.upper()] = Decimal(price)

    def get_price(self, symbol: str) -> Decimal:
        self.calls.append(symbol)
        if symbol not in self.prices:
            raise trading_service.MarketDataUnavailableError(
                f"Could not get a market price for {symbol}. The trade was not executed."
            )
        return trading_service.to_price(self.prices[symbol])


@pytest.fixture(autouse=True)
def market(monkeypatch):
    fake = FakeMarket()
    monkeypatch.setattr(trading_service, "get_market_price", fake.get_price)
    return fake


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = _override_get_db
    # Not used as a context manager, so the lifespan (alert scheduler) never starts.
    test_client = TestClient(fastapi_app)
    try:
        yield test_client
    finally:
        fastapi_app.dependency_overrides.clear()


USER_EMAIL = "trader@example.com"
USER_PASSWORD = "correct-horse-battery"


@pytest.fixture()
def registered_user(client):
    response = client.post(
        "/api/auth/register",
        json={"email": USER_EMAIL, "password": USER_PASSWORD, "full_name": "Test Trader"},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def auth_headers(client, registered_user):
    response = client.post(
        "/api/auth/login",
        data={"username": USER_EMAIL, "password": USER_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
