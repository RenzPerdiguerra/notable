from sqlalchemy.orm import Session
from backend.app.models.model import User
from backend.app.db import SessionLocal

def seed_dev_user(db: Session):
    user_exists = db.query(User).filter(User.email == "test@example.com").first()
    if user_exists:
        return user_exists

    dev_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$SbHDyIMWL80bJu7Tsew9t.9LFwyflQQFJ1BHWePaRRKSxQccsYhIy",
        role="user",
    )
    db.add(dev_user)
    db.commit()
    db.refresh(dev_user)
    return dev_user


if __name__ == "__main__":
    with SessionLocal() as db_session:
        user = seed_dev_user(db_session)
        print(f"Seeded user: {user.email} (id={user.id})")
        
# uv run python -c "from passlib.context import CryptContext;
# pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto');
# password = 'mayday09'[:72]; print(pwd_context.hash(password))"
# bcrypt 4.0.1
# passlib 1.7.4