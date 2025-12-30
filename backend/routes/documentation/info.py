# backend/routes/documentation.py

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
info_router = APIRouter()

@info_router.get("/documentation")
async def serve_scalar_documentation():
    # Вычисляем путь
    static_path = Path(__file__).parents[0] / "scalar.html"
    logger.debug(f"[DEBUG] Путь к scalar.html: {static_path}")

    try:
        with open(static_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"[DEBUG] Файл успешно прочитан. Длина контента: {len(content)}")
    except FileNotFoundError:
        logger.error(f"[ERROR] Файл '{static_path}' не найден.")
        raise HTTPException(status_code=500, detail=f"Файл документации '{static_path}' не найден.")
    except Exception as e:
        logger.error(f"[ERROR] Неизвестная ошибка при чтении файла: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла: {e}")

    return HTMLResponse(content=content)