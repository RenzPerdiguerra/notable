import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.app.db import Base, get_db
import backend.app.db as app_db
from backend.app.schemas.user import UserCreate
from backend.app.schemas.chat import ChatSessionCreate
from backend.app.services.user_service import create_user
from backend.app.services.chat_service import create_chat_session


# Require URL for real DB connection
INTEGRATION_DB_URL = os.environ.get("TEST_DATABASE_URL")

INTEGRATION_TEST_ENGINE = create_engine(INTEGRATION_DB_URL, echo=False)

IntegrationSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=INTEGRATION_TEST_ENGINE
)

app_db.engine = INTEGRATION_TEST_ENGINE
app_db.session = IntegrationSessionLocal

@pytest.fixture(scope = "session", autouse=True)
def setup_db():
    
    import backend.app.models.model
    
    with INTEGRATION_TEST_ENGINE.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS management"))
        conn.commit()
    
    Base.metadata.create_all(bind=INTEGRATION_TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=INTEGRATION_TEST_ENGINE)
    
    
@pytest.fixture(scope = "function")
def db_session(setup_db):
    connection = INTEGRATION_TEST_ENGINE.connect()
    transaction = connection.begin()
    session = IntegrationSessionLocal(bind=connection)

    nested = connection.begin_nested()
    
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(db_session):
    with TestClient(app,
        raise_server_exceptions=False,
        follow_redirects=False
    ) as c:
        yield c
        
@pytest.fixture
def test_user(db_session):
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    return create_user(db_session, user_in)

@pytest.fixture
def user(test_user):
    return test_user

@pytest.fixture
def auth_cookies(client, test_user):
    response = client.post("auth/login", json={
        "email" : "test@example.com",
        "username" : "testuser",
        "password" : "password123"
    })
    assert response.status_code == 200
    return client.cookies

@pytest.fixture
def auth_client(client, auth_cookies):
    return client

@pytest.fixture
def chat_session(db_session):
    chat_session_in = ChatSessionCreate(
        user_id = 1,
        title = "Integration Test Chat"
    )
    return create_chat_session(db_session, chat_session_in)

@pytest.fixture
def mock_oauth(monkeypatch):
    async def fake_oauth_callback(code: str):
        return {
            "email": "oauthuser@gmail.com",
            "username": "mickeymouse",
            "sub": "google-oauth2|123"
        }
    monkeypatch.setattr(
        "backend.app.routers.oauth_router",
        fake_oauth_callback
    )