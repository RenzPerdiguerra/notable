from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


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
