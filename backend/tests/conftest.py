import os
os.environ["FASTAPI_ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_db
import backend.app.db as app_db
from backend.main import app
from backend.app.core.security import create_access_token
from backend.app.schemas.user import UserCreate
from backend.app.services.user_service import create_user

# ── Single In-Memory Engine ───────────────────────────────────────────────
# StaticPool ensures ALL connections share the same in-memory database
# check_same_thread=False allows SQLite to work across threads (FastAPI uses threads)
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # ← this is the fix for in-memory multi-connection issue
    echo=False              # set True to debug SQL queries
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)

# Ensure the application's db engine/session use the TEST_ENGINE so all
# code paths (including imports that reference backend.app.db.engine)
# operate against the same in-memory database used by tests.

app_db.engine = TEST_ENGINE
app_db.SessionLocal = TestingSessionLocal

# ── Create All Tables Once ────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create schema once before all tests, drop after session."""
    # For PostgreSQL we use schema='management' in models. SQLite
    # does not support schemas the same way, so attach an in-memory
    # database with the name `management` so schema-qualified tables
    # (e.g. management.users) can be created during tests.
    connection = TEST_ENGINE.connect()
    connection.execute(text("ATTACH DATABASE ':memory:' AS management"))
    Base.metadata.create_all(bind=connection)
    yield
    Base.metadata.drop_all(bind=connection)
    connection.close()

# ── DB Session Per Test With Rollback ─────────────────────────────────────
@pytest.fixture(scope="function")
def db_session(setup_database):
    """
    Each test gets a clean DB state via transaction rollback.
    No data leaks between tests.
    """
    connection  = TEST_ENGINE.connect()
    transaction = connection.begin()          # outer, "real" transaction
    session     = TestingSessionLocal(bind=connection)

    # Start a SAVEPOINT to handle commit() in test modules
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            # → immediately open a new one so future writes stay nested
            nested = connection.begin_nested()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()   # Teardown - rollback everything the test did
    connection.close()
    app.dependency_overrides.clear()

# ── Test Client ───────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def client(db_session):
    """
    TestClient that shares the same DB session as db_session fixture.
    Override is already set in db_session fixture.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

# ── Auth Fixtures ─────────────────────────────────────────────────────────
@pytest.fixture
def test_user(db_session):
    """Create a test user directly via service layer."""
    user_in = UserCreate(
        email    = "test@example.com",
        username = "testuser",
        password = "password123"
    )
    return create_user(db_session, user_in)


@pytest.fixture
def user(test_user):
    """Alias for tests that expect a `user` fixture name."""
    return test_user

@pytest.fixture
def auth_cookies(client, test_user):
    """
    Login via API to get real HttpOnly cookies.
    Use this instead of manually crafting tokens —
    tests real auth flow end to end.
    """
    response = client.post("/auth/login", json={
        "email"   : "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    return client.cookies   # cookies automatically sent on subsequent requests

@pytest.fixture
def auth_client(client, auth_cookies):
    """
    A TestClient that is already authenticated.
    Use this for protected route tests.
    """
    return client   # cookies already set on the client from auth_cookies fixture

# ── OAuth Mock Fixture ────────────────────────────────────────────────────
@pytest.fixture
def mock_oauth(monkeypatch):
    """
    Mock OAuth provider so tests never hit Google/GitHub.
    Replace with your actual OAuth service call.
    """
    async def fake_oauth_callback(code: str):
        return {
            "email"   : "oauthuser@gmail.com",
            "username": "oauthuser",
            "sub"     : "google-oauth2|123456"
        }

    monkeypatch.setattr(
        "backend.app.services.oauth_service.get_oauth_user",
        fake_oauth_callback
    )