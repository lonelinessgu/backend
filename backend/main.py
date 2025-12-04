# backend.main
from dotenv import load_dotenv
from pathlib import Path
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

# Загрузка dotenv
dotenv_path = Path(__file__).parents[1] / ".env"
if not dotenv_path.exists():
    raise FileNotFoundError(f".env файл не найден по пути: {dotenv_path}")
load_dotenv(dotenv_path)

# Конфигурация логирования
logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Импорты модулей проекта
from backend.lifespan import lifespan
from backend.middleware.logger import log_requests
from backend.middleware.cors import make_cors_middleware
from backend.routes.route_manager import api_router
from backend.middleware.validation_error_catcher import validation_exception_handler

app = FastAPI(lifespan=lifespan, middleware=make_cors_middleware())

# Подключение логгеров
app.exception_handler(RequestValidationError)(validation_exception_handler)
app.middleware("http")(log_requests)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)