from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class AINoteActionRequest(BaseModel):
    note_id: int
    provider: Literal["gemini", "groq"] = "gemini"
    question: Optional[str] = None


class AIActionResponse(BaseModel):
    result: str
    provider: Literal["gemini", "groq"]
    action: Literal["summarize", "questions", "enhance", "ask"]


class AIProviderCreate(BaseModel):
    name: str
    provider_type: str
    model_name: Optional[str] = None
    is_active: bool = True


class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    model_name: Optional[str] = None
    is_active: Optional[bool] = None


class AIProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: str
    model_name: Optional[str] = None
    is_active: bool
