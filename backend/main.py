# backend/main.py
from dotenv import load_dotenv
import uvicorn
import logging
from fastapi import FastAPI

load_dotenv() #Инициализация работы с .env файлом

from backend.lifespan import lifespan
from backend.middleware.logger import log_requests
from backend.middleware.cors import make_cors_middleware
from backend.routes.route_manager import api_router

app = FastAPI(lifespan=lifespan, middleware=make_cors_middleware())

logging.basicConfig(level=logging.INFO)

#Подключение middleware для логирования
app.middleware("http")(log_requests)

#Подключение роутера
app.include_router(api_router)

#Отключение всех логов ниже WARNING, для уменьшения замусоривания консоли
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)