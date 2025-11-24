import asyncio
import logging
from passlib.context import CryptContext
from backend.models.users import User as Model
from backend.models.users_roles import UserRole as RolesModel
from backend.lifespan import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Данные нового администратора
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_ROLE = "admin"  # Должно быть одним из ALLOWED_ROLES


async def create_admin():
    logger.debug("Инициализация базы данных")
    await init_db()

    try:
        logger.debug(f"Проверка существования пользователя с логином '{ADMIN_LOGIN}'")
        if await Model.filter(login=ADMIN_LOGIN).exists():
            logger.warning(f"Пользователь с логином '{ADMIN_LOGIN}' уже существует.")
            return

        logger.debug("Хеширование пароля")
        hashed_password = pwd_context.hash(ADMIN_PASSWORD)

        logger.info(f"Доступные роли: {[role.value for role in RolesModel]}")
        logger.info(f"Проверка роли '{ADMIN_ROLE}'")

        try:
            role_enum = RolesModel(ADMIN_ROLE)
            logger.debug(f"Роль '{ADMIN_ROLE}' валидна, enum значение: {role_enum}")
        except ValueError:
            logger.error(f"Недопустимая роль '{ADMIN_ROLE}'. Проверь ALLOWED_ROLES в .env")
            return

        logger.debug(f"Создание пользователя '{ADMIN_LOGIN}' с ролью '{role_enum.value}'")
        await Model.create(
            login=ADMIN_LOGIN,
            hashed_password=hashed_password,
            role=role_enum.value
        )
        logger.info(f"Администратор '{ADMIN_LOGIN}' успешно создан.")

    finally:
        logger.debug("Закрытие соединений с базой данных")
        from tortoise import Tortoise
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_admin())