# backend.lifespan
from tortoise import Tortoise
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pathlib import Path
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_DIR = Path(os.getenv("DB_DATA_DIR", Path(__file__).parents[1] / "data"))
try:
    os.makedirs(DB_DIR, exist_ok=True)
    logger.info(f"DB_DIR: {DB_DIR} (exists: {DB_DIR.exists()})")
except Exception as e:
    logger.error(f"Ошибка создания директории {DB_DIR}: {e}")

DATABASES = {
    "users": {
        "db_name": "users.db",
        "models_module": "backend.models.users",
        "connection_name": "users_connection",
        "app_name": "users_db"
    }
}

async def init_db():
    logger.info("Initializing databases...")

    connections = {}
    apps = {}

    for name, config in DATABASES.items():
        connections[config["connection_name"]] = {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": DB_DIR / config["db_name"],
                "journal_mode": "WAL",
                "synchronous": "NORMAL"
            },
        }

        apps[config["app_name"]] = {
            "models": [config["models_module"]],
            "default_connection": config["connection_name"]
        }

    try:
        await Tortoise.init({
            "connections": connections,
            "apps": apps,
        })

        logger.info("Generating database schema...")
        await Tortoise.generate_schemas(safe=True)

    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise

async def close_db(app: FastAPI):
    logger.info("Closing database connections...")
    try:
        await Tortoise.close_connections()
    except Exception as e:
        logger.error(f"Ошибка закрытия соединений: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: initializing databases")
    await init_db()
    yield
    logger.info("Shutdown: closing database connections")
    await close_db(app)