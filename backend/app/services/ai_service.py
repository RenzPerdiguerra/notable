import json
import logging
from typing import Literal, Optional

import httpx
from sqlalchemy.orm import Session
from backend.app.models.model import AI, Note
from backend.app.schemas.ai import AIProviderCreate, AIProviderUpdate

logger = logging.getLogger(__name__)

class AIConfigurationError(Exception):
    pass


class AIProviderError(Exception):
    pass


def _build_prompt(action: str, note: Note, question: Optional[str]) -> str:
    content = note.content
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    instructions = {
        "summarize": "Summarize the note clearly, preserving its key facts and decisions.",
        "questions": "Generate a short list of useful questions based on the note.",
        "enhance": "Improve the wording and organization of the note without changing its meaning.",
        "ask": f"Answer the user's question using the note as context. Question: {question or ''}",
    }
    return (
        f"{instructions[action]}\n\n"
        f"Note title: {note.title}\n"
        f"Note content:\n{content}"
    )


def _request_gemini(prompt: str, config) -> str:
    if not config.GEMINI_API_KEY:
        raise AIConfigurationError("GEMINI_API_KEY is not configured in the backend environment")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent"
    )
    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": config.GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gemini returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text[:400],
        )
        raise AIProviderError(
            f"Gemini rejected the request. Please contact your service provider."
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Gemini transport error (%s): %s", type(exc).__name__, exc)
        raise AIProviderError("Could not connect to Gemini; check backend logs and outbound network access") from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.exception("Gemini returned an unexpected response format")
        raise AIProviderError("Gemini returned an unexpected response; check backend logs") from exc


def _request_groq(prompt: str, config) -> str:
    if not config.GROQ_API_KEY:
        raise AIConfigurationError("GROQ_TOKEN is not configured in the backend environment")

    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json={
                "model": config.GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Groq returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text[:1000],
        )
        raise AIProviderError(
            f"Groq rejected the request. Please contact your service provider."
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Groq transport error (%s): %s", type(exc).__name__, exc)
        raise AIProviderError(
            "Could not connect to Groq; check backend logs and outbound network access"
        ) from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.exception("Groq returned an unexpected response format")
        raise AIProviderError("Groq returned an unexpected response; check backend logs") from exc


def generate_note_response(
    db: Session,
    *,
    note_id: int,
    user_id: int,
    provider: Literal["gemini", "groq"],
    action: Literal["summarize", "questions", "enhance", "ask"],
    question: Optional[str] = None,
) -> str:
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == user_id).first()
    if note is None:
        raise LookupError("Note not found")

    prompt = _build_prompt(action, note, question)
    from backend.app.core.config import get_config

    config = get_config()
    if provider == "gemini":
        return _request_gemini(prompt, config)
    return _request_groq(prompt, config)


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
