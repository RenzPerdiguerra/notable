def test_register_user_success(db_session, client):
    response = client.post("/auth/register", json={
        "email": "auth@example.com",
        "username": "authuser",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "auth@example.com"

def test_register_user_duplicate_email(db_session, client):
    client.post("/auth/register", json={
        "email": "dup@example.com",
        "username": "user1",
        "password": "password123"
    })
    response = client.post("/auth/register", json={
        "email": "dup@example.com",
        "username": "user2",
        "password": "password123"
    })
    assert response.status_code == 400

def test_login_success(db_session, client):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "login successful"
    assert "user" in data

def test_login_invalid_credentials(db_session, client):
    response = client.post("/auth/login", json={
        "email": "fake@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401

def test_logout_clears_cookie(client):
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "logout successful"
