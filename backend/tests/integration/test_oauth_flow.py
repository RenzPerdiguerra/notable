"""
def test_oauth_creates_new_user_and_sets_cookie(client):
    response = client.get("/oauth/google/callback?code=fake_code")
    assert response.status_code == 200
    assert "access_token" in response.cookies
    
def test_oauth_existing_user_login(client, mock_oauth, db_session):
    #OAuth with existing email should log in, not create duplicate.
    from backend.app.schemas.user import UserCreate
    from backend.app.services.user_service import create_user
    create_user(db_session, UserCreate(
        email="test@example.com",
        username="mickeymouse",
        password=""
    ))
    
    response = client.post("/oauth/callback?code=fake_code")
    assert response.status_code == 200
    assert "access_cookies" in response.cookies
    
def test_oauth_callback_missing_code_returns_error(client):
    response = client.post("/oauth/callback")
    assert response.status_code in [400, 422]

"""
   
def test_oauth_callback_invalid_code_returns_401(client, monkeypatch):
    """When OAuth provider rejects code, should return 401."""
    async def fake_callback(code: str):
        raise Exception("Invalid code")
    
    response = client.post("oauth/callback?code=bad_code")
    