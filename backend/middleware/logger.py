# middleware/logger
import logging
import time
import os
from pathlib import Path
from fastapi import Request
from starlette.responses import FileResponse, StreamingResponse

# Импортируем список исключений
try:
    from backend.routes.logging_config import EXCLUDED_200_URLS
    # Используем логгер для информации об исключениях
    middleware_logger = logging.getLogger("middleware")
    if EXCLUDED_200_URLS:
        middleware_logger.info(
            f"Следующие маршруты не будут записаны в success.log при статусе 200:\n{', '.join(EXCLUDED_200_URLS)}"
        )
    else:
        middleware_logger.info("Нет маршрутов для исключения из success.log")
except ImportError as e:
    print(f"IMPORT ERROR for logging_config: {e}") # print приемлем для фатальных ошибок при старте
    EXCLUDED_200_URLS = []
except Exception as e:
    print(f"UNEXPECTED ERROR loading EXCLUDED_200_URLS: {e}") # print приемлем для фатальных ошибок при старте
    EXCLUDED_200_URLS = []


PROJECT_ROOT = Path(__file__).parents[2]
LOG_DIR = Path(os.getenv("DB_DATA_DIR", PROJECT_ROOT / "logs"))
LOG_DIR.mkdir(exist_ok=True)

# Логгер для запросов
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Отключаем распространение в корневой логгер

# Форматтер для логов
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

# Обработчики файлов
success_handler = logging.FileHandler(LOG_DIR / "success.log", encoding='utf-8')
error_handler = logging.FileHandler(LOG_DIR / "errors.log", encoding='utf-8')

# Настраиваем форматер
success_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Фильтры для обработчиков остаются простыми, они просто смотрят на статус
class SuccessFilter(logging.Filter):
    def filter(self, record):
        return 200 <= getattr(record, 'status_code', 0) < 300

class ErrorFilter(logging.Filter):
    def filter(self, record):
        return 400 <= getattr(record, 'status_code', 0) < 600

success_handler.addFilter(SuccessFilter())
error_handler.addFilter(ErrorFilter())

# Привязываем обработчики к логгеру
logger.addHandler(success_handler)
logger.addHandler(error_handler)

async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Определение IP клиента
    client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.headers.get("CF-Connecting-IP", "")
            or request.client.host
    )

    # Чтение тела запроса
    content_type = request.headers.get("content-type", "")
    try:
        request_body = await request.json()
    except Exception:
        try:
            request_body = (await request.body()).decode("utf-8")
        except:
            request_body = "<unable to decode>"

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    url_path = request.url.path

    # Проверка типа ответа
    is_file_response = isinstance(response, (FileResponse, StreamingResponse))

    # Формируем краткое описание тела запроса для лога
    if isinstance(request_body, str) and len(request_body) > 100:
         log_request_body = request_body[:100] + "...<truncated>"
    else:
         log_request_body = str(request_body)[:100] # Приведение к строке на случай, если это dict и т.д.

    # Формируем сообщение для лога
    log_message = (
        f"{request.method} {url_path} - "
        f"Status: {response.status_code}, "
        f"IP: {client_ip}, "
        f"Time: {process_time:.2f}ms, "
        f"Content-Type: {content_type}, "
        f"Request-Body: {log_request_body}, "
        f"File-Response: {is_file_response}"
    )

    # --- НОВАЯ ЛОГИКА: Проверка на исключение перед логированием ---
    status_code = response.status_code
    should_log = True

    # Если статус 2xx И путь в списке исключений, НЕ логируем
    if 200 <= status_code < 300 and url_path in EXCLUDED_200_URLS:
        should_log = False

    # Логируем только если should_log == True
    if should_log:
        logger.info(
            log_message,
            extra={'status_code': status_code}
        )

    return response