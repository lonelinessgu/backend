import requests

# URL твоего FastAPI сервера
url = "http://127.0.0.1:8000/login"

# Данные для регистрации
payload = {
    "login": "john_doe",
    "password": "securepassword123",
}

# Отправка POST-запроса
response = requests.post(url, json=payload)

# Вывод ответа
print("Status Code:", response.status_code)
print("Response Body:", response.json())