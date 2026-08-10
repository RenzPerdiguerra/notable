from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
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
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={config.OAUTH_CLIENT_ID or ''}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="OAuth code missing")

    # Placeholder for real OAuth token exchange.
    # In production, exchange the code for an access token and user profile.
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
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "username": user.username},
    }
