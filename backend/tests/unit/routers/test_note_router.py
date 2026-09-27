def test_create_note_endpoint(user, auth_client):
    response = auth_client.post("/notes/", json={"title": "My Note", "content": {"text": "Hello"}})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Note"
    assert data["user_id"] == user.id

def test_note_endpoints_require_authentication(client):
    assert client.get("/notes/").status_code == 401
    assert client.get("/notes/9999").status_code == 401
    assert client.post("/notes/", json={"title": "Note", "content": "Body"}).status_code == 401
    assert client.put("/notes/1", json={"title": "Changed"}).status_code == 401
    assert client.delete("/notes/1").status_code == 401

def test_get_note_endpoint_not_found(auth_client):
    response = auth_client.get("/notes/9999")
    assert response.status_code == 404

def test_list_notes_endpoint(user, auth_client):
    response = auth_client.get("/notes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(note["user_id"] == user.id for note in response.json())

def test_update_note_endpoint(user, auth_client):
    create_resp = auth_client.post("/notes/", json={"title": "Old", "content": {"text": "Hello"}})
    note_id = create_resp.json()["id"]
    update_resp = auth_client.put(f"/notes/{note_id}", json={"title": "New"})
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New"

def test_delete_note_endpoint(user, auth_client):
    create_resp = auth_client.post("/notes/", json={"title": "Delete", "content": {"text": "Bye"}})
    note_id = create_resp.json()["id"]
    delete_resp = auth_client.delete(f"/notes/{note_id}")
    assert delete_resp.status_code == 204

def test_user_cannot_access_another_users_notes(db_session, user, auth_client):
    from backend.app.schemas.user import UserCreate
    from backend.app.services.user_service import create_user

    owned_note = auth_client.post("/notes/", json={
        "title": "Private note",
        "content": {"text": "Only the owner should see this"},
    })
    assert owned_note.status_code == 201
    note_id = owned_note.json()["id"]

    other_user = create_user(db_session, UserCreate(
        email="other-owner@example.com",
        username="otherowner",
        password="password123",
    ))
    auth_client.post("/auth/logout")
    login = auth_client.post("/auth/login", json={
        "email": "other-owner@example.com",
        "password": "password123",
    })
    assert login.status_code == 200

    listed = auth_client.get(f"/notes/?user_id={user.id}")
    assert listed.status_code == 200
    assert all(note["user_id"] == other_user.id for note in listed.json())
    assert auth_client.get(f"/notes/{note_id}").status_code == 404
    assert auth_client.put(f"/notes/{note_id}", json={"title": "Stolen"}).status_code == 404
    assert auth_client.delete(f"/notes/{note_id}").status_code == 404
