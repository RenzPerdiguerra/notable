from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChatSessionCreate(BaseModel):
    user_id: int
    note_id: Optional[int] = None
    ai_id: Optional[int] = None
    title: Optional[str] = None
    expires_at: Optional[datetime] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    note_id: Optional[int] = None
    ai_id: Optional[int] = None
    title: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class ChatMessageCreate(BaseModel):
    session_id: int
    role: str
    content: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
