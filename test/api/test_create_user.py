# test.api.create_user
from fastapi.testclient import TestClient
from backend.main import app
import pytest
import uuid

def get_unique_login():
    """Генерирует уникальный логин для тестов"""
    return f"testuser_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

def test_create_admin_success(client):
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123",
        "role": "admin"
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 200

def test_create_user_success(client):
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123",
        "role": "user"
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 200

@pytest.mark.parametrize("invalid_role", ["", "123", "hacker", "root"])
def test_create_user_invalid_roles(client, invalid_role):
    """
    Параметризованный тест с невалидными ролями
    """
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123",
        "role": invalid_role
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 422

def test_create_user_missing_fields(client):
    """
    Тест с отсутствующими полями
    """
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123"
        # role отсутствует
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 200 # роль автоматически ставится на user


def test_create_user_duplicate_login(client):
    """
    Тест на создание пользователя с уже существующим логином
    """
    login = get_unique_login()
    payload = {
        "login": login,
        "password": "StrongPass123",
        "role": "user"
    }

    # Создаём первого пользователя
    response1 = client.post("/api/create_user", json=payload)
    assert response1.status_code == 200

    # Пытаемся создать второго с тем же логином
    response2 = client.post("/api/create_user", json=payload)
    assert response2.status_code == 409

def test_create_user_with_empty_fields(client):
    """
    Тест с пустыми полями
    """
    payload = {
        "login": "",
        "password": "",
        "role": ""
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 422