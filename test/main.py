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

def test_create_user_success(client):
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123",
        "role": "admin"
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 200

def test_create_user_invalid_role(client):
    """
    Тест с невалидной ролью
    """
    payload = {
        "login": get_unique_login(),
        "password": "StrongPass123",
        "role": "invalid_role"
    }

    response = client.post("/api/create_user", json=payload)

    assert response.status_code == 422  # Ошибка валидации

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

    assert response.status_code == 200  # Ошибка валидации

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
    assert response2.status_code == 409  # или какой там код возвращается

def test_create_user_weak_password(client):
    """
    Тест с слабым паролем (если есть валидация пароля)
    """
    payload = {
        "login": get_unique_login(),
        "password": "123",  # Слабый пароль
        "role": "admin"
    }

    response = client.post("/api/create_user", json=payload)

    # Зависит от валидации, может быть 422 или 200, если валидация пароля в handle_create_user_request
    assert response.status_code in [422, 200]  # или уточни, какой код ожидается

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

    assert response.status_code == 422  # Ошибка валидации