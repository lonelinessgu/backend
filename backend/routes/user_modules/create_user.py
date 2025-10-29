# backend.routes.user_modules.create_user
from fastapi import APIRouter, HTTPException, status
from pydantic import field_validator
from tortoise.contrib.pydantic import pydantic_model_creator
from backend.models.users_roles import UserRole
from backend.auth.add_users import handle_create_user_request
from backend.models.users import User
from pydantic_core import PydanticCustomError
import logging

create_user_router = APIRouter()
logger = logging.getLogger(__name__)

BaseCreateUserRequest = pydantic_model_creator(
    User,
    name="BaseCreateUserRequest",
    include=("login", "role")
)

class CreateUserRequest(BaseCreateUserRequest):
    password: str

    @field_validator('role')
    def validate_role(cls, v: str) -> UserRole:
        try:
            return UserRole(v)
        except ValueError:
            raise PydanticCustomError("value_error", "Недопустимая роль")

@create_user_router.post("/create_user",
    response_model=dict,
    responses={
        200: {"description": "Успешное создание пользователя"},
        404: {"description": "Пользователь не создан"},
        422: {"description": "Ошибки валидации"},
        500: {"description": "Ошибка сервера"}
    },
    description="""
## Создание пользователя

Эндпоинт `/create_user` реализует механизм регистрации нового пользователя.
При успешной обработке запроса создаётся запись в БД с хешированным паролем и указанной ролью.

### Тип запроса
POST

### Параметры запроса
- `login` (string): Уникальное имя пользователя.
- `password` (string): Пароль пользователя. Должен содержать минимум 8 символов.
- `role` (string): Роль пользователя. Должна соответствовать одному из допустимых значений.

### Формат запроса
```json
{
  "login": "string",
  "password": "string",
  "role": "string"
}
"""
)
async def create_user(user_data: CreateUserRequest):
    try:
        result = await handle_create_user_request(user_data.model_dump())
        logger.info(f"User created successfully: {user_data.login}")
        return result
    except HTTPException as e:
        logger.warning(f"User creation failed for {user_data.login}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Server error during user creation for {user_data.login}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сервера при создании пользователя"
        )