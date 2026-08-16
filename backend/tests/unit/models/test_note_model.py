import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.models.model import Note

def test_note_requires_user_id(db_session):
    note = Note(title="Test Note", content={"text": "Hello"})
    db_session.add(note)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_note_title_required(db_session, user):
    note = Note(user_id=user.id, content={"text": "Hello"})
    db_session.add(note)
    with pytest.raises(IntegrityError):
        db_session.commit()
