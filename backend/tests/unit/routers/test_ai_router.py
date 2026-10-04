def test_create_provider(client):
    response = client.post("/ai/providers", json={"name": "Gemini", "provider_type": "gemini"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gemini"

def test_list_providers(client):
    response = client.get("/ai/providers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_provider_not_found(client):
    response = client.get("/ai/providers/9999")
    assert response.status_code == 404


def test_ai_action_requires_authentication(client):
    response = client.post("/ai/summarize", json={
        "note_id": 1,
        "provider": "gemini",
    })
    assert response.status_code == 401


def test_summarize_note_returns_provider_result(auth_client, user, monkeypatch):
    note_response = auth_client.post("/notes/", json={
        "title": "Test note",
        "content": {"text": "A note to summarize"},
    })
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]

    def fake_generate(db, *, note_id, user_id, provider, action, question=None):
        assert user_id == user.id
        assert provider == "gemini"
        assert action == "summarize"
        return "Summary text"

    monkeypatch.setattr(
        "backend.app.routers.ai_router.generate_note_response",
        fake_generate,
    )
    response = auth_client.post("/ai/summarize", json={
        "note_id": note_id,
        "provider": "gemini",
    })

    assert response.status_code == 200
    assert response.json() == {
        "result": "Summary text",
        "provider": "gemini",
        "action": "summarize",
    }


def test_ai_action_cannot_access_another_users_note(db_session, auth_client):
    from backend.app.schemas.user import UserCreate
    from backend.app.services.user_service import create_user

    note_response = auth_client.post("/notes/", json={
        "title": "Private note",
        "content": {"text": "Private content"},
    })
    note_id = note_response.json()["id"]
    create_user(db_session, UserCreate(
        email="ai-other@example.com",
        username="aiother",
        password="password123",
    ))
    auth_client.post("/auth/logout")
    login = auth_client.post("/auth/login", json={
        "email": "ai-other@example.com",
        "password": "password123",
    })
    assert login.status_code == 200
    assert auth_client.get("/users/me").json()["email"] == "ai-other@example.com"
    assert note_response.json()["user_id"] != login.json()["user"]["id"]

    response = auth_client.post("/ai/summarize", json={
        "note_id": note_id,
        "provider": "gemini",
    })

    assert response.status_code == 404
