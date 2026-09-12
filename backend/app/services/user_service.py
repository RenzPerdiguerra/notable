from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.model import User
from backend.app.schemas.user import UserCreate, UserLogin, UserUpdate
from backend.app.core.security import hash_password, verify_password
from backend.app.services.error_handler import EmailAlreadyExistsException, UserNameAlreadyExistsException

def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    if _get_user_by_email(db, user_in.email):
        raise EmailAlreadyExistsException("email is already registered")

    if db.query(User).filter(User.username == user_in.username.strip()).first():
        raise UserNameAlreadyExistsException("username is already taken")

    user = User(
        email=user_in.email.lower(),
        username=user_in.username.strip(),
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
    user = get_user(db, user_id)
    if not user:
        return None

    if user_in.email is not None:
        if _get_user_by_email(db, user_in.email) and user.email != user_in.email.lower():
            raise ValueError("email is already registered")
        user.email = user_in.email.lower()

    if user_in.username is not None:
        if db.query(User).filter(User.username == user_in.username.strip(), User.id != user_id).first():
            raise ValueError("username is already taken")
        user.username = user_in.username.strip()

    if user_in.password is not None:
        user.hashed_password = hash_password(user_in.password)

    if user_in.role is not None:
        user.role = user_in.role

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


def authenticate_user(db: Session, user_in: UserLogin) -> Optional[User]:
    user = _get_user_by_email(db, user_in.email)
    if not user:
        return None

    if not verify_password(user_in.password, user.hashed_password):
        return None

    return user


