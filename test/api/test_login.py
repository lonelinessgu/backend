# test.api.login
from fastapi.testclient import TestClient
from backend.main import app
import pytest
from uuid import uuid4

def get_unique_login():
    """Генерирует уникальный логин для тестов"""
    return f"testuser_{uuid4().hex[:8]}"

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

def test_login_success(client):
    login = get_unique_login()
    create_payload = {
        "login": login,
        "password": "ByPass777",
        "role": "user"
    }
    create_response = client.post("/api/create_user", json=create_payload)
    assert create_response.status_code == 200

    # Login
    login_payload = {
        "login": login,
        "password": "ByPass777"
    }
    login_response = client.post("/api/login", json=login_payload)

    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["login"] == login

def test_login_invalid_credentials(client):
    login_payload = {
        "login": get_unique_login(),
        "password": "wrong_password"
    }
    response = client.post("/api/login", json=login_payload)

    assert response.status_code == 401

