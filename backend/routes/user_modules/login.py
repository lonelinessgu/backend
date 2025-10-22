# routes/user_modules/login
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import timedelta
from backend.auth.user_auth import create_access_token, authenticate_user
from backend.models.users import User
import os

login_router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


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


@login_router.post(
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
        logger.info(f"User {request.login} authenticated successfully")

        try:
            expires_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))
            access_token = create_access_token(
                data={"sub": user.login, "role": user.role},
                expires_delta=timedelta(minutes=expires_minutes)
            )
        except ValueError:
            logger.error("Invalid JWT expiration configuration")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка конфигурации сервера"
            )

        response = LoginResponse(
            user=await UserOut.from_tortoise_orm(user),
            access_token=access_token
        )
        return response

    except HTTPException as e:
        logger.warning(f"Login failed for user {request.login}: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error during login for user {request.login}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )