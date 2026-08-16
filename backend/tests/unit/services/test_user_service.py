import pytest
from backend.app.services.user_service import create_user, update_user, delete_user, authenticate_user
from backend.app.schemas.user import UserCreate, UserUpdate, UserLogin

def test_create_user_success(db_session):
    user_in = UserCreate(email="new@example.com", username="newuser", password="password123")
    user = create_user(db_session, user_in)
    assert user.id is not None
    assert user.email == "new@example.com"

def test_create_user_duplicate_email(db_session):
    user_in = UserCreate(email="dup@example.com", username="dupuser", password="password123")
    create_user(db_session, user_in)
    with pytest.raises(ValueError):
        create_user(db_session, user_in)

def test_update_user_username(db_session):
    user_in = UserCreate(email="update@example.com", username="oldname", password="password123")
    user = create_user(db_session, user_in)
    update_in = UserUpdate(username="newname")
    updated = update_user(db_session, user.id, update_in)
    assert updated.username == "newname"

def test_delete_user(db_session):
    user_in = UserCreate(email="del@example.com", username="deluser", password="password123")
    user = create_user(db_session, user_in)
    success = delete_user(db_session, user.id)
    assert success

def test_authenticate_user_success(db_session):
    user_in = UserCreate(email="auth@example.com", username="authuser", password="password123")
    user = create_user(db_session, user_in)
    login_in = UserLogin(email="auth@example.com", password="password123")
    auth_user = authenticate_user(db_session, login_in)
    assert auth_user is not None

def test_authenticate_user_wrong_password(db_session):
    user_in = UserCreate(email="wrong@example.com", username="wronguser", password="password123")
    create_user(db_session, user_in)
    login_in = UserLogin(email="wrong@example.com", password="badpass")
    auth_user = authenticate_user(db_session, login_in)
    assert auth_user is None
