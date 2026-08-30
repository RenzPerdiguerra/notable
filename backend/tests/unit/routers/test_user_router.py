def test_list_users_endpoint(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_not_found(client):
    response = client.get("/users/9999")
    assert response.status_code == 404

def test_update_user_endpoint(client):
    create_resp = client.post("/auth/register", json={"email": "update@example.com", "username": "old", "password": "password123"})
    user_id = create_resp.json()["id"]
    update_resp = client.put(f"/users/{user_id}", json={"username": "new"})
    assert update_resp.status_code == 200
    assert update_resp.json()["username"] == "new"


def test_delete_user_endpoint(client):
    create_resp = client.post("/auth/register", json={"email": "del@example.com", "username": "deluser", "password": "password123"})
    user_id = create_resp.json()["id"]
    delete_resp = client.delete(f"/users/{user_id}")
    assert delete_resp.status_code == 204
