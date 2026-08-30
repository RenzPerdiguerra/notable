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
