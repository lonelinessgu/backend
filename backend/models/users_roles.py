# models/users_roles
from enum import Enum
from functools import cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ALLOWED_ROLES: Optional[str] = None

    class Config:
        env_file = None  #Отключаем автоматическую загрузку из .env
        env_file_encoding = "utf-8"


@cache
def get_role_enum() -> type[Enum]:
    """
    Динамически создает и возвращает Enum класс ролей пользователей
    на основе значений из настроек.

    Кэширует результат, чтобы избежать повторного создания Enum при каждом вызове.
    """
    settings = Settings()
    roles = [role.strip() for role in settings.ALLOWED_ROLES.split(",")]
    return Enum("UserRole", {role: role for role in roles}, type=str)


UserRole = get_role_enum()