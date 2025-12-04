import logging
import time
import os
from pathlib import Path
from fastapi import Request
from starlette.responses import FileResponse, StreamingResponse

try:
    from backend.routes.logging_config import EXCLUDED_200_URLS

    middleware_logger = logging.getLogger("middleware")
    if EXCLUDED_200_URLS:
        middleware_logger.info(f" Excluded routes: {', '.join(EXCLUDED_200_URLS)}")
    else:
        middleware_logger.info(" No excluded routes")
except ImportError:
    EXCLUDED_200_URLS = []
except Exception as e:
    print(f"Error loading EXCLUDED_200_URLS: {e}")
    EXCLUDED_200_URLS = []

PROJECT_ROOT = Path(__file__).parents[2]
LOG_DIR = Path(os.getenv("DB_DATA_DIR", PROJECT_ROOT / "logs"))
LOG_DIR.mkdir(exist_ok=True)


class RequestLogger:
    def __init__(self):
        self.logger = self._setup_logger()
        self.excluded_urls = EXCLUDED_200_URLS

    def _setup_logger(self):
        logger = logging.getLogger("request_logger")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        success_handler = logging.FileHandler(LOG_DIR / "success.log", encoding='utf-8')
        error_handler = logging.FileHandler(LOG_DIR / "errors.log", encoding='utf-8')

        success_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)

        class SuccessFilter(logging.Filter):
            def filter(self, record):
                return 200 <= getattr(record, 'status_code', 0) < 300

        class ErrorFilter(logging.Filter):
            def filter(self, record):
                return 400 <= getattr(record, 'status_code', 0) < 600

        success_handler.addFilter(SuccessFilter())
        error_handler.addFilter(ErrorFilter())

        logger.addHandler(success_handler)
        logger.addHandler(error_handler)
        return logger

    async def log_request(self, request: Request, call_next):
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        request_body = await self._get_request_body(request)

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        url_path = request.url.path

        if self._should_log(url_path, response.status_code):
            log_message = self._format_log_message(
                request.method, url_path, response.status_code,
                client_ip, process_time, request.headers.get("content-type", ""),
                request_body, isinstance(response, (FileResponse, StreamingResponse))
            )
            self.logger.info(log_message, extra={'status_code': response.status_code})

        return response

    def _get_client_ip(self, request: Request) -> str:
        return (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or request.headers.get("X-Real-IP", "")
                or request.headers.get("CF-Connecting-IP", "")
                or request.client.host
        )

    async def _get_request_body(self, request: Request) -> str:
        try:
            body = await request.json()
        except Exception:
            try:
                body = (await request.body()).decode("utf-8")
            except:
                body = "<unable to decode>"
        return body

    def _should_log(self, url_path: str, status_code: int) -> bool:
        if 200 <= status_code < 300 and url_path in self.excluded_urls:
            return False
        return True

    def _format_log_message(self, method: str, url: str, status: int, ip: str,
                            time_ms: float, content_type: str, body: str, is_file: bool) -> str:
        body_str = str(body)
        if len(body_str) > 100:
            body_str = body_str[:100] + "...<truncated>"

        return (
            f"{method} {url} - Status: {status}, IP: {ip}, "
            f"Time: {time_ms:.2f}ms, Content-Type: {content_type}, "
            f"Request-Body: {body_str}, File-Response: {is_file}"
        )


request_logger = RequestLogger()
log_requests = request_logger.log_request