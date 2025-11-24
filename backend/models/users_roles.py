# backend.models.users_roles
from enum import Enum
from functools import cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    ALLOWED_ROLES: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@cache
def _get_role_enum() -> type[Enum]:
    settings = Settings()
    logger.debug(f"Загружен ALLOWED_ROLES: {settings.ALLOWED_ROLES}")

    if not settings.ALLOWED_ROLES:
        default_roles = {"user": "user", "admin": "admin", "guest": "guest"}
        logger.warning(f"Используются стандартные роли: {list(default_roles.keys())}")
        return Enum("UserRole", default_roles, type=str)

    roles = [role.strip() for role in settings.ALLOWED_ROLES.split(",")]
    logger.debug(f"Загружены пользовательские роли: {roles}")
    return Enum("UserRole", {role: role for role in roles}, type=str)


def __getattr__(name):
    if name == 'UserRole':
        return _get_role_enum()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")