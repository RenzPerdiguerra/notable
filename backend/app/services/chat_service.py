from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.model import ChatMessage, ChatSession
from backend.app.schemas.chat import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate


def create_chat_session(db: Session, session_in: ChatSessionCreate) -> ChatSession:
    session = ChatSession(
        user_id=session_in.user_id,
        note_id=session_in.note_id,
        ai_id=session_in.ai_id,
        title=session_in.title.strip() if session_in.title else None,
        expires_at=session_in.expires_at,
        is_active=True,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_session(db: Session, session_id: int) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def list_chat_sessions(db: Session, user_id: Optional[int] = None) -> list[ChatSession]:
    query = db.query(ChatSession)
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    return query.order_by(ChatSession.created_at.desc()).all()


def update_chat_session(db: Session, session_id: int, session_in: ChatSessionUpdate) -> Optional[ChatSession]:
    session = get_chat_session(db, session_id)
    if not session:
        return None

    if session_in.title is not None:
        session.title = session_in.title.strip()
    if session_in.expires_at is not None:
        session.expires_at = session_in.expires_at
    if session_in.is_active is not None:
        session.is_active = session_in.is_active

    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def delete_chat_session(db: Session, session_id: int) -> bool:
    session = get_chat_session(db, session_id)
    if not session:
        return False

    db.delete(session)
    db.commit()
    return True


def add_chat_message(db: Session, message_in: ChatMessageCreate) -> ChatMessage:
    message = ChatMessage(
        session_id=message_in.session_id,
        role=message_in.role.strip().lower(),
        content=message_in.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_chat_messages(db: Session, session_id: int) -> list[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
