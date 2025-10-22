# auth/add_users
from fastapi import HTTPException, status
from passlib.context import CryptContext
from backend.models.users import User
from typing import Dict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(user_data: Dict) -> bool:
    """Создание нового пользователя с валидацией данных."""
    if await User.filter(login=user_data["login"]).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this login already exists"
        )

    hashed_password = pwd_context.hash(user_data["password"][:72])
    await User.create(
        login=user_data["login"],
        role=user_data["role"],
        hashed_password=hashed_password
    )
    return True

async def handle_create_user_request(user_data: Dict) -> dict:
    """
    Обработчик запроса на создание пользователя с Pydantic валидацией.
    """
    try:
        await create_user(user_data)

        return {
            "status": "created",
            "user": {
                "login": user_data["login"],
                "role": user_data["role"]
            }
        }
    except HTTPException as e:
        # Пробрасываем HTTPException как есть
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )