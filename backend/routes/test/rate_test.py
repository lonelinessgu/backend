# backend.test.rate_test
from fastapi import APIRouter, Depends
from backend.utils.rate_limiter import rate_limiter_factory

rate_test_router = APIRouter()

@rate_test_router.get("/ping", dependencies=[Depends(rate_limiter_factory(__name__, 5, 5, "lol"))])
async def health_check():
    try:
        return {"pong"}
    except Exception as e:
        return {str(e)}