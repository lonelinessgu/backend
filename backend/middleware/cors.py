# backend.middleware.cors
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

def make_cors_middleware():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],           # Разрешить все источники
            allow_credentials=True,
            allow_methods=["*"],           # Разрешить все методы
            allow_headers=["*"],           # Разрешить все заголовки
        )
    ]
    return middleware