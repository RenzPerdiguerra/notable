from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.model import AI
from backend.app.schemas.ai import AIProviderCreate, AIProviderUpdate


def create_ai_provider(db: Session, ai_in: AIProviderCreate) -> AI:
    provider = AI(
        name=ai_in.name.strip(),
        provider_type=ai_in.provider_type.strip().lower(),
        model_name=ai_in.model_name.strip() if ai_in.model_name else None,
        is_active=ai_in.is_active,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def get_ai_provider(db: Session, ai_id: int) -> Optional[AI]:
    return db.query(AI).filter(AI.id == ai_id).first()


def list_ai_providers(db: Session) -> list[AI]:
    return db.query(AI).order_by(AI.id.asc()).all()


def update_ai_provider(db: Session, ai_id: int, ai_in: AIProviderUpdate) -> Optional[AI]:
    provider = get_ai_provider(db, ai_id)
    if not provider:
        return None

    if ai_in.name is not None:
        provider.name = ai_in.name.strip()
    if ai_in.provider_type is not None:
        provider.provider_type = ai_in.provider_type.strip().lower()
    if ai_in.model_name is not None:
        provider.model_name = ai_in.model_name.strip()
    if ai_in.is_active is not None:
        provider.is_active = ai_in.is_active

    db.commit()
    db.refresh(provider)
    return provider


def delete_ai_provider(db: Session, ai_id: int) -> bool:
    provider = get_ai_provider(db, ai_id)
    if not provider:
        return False

    db.delete(provider)
    db.commit()
    return True
