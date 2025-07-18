from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import timedelta
from backend.auth.auth import create_access_token, authenticate_user
from backend.models.users import User
import os

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    login: str
    password: str


UserOut = pydantic_model_creator(
    User,
    name="UserOut",
    include=("login", "role")
)


class LoginResponse(BaseModel):
    user: UserOut
    access_token: str
    token_type: str = "bearer"
    message: str = "Успешная авторизация"


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {"description": "Успешная авторизация"},
        401: {"description": "Неверные учетные данные"},
        404: {"description": "Пользователь не найден"},
        422: {"description": "Ошибки валидации"},
        500: {"description": "Ошибка сервера"}
    },
    description="""
## Авторизация пользователя

Эндпоинт `/login` реализует механизм аутентификации пользователя по логину и паролю.
В случае успешной аутентификации возвращается JWT-токен и данные пользователя.

### Тип запроса
POST

### Параметры запроса
- `login` (string): Логин пользователя.
- `password` (string): Пароль пользователя.

### Формат запроса
```json
{
  "login": "string",
  "password": "string"
}
"""
)
async def login(request: LoginRequest):
    try:
        user = await authenticate_user(request.login, request.password)

        # Создание токена
        try:
            expires_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))
            access_token = create_access_token(
                data={"sub": user.login, "role": user.role},
                expires_delta=timedelta(minutes=expires_minutes)
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка конфигурации сервера"
            )

        return LoginResponse(
            user=await UserOut.from_tortoise_orm(user),
            access_token=access_token
        )

    except HTTPException as e:
        raise e  # Пробрасываем HTTPException

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )