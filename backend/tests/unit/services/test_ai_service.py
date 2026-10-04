from types import SimpleNamespace

import httpx
import pytest

from backend.app.services.ai_service import (
    AIConfigurationError,
    create_ai_provider,
    delete_ai_provider,
    generate_note_response,
    get_ai_provider,
    update_ai_provider,
)
from backend.app.schemas.ai import AIProviderCreate, AIProviderUpdate
from backend.app.schemas.note import NoteCreate
from backend.app.services.note_service import create_note

def test_create_ai_provider(db_session):
    ai_in = AIProviderCreate(name="Gemini", provider_type="gemini")
    provider = create_ai_provider(db_session, ai_in)
    assert provider.id is not None
    assert provider.name == "Gemini"

def test_update_ai_provider(db_session):
    ai_in = AIProviderCreate(name="Gemini", provider_type="gemini")
    provider = create_ai_provider(db_session, ai_in)

    update_in = AIProviderUpdate(name="Gemini Pro")
    updated = update_ai_provider(db_session, provider.id, update_in)
    assert updated.name == "Gemini Pro"

def test_delete_ai_provider(db_session):
    ai_in = AIProviderCreate(name="Gemini", provider_type="gemini")
    provider = create_ai_provider(db_session, ai_in)

    success = delete_ai_provider(db_session, provider.id)
    assert success
    assert get_ai_provider(db_session, provider.id) is None


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_generate_gemini_response_uses_api_key_header(db_session, user, monkeypatch):
    note = create_note(
        db_session,
        NoteCreate(title="Study notes", content={"text": "Photosynthesis"}),
        user_id=user.id,
    )
    config = SimpleNamespace(
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="test-model",
        GROQ_API_KEY=None,
        GROQ_MODEL="test-groq-model",
    )
    monkeypatch.setattr("backend.app.core.config.get_config", lambda: config)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse({
            "candidates": [{"content": {"parts": [{"text": "Plant food production"}]}}]
        })

    monkeypatch.setattr(httpx, "post", fake_post)
    result = generate_note_response(
        db_session,
        note_id=note.id,
        user_id=user.id,
        provider="gemini",
        action="summarize",
    )

    assert result == "Plant food production"
    assert captured["headers"]["x-goog-api-key"] == "test-gemini-key"
    assert "test-gemini-key" not in captured["url"]
    assert "Photosynthesis" in captured["json"]["contents"][0]["parts"][0]["text"]


def test_generate_groq_response_uses_chat_completion(db_session, user, monkeypatch):
    note = create_note(
        db_session,
        NoteCreate(title="Study notes", content="Photosynthesis"),
        user_id=user.id,
    )
    config = SimpleNamespace(
        GEMINI_API_KEY=None,
        GEMINI_MODEL="test-model",
        GROQ_API_KEY="test-groq-api-key",
        GROQ_MODEL="test-groq-model",
    )
    monkeypatch.setattr("backend.app.core.config.get_config", lambda: config)
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse({
            "choices": [{"message": {"content": "Generated questions"}}]
        })

    monkeypatch.setattr(httpx, "post", fake_post)
    result = generate_note_response(
        db_session,
        note_id=note.id,
        user_id=user.id,
        provider="groq",
        action="questions",
    )

    assert result == "Generated questions"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-groq-api-key"
    assert captured["json"]["model"] == "test-groq-model"


def test_generate_response_denies_other_users_note_before_provider_call(
    db_session, user, monkeypatch
):
    note = create_note(
        db_session,
        NoteCreate(title="Private", content="Private content"),
        user_id=user.id,
    )
    config = SimpleNamespace(GEMINI_API_KEY="test-key", GEMINI_MODEL="test-model")
    monkeypatch.setattr("backend.app.core.config.get_config", lambda: config)
    provider_called = False

    def unexpected_post(*args, **kwargs):
        nonlocal provider_called
        provider_called = True
        raise AssertionError("Provider must not receive another user's note")

    monkeypatch.setattr(httpx, "post", unexpected_post)
    with pytest.raises(LookupError, match="Note not found"):
        generate_note_response(
            db_session,
            note_id=note.id,
            user_id=user.id + 1,
            provider="gemini",
            action="summarize",
        )
    assert not provider_called


def test_generate_response_requires_provider_key(db_session, user, monkeypatch):
    note = create_note(
        db_session,
        NoteCreate(title="Study notes", content="Photosynthesis"),
        user_id=user.id,
    )
    config = SimpleNamespace(GEMINI_API_KEY=None, GEMINI_MODEL="test-model")
    monkeypatch.setattr("backend.app.core.config.get_config", lambda: config)

    with pytest.raises(AIConfigurationError, match="GEMINI_API_KEY"):
        generate_note_response(
            db_session,
            note_id=note.id,
            user_id=user.id,
            provider="gemini",
            action="summarize",
        )
