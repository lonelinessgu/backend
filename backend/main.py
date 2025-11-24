# backend.main
from dotenv import load_dotenv
from pathlib import Path
dotenv_path = Path(__file__).parents[1] / ".env"

if not dotenv_path.exists():
    raise FileNotFoundError(f".env файл не найден по пути: {dotenv_path}")

load_dotenv(dotenv_path)
import logging
logging.basicConfig(level=logging.INFO)
import uvicorn
#Отключение всех логов ниже WARNING, для уменьшения замусоривания консоли
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
from fastapi import FastAPI
from backend.lifespan import lifespan
from backend.middleware.logger import log_requests
from backend.middleware.cors import make_cors_middleware
from backend.routes.route_manager import api_router

app = FastAPI(lifespan=lifespan, middleware=make_cors_middleware())

#Подключение middleware для логирования
app.middleware("http")(log_requests)

#Подключение роутера
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)