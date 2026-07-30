from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    user_id: Optional[int] = None
    title: str
    content: Any


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Any] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    content: object
    created_at: datetime
    updated_at: datetime | None = None
