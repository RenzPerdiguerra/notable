from urllib.parse import urlparse, parse_qs

def _get_state_from_login(client):
    """Helper: hits /oauth/google, returns the state value Google would echo back.
    TestClient keeps the oauth_state cookie in its jar automatically.
    """
    response = client.get("/oauth/google")
    location = response.headers["location"]
    query = parse_qs(urlparse(location).query)
    return query["state"][0]


def test_google_login_redirect(client):
    response = client.get("/oauth/google")
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers["location"]
    # state param must be present in the redirect URL
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert "state" in query
    # cookie must be set so we can validate it on callback
    assert "oauth_state" in response.cookies


def test_google_callback_missing_code(client):
    state = _get_state_from_login(client)
    response = client.get(f"/oauth/google/callback?state={state}")
    assert response.status_code == 400
    assert response.json()["detail"] == "OAuth code missing"


def test_google_callback_missing_state(client):
    # No prior /oauth/google call → no cookie → state check fails first
    response = client.cookies.clear() or client.get("/oauth/google/callback?code=fakecode")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OAuth state"


def test_google_callback_state_mismatch(client):
    _get_state_from_login(client)  # sets a valid cookie
    response = client.get("/oauth/google/callback?code=fakecode&state=wrong-value")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OAuth state"


def test_google_callback_provider_error(client):
    state = _get_state_from_login(client)
    response = client.get(
        f"/oauth/google/callback?error=access_denied&state={state}"
    )
    assert response.status_code == 400
    assert "access_denied" in response.json()["detail"]


def test_google_callback_creates_user(db_session, client):
    state = _get_state_from_login(client)
    response = client.get(f"/oauth/google/callback?code=fakecode&state={state}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "oauth-user@example.com"