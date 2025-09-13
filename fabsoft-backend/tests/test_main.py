from fastapi.testclient import TestClient
from app import schemas

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo à API SlamTalk 0.2.0!"}

def test_create_user(client: TestClient):
    response = client.post(
        "/usuarios/",
        json={"username": "testuser", "email": "test@example.com", "senha": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login(client: TestClient):
    # Cria um usuário para o teste de login
    client.post(
        "/usuarios/",
        json={"username": "logintest", "email": "login@example.com", "senha": "password123"},
    )
    
    login_response = client.post(
        "/usuarios/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_read_users_me(client: TestClient, test_user_token_headers: dict):
    # A fixture 'test_user_token_headers' já cria um usuário e nos dá o cabeçalho
    profile_response = client.get("/usuarios/me", headers=test_user_token_headers)
    
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == "fixture@example.com"