# backend.auth.create_admin_user
import asyncio
from dotenv import load_dotenv
from passlib.context import CryptContext
from backend.models.users import User
from backend.models.users_roles import UserRole
from backend.lifespan import init_db  # Используем твою функцию инициализации

# Загружаем переменные окружения
load_dotenv()

# Инициализируем контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Данные нового администратора
ADMIN_LOGIN = "administrator"
ADMIN_PASSWORD = "administrator"
ADMIN_ROLE = "administrator"  # Должно быть одним из ALLOWED_ROLES


async def create_admin():
    # Инициализация БД
    await init_db()

    try:
        # Проверка, существует ли уже пользователь с таким логином
        if await User.filter(login=ADMIN_LOGIN).exists():
            print(f"[!] Пользователь с логином '{ADMIN_LOGIN}' уже существует.")
            return

        # Хешируем пароль
        hashed_password = pwd_context.hash(ADMIN_PASSWORD)

        # Проверяем, что роль допустима
        try:
            role_enum = UserRole(ADMIN_ROLE)
        except ValueError:
            print(f"[!] Недопустимая роль '{ADMIN_ROLE}'. Проверь ALLOWED_ROLES в .env")
            return

        # Создаём пользователя
        await User.create(
            login=ADMIN_LOGIN,
            hashed_password=hashed_password,
            role=role_enum.value
        )
        print(f"[+] Администратор '{ADMIN_LOGIN}' успешно создан.")

    finally:
        # Закрываем соединения с БД
        from tortoise import Tortoise
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_admin())