import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.models.model import ChatSession, ChatMessage

def test_chat_session_requires_user_id(db_session):
    session = ChatSession(title="Test Session")
    db_session.add(session)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_chat_message_requires_role_and_content(db_session, chat_session):
    msg = ChatMessage(session_id=chat_session.id, role=None, content=None)
    db_session.add(msg)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_chat_session_relationship_with_messages(db_session, chat_session):
    msg = ChatMessage(session_id=chat_session.id, role="user", content="Hello")
    db_session.add(msg)
    db_session.commit()
    assert chat_session.messages[0].content == "Hello"
