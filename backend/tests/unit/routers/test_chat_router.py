from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_session_endpoint(user):
    response = client.post("/chat/sessions", json={"user_id": user.id, "title": "My Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Session"

def test_get_session_not_found():
    response = client.get("/chat/sessions/9999")
    assert response.status_code == 404

def test_update_session_endpoint(user):
    create_resp = client.post("/chat/sessions", json={"user_id": user.id, "title": "Old"})
    session_id = create_resp.json()["id"]
    update_resp = client.put(f"/chat/sessions/{session_id}", json={"title": "New"})
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New"

def test_delete_session_endpoint(user):
    create_resp = client.post("/chat/sessions", json={"user_id": user.id, "title": "Delete"})
    session_id = create_resp.json()["id"]
    delete_resp = client.delete(f"/chat/sessions/{session_id}")
    assert delete_resp.status_code == 204

def test_create_message_endpoint(user):
    create_resp = client.post("/chat/sessions", json={"user_id": user.id, "title": "Chat"})
    session_id = create_resp.json()["id"]
    msg_resp = client.post("/chat/messages", json={"session_id": session_id, "role": "user", "content": "Hello"})
    assert msg_resp.status_code == 201
    assert msg_resp.json()["content"] == "Hello"

def test_list_messages_endpoint(user):
    create_resp = client.post("/chat/sessions", json={"user_id": user.id, "title": "Chat"})
    session_id = create_resp.json()["id"]
    client.post("/chat/messages", json={"session_id": session_id, "role": "user", "content": "First"})
    list_resp = client.get(f"/chat/messages/{session_id}")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)
    assert list_resp.json()[0]["content"] == "First"
