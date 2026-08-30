import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base, get_db
import backend.app.db as app_db
from backend.main import app
from backend.app.schemas.user import UserCreate
from backend.app.services.user_service import create_user
from backend.app.schemas.chat import ChatSessionCreate
from backend.app.services.chat_service import create_chat_session

# ── Single In-Memory Engine ───────────────────────────────────────────────
# StaticPool ensures ALL connections share the same in-memory database
# check_same_thread=False allows SQLite to work across threads (FastAPI uses threads)

UNIT_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # ← this is the fix for in-memory multi-connection issue
    echo=False              # set True to debug SQL queries
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=UNIT_TEST_ENGINE
)

# Ensure the application's db engine/session use the TEST_ENGINE so all
# code paths (including imports that reference backend.app.db.engine)
# operate against the same in-memory database used by tests.

app_db.engine = UNIT_TEST_ENGINE
app_db.SessionLocal = TestingSessionLocal

# ── Create All Tables Once ────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create schema once before all tests, drop after session."""
    # For PostgreSQL we use schema='management' in models. SQLite
    # does not support schemas the same way, so attach an in-memory
    # database with the name `management` so schema-qualified tables
    # (e.g. management.users) can be created during tests.
    connection = UNIT_TEST_ENGINE.connect()
    connection.execute(text("ATTACH DATABASE ':memory:' AS management"))
    Base.metadata.create_all(bind=connection)
    yield
    Base.metadata.drop_all(bind=connection)
    connection.close()

# ── DB Session Per Test With Rollback ─────────────────────────────────────
@pytest.fixture(scope="function")
def db_session(setup_db):
    """
    Each test gets a clean DB state via transaction rollback.
    No data leaks between tests.
    """
    print("\n--- NEW DB SESSION STARTED ---")
    connection  = UNIT_TEST_ENGINE.connect()
    transaction = connection.begin()          # outer, "real" transaction
    session     = TestingSessionLocal(bind=connection)
    original_commit = session.commit

    # Start a SAVEPOINT to handle commit() in test modules
    def fake_savepoint():
        print("--- FAKE COMMIT CALLED (flush only) ---")
        session.flush()
    
    session.commit = fake_savepoint

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    print("--- ROLLING BACK ---")
    session.commit = original_commit
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
    with TestClient(app,
                    raise_server_exceptions=True,
                    follow_redirects=False
                    ) as c:
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

# ── Chat Fixture ────────────────────────────────────────────────────
@pytest.fixture
def chat_session(db_session):
    chat_session_in = ChatSessionCreate(
        user_id = 1,
        title = "MyTestChat",
    )
    return create_chat_session(db_session, chat_session_in)