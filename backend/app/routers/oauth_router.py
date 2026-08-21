import secrets
from urllib.parse import urlencode
from typing import Optional

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

@router.get("/google")
def google_login(request: Request):
    config = get_config()
    redirect_uri = "http://localhost:8000/oauth/google/callback"

    # Random, unguessable value tied to this login attempt.
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": config.OAUTH_CLIENT_ID or "",
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,      # JS can't read it — mitigates XSS-assisted theft
        secure=False,        # set True in production (requires HTTPS)
        samesite="lax",
        max_age=600,          # state is only valid for 10 minutes
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    cookie_state = request.cookies.get("oauth_state")

    # Both must be present AND match. Missing cookie = no login was ever
    # initiated from this browser, or it expired.
    if not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    if not code:
        raise HTTPException(status_code=400, detail="OAuth code missing")

    # Placeholder for real OAuth token exchange.
    user_in = UserCreate(
        email="oauth-user@example.com",
        username="oauth-user",
        password="oauth-password",
    )

    try:
        user = create_user(db=db, user_in=user_in)
    except ValueError:
        user = db.query(User).filter(User.email == user_in.email.lower()).first()

    token = create_access_token(subject=user.id)

    response = JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "username": user.username},
    })
    response.delete_cookie("oauth_state")  # one-time use — burn it after success
    return response