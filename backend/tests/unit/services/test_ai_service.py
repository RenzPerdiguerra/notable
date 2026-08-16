from backend.app.services.ai_service import create_ai_provider, get_ai_provider, update_ai_provider, delete_ai_provider
from backend.app.schemas.ai import AIProviderCreate, AIProviderUpdate

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
