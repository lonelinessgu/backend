from fastapi import HTTPException, status
from passlib.context import CryptContext
from tortoise.contrib.pydantic import pydantic_model_creator
from backend.models.users import User
from backend.models.users_roles import UserRole
from typing import Dict, Any
from pydantic import field_validator, ConfigDict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создаем Pydantic модель для создания пользователя
UserCreate = pydantic_model_creator(
    User,
    name="BaseUserCreate",
    exclude=("id", "status", "hashed_password"),
    exclude_readonly=True,
)

# Дополняем модель валидацией
class UserCreateRequest(UserCreate):
    password: str  # Добавляем поле для пароля
    model_config = ConfigDict(extra='forbid')

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Any) -> str:
        """Валидатор для проверки допустимых значений роли"""
        try:
            role_enum = UserRole(v)
            return role_enum.value
        except ValueError:
            raise ValueError(f"Недопустимая роль")

async def create_user(user_data: UserCreateRequest) -> bool:
    """Создание нового пользователя с валидацией данных."""
    if await User.filter(login=user_data.login).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this login already exists"
        )

    hashed_password = pwd_context.hash(user_data.password)
    await User.create(
        **user_data.model_dump(exclude={"password"}),
        hashed_password=hashed_password
    )
    return True

async def handle_create_user_request(user_data: Dict) -> dict:
    """
    Обработчик запроса на создание пользователя с Pydantic валидацией.
    """
    try:
        # Валидация входных данных
        user_request = UserCreateRequest(**user_data)

        # Создание пользователя
        await create_user(user_request)

        return {
            "status": "created",
            "user": user_request.model_dump(exclude={"password"})
        }
    except HTTPException as e:
        # Пробрасываем HTTPException как есть
        raise e
    except ValueError as e:
        # Ошибки валидации Pydantic
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Все остальные ошибки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )