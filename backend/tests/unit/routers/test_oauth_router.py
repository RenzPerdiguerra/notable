from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_google_login_redirect():
    response = client.get("/oauth/google")
    assert response.status_code == 307  # Redirect
    assert "accounts.google.com" in response.headers["location"]

def test_google_callback_missing_code():
    response = client.get("/oauth/google/callback")
    assert response.status_code == 400
    assert response.json()["detail"] == "OAuth code missing"

def test_google_callback_creates_user(db_session):
    response = client.get("/oauth/google/callback?code=fakecode")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "oauth-user@example.com"
