from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.auth_dependencies import get_current_user
from backend.app.db import get_db
from backend.app.models.model import User
from backend.app.schemas.ai import (
  AIActionResponse,
  AINoteActionRequest,
  AIProviderCreate,
  AIProviderOut,
  AIProviderUpdate,
)
from backend.app.services.ai_service import (
  AIConfigurationError,
  AIProviderError,
  create_ai_provider,
  delete_ai_provider,
  generate_note_response,
  get_ai_provider,
  list_ai_providers,
  update_ai_provider,
)

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

def _run_note_action(
  action: str,
  request: AINoteActionRequest,
  db: Session,
  current_user: User,
) -> AIActionResponse:
  if action == "ask" and not (request.question and request.question.strip()):
    raise HTTPException(status_code=422, detail="A question is required for this action")

  try:
    result = generate_note_response(
      db,
      note_id=request.note_id,
      user_id=current_user.id,
      provider=request.provider,
      action=action,
      question=request.question,
    )
  except LookupError as exc:
    raise HTTPException(status_code=404, detail="Note not found") from exc
  except AIConfigurationError as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc
  except AIProviderError as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc

  return AIActionResponse(result=result, provider=request.provider, action=action)


@router.post("/summarize", response_model=AIActionResponse)
def summarize_note(
  request: AINoteActionRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  return _run_note_action("summarize", request, db, current_user)


@router.post("/questions", response_model=AIActionResponse)
def generate_questions(
  request: AINoteActionRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  return _run_note_action("questions", request, db, current_user)


@router.post("/enhance", response_model=AIActionResponse)
def enhance_note(
  request: AINoteActionRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  return _run_note_action("enhance", request, db, current_user)


@router.post("/ask", response_model=AIActionResponse)
def ask_about_note(
  request: AINoteActionRequest,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  return _run_note_action("ask", request, db, current_user)