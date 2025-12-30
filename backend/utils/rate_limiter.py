import time
from functools import lru_cache
from typing import Annotated
import logging
from fastapi import HTTPException, status, Request, Depends
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

@lru_cache
def get_redis() -> Redis:
    return Redis(host="localhost", port=6379, decode_responses=False)


class RateLimiter:
    def __init__(self, redis: Redis):
        self._redis = redis
        self._lua_sha = None

    async def _load_script(self):
        if self._lua_sha is None:
            script = """
            redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, ARGV[2])
            local current_count = redis.call("ZCARD", KEYS[1])
            if current_count >= tonumber(ARGV[3]) then
                return 1
            end
            redis.call("ZADD", KEYS[1], ARGV[1], ARGV[4])
            redis.call("EXPIRE", KEYS[1], ARGV[5])
            return 0
            """
            self._lua_sha = await self._redis.script_load(script)

    async def is_limited(
            self,
            ip_address: str,
            endpoint: str,
            max_requests: int,
            window_seconds: int,
    ) -> bool:
        await self._load_script()

        key = f"rate_limiter:{endpoint}:{ip_address}"
        current_ms = int(time.time() * 1000)
        window_start_ms = current_ms - (window_seconds * 1000)
        unique_id = f"{current_ms}-{id(self)}-{int(time.time_ns()) & 0xFFFF}"

        try:
            result = await self._redis.evalsha(
                self._lua_sha,
                1,  # количество ключей
                key,
                str(current_ms),  # ARGV[1] - текущее время
                str(window_start_ms),  # ARGV[2] - начало окна
                str(max_requests),  # ARGV[3] - лимит
                unique_id,  # ARGV[4] - уникальный ID
                str(window_seconds),  # ARGV[5] - TTL
            )
            return result == 1
        except Exception as e:
            # fallback на повторную загрузку скрипта при ошибке
            logger.warning(f"{e}")
            self._lua_sha = None
            return await self.is_limited(ip_address, endpoint, max_requests, window_seconds)


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter(get_redis())



def rate_limiter_factory(endpoint: str, max_requests: int, window_seconds: int, detail: str = "Превышено количество запросов."):
    async def dependency(
            request: Request,
            rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    ):
        ip_address = request.client.host
        limited = await rate_limiter.is_limited(
            ip_address, endpoint, max_requests, window_seconds
        )
        if limited:
            logger.info(f"ENDPOINT: {endpoint} went beyond the limit from {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail
            )

    return dependency