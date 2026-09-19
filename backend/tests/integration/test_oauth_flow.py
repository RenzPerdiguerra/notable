import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app

# ── Fake provider responses ───────────────────────────────────────────────
FAKE_TOKEN_RESPONSE = {
    "access_token" : "fake_access_token",
    "token_type"   : "Bearer",
    "expires_in"   : 3600,
}

FAKE_USER_INFO = {
    "google": {
        "sub"  : "1234567890",
        "email": "oauthuser@gmail.com",
        "name" : "Mickey Mouse",
    },
    "github": {
        "id"   : 9876543,
        "login": "mickeymouse",
        "email": "oauthuser@github.com",
    },
}

FAKE_GITHUB_EMAILS = [
    {"email": "oauthuser@github.com", "primary": True, "verified": True},
    {"email": "other@github.com",     "primary": False, "verified": True},
]


# ── Patch targets ─────────────────────────────────────────────────────────
EXCHANGE_TARGET  = "backend.app.routers.oauth_router.exchange_code_for_token"
USERINFO_TARGET  = "backend.app.routers.oauth_router.get_provider_user_info"
GH_EMAIL_TARGET  = "backend.app.routers.oauth_router.get_github_primary_email"


# ── Parametrize providers ─────────────────────────────────────────────────
# Every test marked with @pytest.mark.parametrize("provider", PROVIDERS)
# runs once for Google and once for GitHub automatically.
PROVIDERS = ["google", "github"]


# ── Login redirect tests ──────────────────────────────────────────────────
class TestOAuthLogin:

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_redirects_to_provider(self, provider):
        """Happy path — redirects to correct provider consent screen."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get(f"/oauth/{provider}")
        assert response.status_code == 307
        location = response.headers["location"]
        if provider == "google":
            assert "accounts.google.com" in location
        elif provider == "github":
            assert "github.com/login/oauth" in location

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_redirect_contains_client_id(self, provider):
        """Redirect URL contains client_id parameter."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get(f"/oauth/{provider}")
        assert "client_id=" in response.headers["location"]

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_redirect_contains_state(self, provider):
        """Redirect URL contains state for CSRF protection."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get(f"/oauth/{provider}")
        assert "state=" in response.headers["location"]

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_sets_oauth_state_cookie(self, provider):
        """Login response sets httponly oauth_state cookie."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get(f"/oauth/{provider}")
        assert "oauth_state" in response.cookies

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_unique_state_per_request(self, provider):
        """Each login attempt generates a unique state."""
        with TestClient(app, follow_redirects=False) as c:
            r1 = c.get(f"/oauth/{provider}")
            r2 = c.get(f"/oauth/{provider}")
        assert r1.cookies["oauth_state"] != r2.cookies["oauth_state"]

    def test_unsupported_provider_returns_400(self):
        """Negative — unsupported provider name returns 400."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get("/oauth/facebook")
        assert response.status_code == 400
        assert "Unsupported provider" in response.json()["detail"]


# ── Callback validation tests ─────────────────────────────────────────────
class TestOAuthCallbackValidation:

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_missing_code_returns_400(self, provider):
        """Negative — no code parameter."""
        with TestClient(app, follow_redirects=False) as c:
            c.cookies.set("oauth_state", "somestate")
            response = c.get(f"/oauth/{provider}/callback?state=somestate")
        assert response.status_code == 400
        assert "code" in response.json()["detail"].lower()

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_missing_state_returns_400(self, provider):
        """Negative — no state parameter."""
        with TestClient(app, follow_redirects=False) as c:
            c.cookies.set("oauth_state", "somestate")
            response = c.get(f"/oauth/{provider}/callback?code=abc")
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_state_mismatch_returns_400(self, provider):
        """Negative — state in URL doesn't match cookie."""
        with TestClient(app, follow_redirects=False) as c:
            c.cookies.set("oauth_state", "correct_state")
            response = c.get(
                f"/oauth/{provider}/callback?code=abc&state=wrong_state"
            )
        assert response.status_code == 400
        assert "state" in response.json()["detail"].lower()

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_missing_cookie_returns_400(self, provider):
        """Negative — no oauth_state cookie at all."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get(
                f"/oauth/{provider}/callback?code=abc&state=somestate"
            )
        assert response.status_code == 400

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_provider_error_param_returns_400(self, provider):
        """Negative — provider returns error param (e.g. user denied)."""
        with TestClient(app, follow_redirects=False) as c:
            c.cookies.set("oauth_state", "somestate")
            response = c.get(
                f"/oauth/{provider}/callback"
                f"?error=access_denied&state=somestate"
            )
        assert response.status_code == 400
        assert "OAuth error" in response.json()["detail"]

    def test_unsupported_provider_callback_returns_400(self):
        """Negative — unsupported provider in callback returns 400."""
        with TestClient(app, follow_redirects=False) as c:
            response = c.get("/oauth/facebook/callback?code=abc&state=x")
        assert response.status_code == 400


# ── Happy path callback tests ─────────────────────────────────────────────
class TestOAuthCallbackSuccess:

    def _run_callback(self, provider: str, db_session, extra_patches=None):
        """
        Helper — runs the callback with mocked provider calls.
        extra_patches: list of (target, mock) tuples for additional patching.
        """
        state     = secrets.token_urlsafe(16) if False else "test_state_abc"
        user_info = FAKE_USER_INFO[provider]

        patches = [
            patch(EXCHANGE_TARGET, new=AsyncMock(return_value=FAKE_TOKEN_RESPONSE)),
            patch(USERINFO_TARGET, new=AsyncMock(return_value=user_info)),
        ]
        if provider == "github":
            patches.append(
                patch(GH_EMAIL_TARGET, new=AsyncMock(return_value="oauthuser@github.com"))
            )
        if extra_patches:
            patches.extend(extra_patches)

        with TestClient(app, follow_redirects=False) as c:
            c.cookies.set("oauth_state", state)
            with ExitStack() as stack:
                for patcher in patches:
                    stack.enter_context(patcher)
                response = c.get(
                    f"/oauth/{provider}/callback?code=valid_code&state={state}"
                )
        return response

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_returns_token_and_user(self, provider, db_session):
        """Happy path — valid callback returns JWT and user info."""
        response = self._run_callback(provider, db_session)
        assert response.status_code == 200
        data = response.json()
        assert "access_token"       in data
        assert data["token_type"]   == "bearer"
        assert "user"               in data
        assert "email"              in data["user"]
        assert "id"                 in data["user"]
        assert "username"           in data["user"]

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_state_cookie_cleared_after_success(self, provider, db_session):
        """After success oauth_state cookie is deleted."""
        response = self._run_callback(provider, db_session)
        cookie_val = response.cookies.get("oauth_state", "")
        assert cookie_val == "" or "oauth_state" not in response.cookies

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_existing_user_not_duplicated(self, provider, db_session):
        """Calling callback twice with same email reuses existing user."""
        r1 = self._run_callback(provider, db_session)
        r2 = self._run_callback(provider, db_session)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["user"]["id"] == r2.json()["user"]["id"]

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_token_exchange_failure_returns_error(self, provider, db_session):
        """Negative — token exchange raises exception."""
        state = "test_state_fail"
        with patch(EXCHANGE_TARGET, new=AsyncMock(
            side_effect=HTTPException(status_code=400, detail="Token exchange failed")
        )):
            with TestClient(app, follow_redirects=False) as c:
                c.cookies.set("oauth_state", state)
                response = c.get(
                    f"/oauth/{provider}/callback?code=bad&state={state}"
                )
        assert response.status_code == 400

    @pytest.mark.parametrize("provider", PROVIDERS)
    def test_userinfo_failure_returns_error(self, provider, db_session):
        """Negative — user info fetch fails after token exchange."""
        state = "test_state_userinfo_fail"
        with patch(EXCHANGE_TARGET, new=AsyncMock(return_value=FAKE_TOKEN_RESPONSE)), \
             patch(USERINFO_TARGET, new=AsyncMock(
                 side_effect=HTTPException(status_code=400, detail="Failed to fetch user info")
             )):
            with TestClient(app, follow_redirects=False) as c:
                c.cookies.set("oauth_state", state)
                response = c.get(
                    f"/oauth/{provider}/callback?code=valid&state={state}"
                )
        assert response.status_code == 400


# ── GitHub-specific tests ─────────────────────────────────────────────────
class TestGitHubSpecific:

    def test_github_fetches_email_separately_when_missing(self, db_session):
        """GitHub callback fetches email from /user/emails if not in /user."""
        state         = "github_email_test"
        no_email_info = {**FAKE_USER_INFO["github"], "email": None}

        with patch(EXCHANGE_TARGET, new=AsyncMock(return_value=FAKE_TOKEN_RESPONSE)), \
             patch(USERINFO_TARGET, new=AsyncMock(return_value=no_email_info)), \
             patch(GH_EMAIL_TARGET, new=AsyncMock(return_value="oauthuser@github.com")):
            with TestClient(app, follow_redirects=False) as c:
                c.cookies.set("oauth_state", state)
                response = c.get(
                    f"/oauth/github/callback?code=valid_code&state={state}"
                )

        assert response.status_code == 200
        assert response.json()["user"]["email"] == "oauthuser@github.com"

    def test_github_no_email_anywhere_returns_400(self, db_session):
        """Negative — GitHub returns no email at all → 400."""
        state         = "github_no_email"
        no_email_info = {**FAKE_USER_INFO["github"], "email": None}

        with patch(EXCHANGE_TARGET, new=AsyncMock(return_value=FAKE_TOKEN_RESPONSE)), \
             patch(USERINFO_TARGET, new=AsyncMock(return_value=no_email_info)), \
             patch(GH_EMAIL_TARGET, new=AsyncMock(return_value=None)):
            with TestClient(app, follow_redirects=False) as c:
                c.cookies.set("oauth_state", state)
                response = c.get(
                    f"/oauth/github/callback?code=valid_code&state={state}"
                )

        assert response.status_code == 400
        assert "Email" in response.json()["detail"]