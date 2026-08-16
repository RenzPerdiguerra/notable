import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.models.model import AI

def test_ai_provider_unique_name(db_session):
    ai1 = AI(name="Gemini", provider_type="gemini")
    ai2 = AI(name="Gemini", provider_type="gemini")
    db_session.add(ai1)
    db_session.commit()

    db_session.add(ai2)
    with pytest.raises(IntegrityError):
        db_session.commit()
