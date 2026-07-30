from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.schemas.ai import AIProviderCreate, AIProviderOut, AIProviderUpdate
from backend.app.services.ai_service import create_ai_provider, delete_ai_provider, get_ai_provider, list_ai_providers, update_ai_provider

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/providers", response_model=AIProviderOut, status_code=status.HTTP_201_CREATED)
def create_provider(ai_in: AIProviderCreate, db: Session = Depends(get_db)):
    return create_ai_provider(db=db, ai_in=ai_in)


@router.get("/providers", response_model=list[AIProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return list_ai_providers(db=db)


@router.get("/providers/{ai_id}", response_model=AIProviderOut)
def get_provider(ai_id: int, db: Session = Depends(get_db)):
    provider = get_ai_provider(db=db, ai_id=ai_id)
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found")
    return provider


@router.put("/providers/{ai_id}", response_model=AIProviderOut)
def update_provider(ai_id: int, ai_in: AIProviderUpdate, db: Session = Depends(get_db)):
    provider = update_ai_provider(db=db, ai_id=ai_id, ai_in=ai_in)
    if not provider:
        raise HTTPException(status_code=404, detail="AI provider not found")
    return provider


@router.delete("/providers/{ai_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(ai_id: int, db: Session = Depends(get_db)):
    success = delete_ai_provider(db=db, ai_id=ai_id)
    if not success:
        raise HTTPException(status_code=404, detail="AI provider not found")
    return None
