import secrets
from urllib.parse import urlencode
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.core.config import get_config
from backend.app.core.security import create_access_token
from backend.app.models.model import User
from backend.app.schemas.user import UserCreate
from backend.app.services.user_service import create_user

router = APIRouter(prefix="/oauth", tags=["OAuth"])

# ── Provider Registry ─────────────────────────────────────────────────────
# Add new providers here without touching route logic.
# Each provider defines how to build its auth URL, exchange a token,
# and fetch user info — all differences are isolated to this map.

def build_provider_config(config) -> dict:
    return {
        "google": {
            "auth_url"     : "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url"    : "https://oauth2.googleapis.com/token",
            "userinfo_url" : "https://www.googleapis.com/oauth2/v3/userinfo",
            "client_id"    : config.OAUTH_GOOGLE_CLIENT_ID,
            "client_secret": config.OAUTH_GOOGLE_CLIENT_SECRET,
            "scope"        : "openid email profile",
            "extra_params" : {
                "access_type": "offline",
                "prompt"     : "consent",
            },
        },
        "github": {
            "auth_url"     : "https://github.com/login/oauth/authorize",
            "token_url"    : "https://github.com/login/oauth/access_token",
            "userinfo_url" : "https://api.github.com/user",
            "client_id"    : config.OAUTH_GITHUB_CLIENT_ID,
            "client_secret": config.OAUTH_GITHUB_CLIENT_SECRET,
            "scope"        : "read:user user:email",
            "extra_params" : {},
        },
    }

SUPPORTED_PROVIDERS = {"google", "github"}


# ── Helpers ───────────────────────────────────────────────────────────────
def get_redirect_uri(request: Request, provider: str) -> str:
    """Build redirect URI dynamically based on environment and provider."""
    base = str(request.base_url).rstrip("/")
    return f"{base}/oauth/{provider}/callback"


def validate_provider(provider: str):
    """Raise 400 if provider is not supported."""
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
        )


async def exchange_code_for_token(
    provider_cfg : dict,
    code         : str,
    redirect_uri : str,
) -> dict:
    """Exchange authorization code for provider access token."""
    headers = {"Accept": "application/json"}   # GitHub needs this
    async with httpx.AsyncClient() as client:
        response = await client.post(
            provider_cfg["token_url"],
            data={
                "code"         : code,
                "client_id"    : provider_cfg["client_id"],
                "client_secret": provider_cfg["client_secret"],
                "redirect_uri" : redirect_uri,
                "grant_type"   : "authorization_code",
            },
            headers=headers,
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {response.text}"
        )
    return response.json()


async def get_provider_user_info(provider_cfg: dict, access_token: str) -> dict:
    """Fetch user profile from the OAuth provider."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            provider_cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch user info from provider"
        )
    return response.json()


async def get_github_primary_email(access_token: str) -> Optional[str]:
    """
    GitHub does not always return email in /user — fetch it separately
    from /user/emails if needed.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code != 200:
        return None
    emails = response.json()
    # return the primary verified email
    for entry in emails:
        if entry.get("primary") and entry.get("verified"):
            return entry["email"]
    return None


def normalize_user_info(provider: str, user_info: dict, access_token: str = None) -> dict:
    """
    Each provider returns user info in a different shape.
    Normalize to a consistent { email, username, sub } dict.
    """
    if provider == "google":
        return {
            "email"   : user_info.get("email", ""),
            "username": user_info.get("name", "").replace(" ", "").lower(),
            "sub"     : f"google|{user_info.get('sub', '')}",
        }
    if provider == "github":
        return {
            "email"   : user_info.get("email", ""),   # may be None — handled in callback
            "username": user_info.get("login", ""),
            "sub"     : f"github|{user_info.get('id', '')}",
        }
    raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


# ── Routes ────────────────────────────────────────────────────────────────
@router.get("/{provider}")
def oauth_login(provider: str, request: Request):
    """Redirect user to the OAuth provider's consent screen."""
    validate_provider(provider)

    config       = get_config()
    providers    = build_provider_config(config)
    provider_cfg = providers[provider]
    state        = secrets.token_urlsafe(32)
    redirect_uri = get_redirect_uri(request, provider)

    params = {
        "client_id"    : provider_cfg["client_id"] or "",
        "redirect_uri" : redirect_uri,
        "response_type": "code",
        "scope"        : provider_cfg["scope"],
        "state"        : state,
        **provider_cfg["extra_params"],
    }
    auth_url = provider_cfg["auth_url"] + "?" + urlencode(params)

    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key      = "oauth_state",
        value    = state,
        httponly = True,
        secure   = False,    # set True in production
        samesite = "lax",
        max_age  = 600,
    )
    return response


@router.get("/{provider}/callback")
async def oauth_callback(
    provider : str,
    request  : Request,
    code     : Optional[str] = Query(default=None),
    error    : Optional[str] = Query(default=None),
    state    : Optional[str] = Query(default=None),
    db       : Session       = Depends(get_db),
):
    """Handle OAuth callback — exchange code for user info and issue JWT."""
    validate_provider(provider)

    config       = get_config()
    providers    = build_provider_config(config)
    provider_cfg = providers[provider]

    # ── 1. Provider-level error ───────────────────────────────────────────
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # ── 2. CSRF state validation ──────────────────────────────────────────
    cookie_state = request.cookies.get("oauth_state")
    if not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # ── 3. Code must be present ───────────────────────────────────────────
    if not code:
        raise HTTPException(status_code=400, detail="OAuth code missing")

    # ── 4. Exchange code for access token ─────────────────────────────────
    redirect_uri = get_redirect_uri(request, provider)
    token_data   = await exchange_code_for_token(provider_cfg, code, redirect_uri)
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    # ── 5. Fetch user info ────────────────────────────────────────────────
    raw_user_info = await get_provider_user_info(provider_cfg, access_token)
    user_info     = normalize_user_info(provider, raw_user_info)

    # GitHub may not return email in /user — fetch separately
    if provider == "github" and not user_info["email"]:
        user_info["email"] = await get_github_primary_email(access_token) or ""

    if not user_info["email"]:
        raise HTTPException(status_code=400, detail="Email not returned by provider")

    # ── 6. Find or create user ────────────────────────────────────────────
    email = user_info["email"].lower()
    user  = db.query(User).filter(User.email == email).first()
    if not user:
        user_in = UserCreate(
            email    = email,
            username = user_info["username"] or email.split("@")[0],
            password = secrets.token_urlsafe(32),
        )
        user = create_user(db=db, user_in=user_in)

    # ── 7. Issue JWT ──────────────────────────────────────────────────────
    jwt_token = create_access_token(subject=user.id)

    response = JSONResponse({
        "access_token": jwt_token,
        "token_type"  : "bearer",
        "user"        : {
            "id"      : user.id,
            "email"   : user.email,
            "username": user.username,
        },
    })
    response.delete_cookie("oauth_state")
    return response