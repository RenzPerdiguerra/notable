import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.models.model import User

def test_user_requires_email(db_session):
    user = User(username="testuser", hashed_password="hashed")
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_user_unique_email(db_session):
    u1 = User(email="test@example.com", username="user1", hashed_password="hashed")
    u2 = User(email="test@example.com", username="user2", hashed_password="hashed")
    db_session.add(u1)
    db_session.commit()
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
