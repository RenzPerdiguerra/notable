import pytest
from datetime import datetime, timedelta
from backend.app.services.chat_service import (
    create_chat_session, get_chat_session, list_chat_sessions,
    update_chat_session, delete_chat_session,
    add_chat_message, list_chat_messages
)
from backend.app.schemas.chat import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate

def test_create_chat_session(db_session, user):
    session_in = ChatSessionCreate(user_id=user.id, title="My Session")
    session = create_chat_session(db_session, session_in)
    assert session.id is not None
    assert session.title == "My Session"

def test_update_chat_session(db_session, user):
    session_in = ChatSessionCreate(user_id=user.id, title="Old Title")
    session = create_chat_session(db_session, session_in)
    update_in = ChatSessionUpdate(title="New Title", is_active=False)
    updated = update_chat_session(db_session, session.id, update_in)
    assert updated.title == "New Title"
    assert updated.is_active is False
    assert updated.updated_at is not None

def test_delete_chat_session(db_session, user):
    session_in = ChatSessionCreate(user_id=user.id, title="Delete Me")
    session = create_chat_session(db_session, session_in)
    success = delete_chat_session(db_session, session.id)
    assert success
    assert get_chat_session(db_session, session.id) is None

def test_add_chat_message(db_session, user):
    session_in = ChatSessionCreate(user_id=user.id, title="Chat")
    session = create_chat_session(db_session, session_in)
    msg_in = ChatMessageCreate(session_id=session.id, role="User", content="Hello")
    msg = add_chat_message(db_session, msg_in)
    assert msg.role == "user"  # lowercased
    assert msg.content == "Hello"

def test_list_chat_messages(db_session, user):
    session_in = ChatSessionCreate(user_id=user.id, title="Chat")
    session = create_chat_session(db_session, session_in)
    msg_in = ChatMessageCreate(session_id=session.id, role="user", content="First")
    add_chat_message(db_session, msg_in)
    msgs = list_chat_messages(db_session, session.id)
    assert len(msgs) == 1
    assert msgs[0].content == "First"
