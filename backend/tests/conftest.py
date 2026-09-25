"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database so they need no running
Postgres. Settings are forced through environment variables *before* the app
is imported, because `app.config.settings` is built at import time.
"""

import os
import tempfile

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
        # The app's own engine is created at import time with QueuePool
        # arguments, so it needs a file-based URL. Tests use their own engine.
        "DATABASE_URL": f"sqlite:///{_tmp_dir}/unused.db",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.api.deps import get_db_session  # noqa: E402
from app.db.session import Base  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app import models as _models  # noqa: E402,F401  (registers every table on Base.metadata)


@compiles(JSONB, "sqlite")
def _compile_jsonb_for_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


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
