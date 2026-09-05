def test_register_and_login(client):
    register = client.post("/auth/register", json={
        "email": "tester@example.com",
        "username": "myownusername",
        "password": "myownpassword",
        "role": "user"
    })
    assert register.status_code == 201
    
    login = client.post("/auth/login", json={
        "email": "tester@example.com",
        "password": "myownpassword"
    })
    assert login.status_code == 200
    
    assert "access_token" in login.headers["set-cookie"]
    
    me = client.get("/users/me")
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "tester@example.com"

def test_login_wrong_password_returns_401(client, test_user):
    login = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "mywrongpassword"
    })
    assert login.status_code == 401

def test_login_nonexistent_user_returns_401(client, test_user):
    login = client.post("/auth/login", json={
        "email": "wrongtester@example.com",
        "password": "password123"
    })
    assert login.status_code == 401

def test_logout_clears_cookie(auth_client):
    logout = auth_client.post("/auth/logout")
    assert "access_token" in logout.headers["set-cookie"]
    assert "Max-Age=0" in logout.headers["set-cookie"]
    
    me = auth_client.get("/users/me")
    assert me.status_code == 401
    
def test_register_duplicate_email_returns_409(client, test_user):
    register = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    assert register.status_code == 409
    
def test_username_duplicate_username_returns_409(client, test_user):
    register = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    assert register.status_code == 409
    
def test_protected_route_without_cookie_returns_401(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    
def test_token_persist_across_requests(auth_client):
    response1 = auth_client.get("/users/me")
    response2 = auth_client.get("/users/me")
    assert response1.status_code == 200
    assert response2.status_code == 200 



