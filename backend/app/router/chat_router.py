from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.schemas.chat import ChatMessageCreate, ChatMessageOut, ChatSessionCreate, ChatSessionOut, ChatSessionUpdate
from backend.app.services.chat_service import add_chat_message, create_chat_session, delete_chat_session, get_chat_session, list_chat_messages, list_chat_sessions, update_chat_session

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(session_in: ChatSessionCreate, db: Session = Depends(get_db)):
    return create_chat_session(db=db, session_in=session_in)


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_sessions(user_id: int | None = None, db: Session = Depends(get_db)):
    return list_chat_sessions(db=db, user_id=user_id)


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = get_chat_session(db=db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.put("/sessions/{session_id}", response_model=ChatSessionOut)
def update_session(session_id: int, session_in: ChatSessionUpdate, db: Session = Depends(get_db)):
    session = update_chat_session(db=db, session_id=session_id, session_in=session_in)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    success = delete_chat_session(db=db, session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return None


@router.post("/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def create_message(message_in: ChatMessageCreate, db: Session = Depends(get_db)):
    return add_chat_message(db=db, message_in=message_in)


@router.get("/messages/{session_id}", response_model=list[ChatMessageOut])
def list_messages(session_id: int, db: Session = Depends(get_db)):
    return list_chat_messages(db=db, session_id=session_id)
