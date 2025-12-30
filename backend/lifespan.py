from tortoise import Tortoise
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.utils.rate_limiter import get_redis
import logging
import os

logger = logging.getLogger(__name__)

DATABASES_CONFIG = {
    "users": {
        "connection_name": "users_connection",
        "app_name": "users",
        "models_module": "backend.models.users",
        "database": "users"
    }
}


async def init_db():
    logger.info("Initializing PostgreSQL databases...")

    # Проверяем обязательные переменные окружения
    host = os.getenv("POSTGRES_HOST")
    port_str = os.getenv("POSTGRES_PORT")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    if not all([host, port_str, user, password]):
        missing = [name for name, value in
                  [("POSTGRES_HOST", host), ("POSTGRES_PORT", port_str),
                   ("POSTGRES_USER", user), ("POSTGRES_PASSWORD", password)]
                  if not value]
        raise ValueError(f"Missing required environment variables: {missing}")

    try:
        port = int(port_str)
    except ValueError:
        raise ValueError(f"Invalid POSTGRES_PORT value: {port_str}")

    connections = {}
    apps = {}

    for name, config in DATABASES_CONFIG.items():
        connections[config["connection_name"]] = {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": config["database"],
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
        logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


async def close_db(app: FastAPI):
    logger.info("Closing database connections...")
    try:
        await Tortoise.close_connections()
    except Exception as e:
        logger.error(f"Error closing connections: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: initializing databases")
    await init_db()
    try:
        redis = get_redis()
        await redis.ping()
        logger.info(f"Startup: initializing Redis")
    except Exception as e:
        logger.error(f"Redis initialization has BROKE: {e}")
    yield
    logger.info("Shutdown: closing database connections")
    await close_db(app)
    logger.info("Shutdown: closing Redis connections")
    await redis.aclose()