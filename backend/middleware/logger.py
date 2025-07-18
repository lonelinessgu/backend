# middleware/logger.py
import logging
import time
from collections import Counter
from pathlib import Path
from fastapi import Request

# Получаем путь к корню проекта: backend/
PROJECT_ROOT = Path(__file__).parents[1]
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Список URL для исключения при статусе 200 (добавьте нужные пути)
EXCLUDED_200_URLS = []

# Форматтер для логов
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Основной логгер для всех запросов
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Отключаем распространение в корневой логгер

# Логгер для ошибок (4xx и 5xx)
error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
error_logger.propagate = False

# Создаем обработчики для разных статусов
handlers = {
    "2xx": logging.FileHandler(LOGS_DIR / "success.log", encoding='utf-8'),
    "3xx": logging.FileHandler(LOGS_DIR / "redirect.log", encoding='utf-8'),
    "4xx": logging.FileHandler(LOGS_DIR / "client_errors.log", encoding='utf-8'),
    "5xx": logging.FileHandler(LOGS_DIR / "server_errors.log", encoding='utf-8'),
    "errors": logging.FileHandler(LOGS_DIR / "errors.log", encoding='utf-8'),
    "console": logging.StreamHandler(),  # Добавляем обработчик для консоли
}

# Настраиваем форматер для всех обработчиков
for handler in handlers.values():
    handler.setFormatter(formatter)

# Привязываем обработчики к логгерам
# Основной логгер получает обработчики для всех категорий + консоль
logger.addHandler(handlers["2xx"])
logger.addHandler(handlers["3xx"])
logger.addHandler(handlers["4xx"])
logger.addHandler(handlers["5xx"])
logger.addHandler(handlers["console"])  # Добавляем вывод в консоль

# Логгер ошибок получает только обработчик для ошибок и отдельные файлы для 4xx и 5xx + консоль
error_logger.addHandler(handlers["errors"])
error_logger.addHandler(handlers["4xx"])
error_logger.addHandler(handlers["5xx"])
error_logger.addHandler(handlers["console"])  # Добавляем вывод в консоль

# Создаем фильтры для обработчиков
class StatusCategoryFilter(logging.Filter):
    def __init__(self, status_category):
        super().__init__()
        self.status_category = status_category

    def filter(self, record):
        return getattr(record, 'status_category', None) == self.status_category


# Применяем фильтры к обработчикам (кроме консольного)
handlers["2xx"].addFilter(StatusCategoryFilter("2xx"))
handlers["3xx"].addFilter(StatusCategoryFilter("3xx"))
handlers["4xx"].addFilter(StatusCategoryFilter("4xx"))
handlers["5xx"].addFilter(StatusCategoryFilter("5xx"))

# Для консольного вывода можно добавить свой фильтр, если нужно
class ConsoleFilter(logging.Filter):
    def filter(self, record):
        # Можно настроить фильтрацию для консоли, если нужно
        return True

handlers["console"].addFilter(ConsoleFilter())


def process_string(s):
    """Обработка длинных строк со статистикой"""
    if not isinstance(s, str):
        return s

    if len(s) <= 256:
        return s

    truncated = s[:255]
    analysis_part = s[:25000]
    counts = Counter(analysis_part)

    most_common = counts.most_common(1)[0] if counts else None
    stats_lines = []

    if most_common:
        stats_lines.append(f"Самый частый символ: '{most_common[0]}' x {most_common[1]}")

    all_counts = [f"{char}: {cnt}" for char, cnt in counts.items()]
    stats_lines.append(f"Все символы: {', '.join(all_counts)}")

    return f"{truncated}\n[СТАТИСТИКА: {', '.join(stats_lines)}]"


def process_log_dict(log_dict):
    """Рекурсивная обработка строк в структурах данных"""
    if isinstance(log_dict, str):
        return process_string(log_dict)
    elif isinstance(log_dict, dict):
        return {key: process_log_dict(value) for key, value in log_dict.items()}
    elif isinstance(log_dict, (list, tuple)):
        return [process_log_dict(item) for item in log_dict]
    return log_dict


def should_log_request(status_code: int, url_path: str) -> bool:
    """Определяем нужно ли логировать запрос"""
    # Всегда логируем ошибки и редиректы
    if status_code >= 300:
        return True

    # Для статуса 200 проверяем исключения
    return url_path not in EXCLUDED_200_URLS


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

    # Формируем данные для лога
    log_data = {
        "method": request.method,
        "path": url_path,
        "client_ip": client_ip,
        "status": response.status_code,
        "time_ms": f"{process_time:.2f}",
        "content_type": content_type,
        "request_body": request_body,
    }

    # Проверяем нужно ли логировать этот запрос
    if not should_log_request(response.status_code, url_path):
        return response

    # Обрабатываем данные перед логированием
    processed_log = process_log_dict(log_data)

    # Определяем категорию статуса
    status_category = f"{response.status_code // 100}xx"

    # Логируем в соответствующий файл и консоль
    if 200 <= response.status_code < 300:
        logger.info(processed_log, extra={"status_category": "2xx"})
    elif 300 <= response.status_code < 400:
        logger.info(processed_log, extra={"status_category": "3xx"})
    elif 400 <= response.status_code < 500:
        logger.info(processed_log, extra={"status_category": "4xx"})
        error_logger.error(processed_log, extra={"status_category": "4xx"})
    elif response.status_code >= 500:
        logger.info(processed_log, extra={"status_category": "5xx"})
        error_logger.error(processed_log, extra={"status_category": "5xx"})

    return response