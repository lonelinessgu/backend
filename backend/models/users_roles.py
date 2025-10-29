# backend.models.users_roles
from enum import Enum
from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    ALLOWED_ROLES: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

@cache
def _get_role_enum() -> type[Enum]:
    settings = Settings()
    if not settings.ALLOWED_ROLES:
        return Enum("UserRole", {"user": "user", "admin": "admin", "guest": "guest"}, type=str)
    roles = [role.strip() for role in settings.ALLOWED_ROLES.split(",")]
    return Enum("UserRole", {role: role for role in roles}, type=str)

# Создаем UserRole как динамический атрибут
def __getattr__(name):
    if name == 'UserRole':
        return _get_role_enum()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")