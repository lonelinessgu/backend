#backend\lifespan.py
from tortoise import Tortoise
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Автоматически вычисляет родительскую директорию и следует из неё в data, так же можно задать искомую директорию через .env файл
DB_DIR = Path(os.getenv("DB_DATA_DIR", Path(__file__).parents[1] / "data"))
try:
    os.makedirs(DB_DIR, exist_ok=True)
    logger.info(f"DB_DIR: {DB_DIR} (exists: {DB_DIR.exists()})")
except Exception as e:
    logger.error(f"Ошибка создания директории {DB_DIR}: {e}")

async def init_db():
    logger.info("Инициализация db...")

    try:
        await Tortoise.init(
            {
                "connections": {
                    "users_connection": {
                        "engine": "tortoise.backends.sqlite",
                        "credentials": {
                            "file_path": DB_DIR / "users.db",
                            "journal_mode": "WAL", #Позволяет работать параллельно с записью и чтением
                            "synchronous": "NORMAL" #Устанавливает насколько агрессивно записывать изменения из буфера в физический файл БД
                        },
                    },
                },
                "apps": {
                    # База данных пользователей
                    "users_db": {
                        "models": ["backend.models.users"],
                        "default_connection": "users_connection"
                    },
                },
            }
        )

        logger.info("Создание схем баз данных...")
        await Tortoise.generate_schemas(safe=True)

    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise

async def close_db(app: FastAPI):
    logger.info("Закрытие подключения к db...")
    try:
        await Tortoise.close_connections()
    except Exception as e:
        logger.error(f"Ошибка закрытия соединений: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Инициализация db")
    await init_db()
    yield
    logger.info("Shutdown: Закрытие подключения к db")
    await close_db(app)