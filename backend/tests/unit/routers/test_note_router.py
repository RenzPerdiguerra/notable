from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_note_endpoint(user):
    response = client.post("/notes/", json={"user_id": user.id, "title": "My Note", "content": {"text": "Hello"}})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Note"

def test_get_note_endpoint_not_found():
    response = client.get("/notes/9999")
    assert response.status_code == 404

def test_list_notes_endpoint(user):
    response = client.get(f"/notes/?user_id={user.id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_note_endpoint(user):
    create_resp = client.post("/notes/", json={"user_id": user.id, "title": "Old", "content": {"text": "Hello"}})
    note_id = create_resp.json()["id"]
    update_resp = client.put(f"/notes/{note_id}", json={"title": "New"})
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New"

def test_delete_note_endpoint(user):
    create_resp = client.post("/notes/", json={"user_id": user.id, "title": "Delete", "content": {"text": "Bye"}})
    note_id = create_resp.json()["id"]
    delete_resp = client.delete(f"/notes/{note_id}")
    assert delete_resp.status_code == 204
