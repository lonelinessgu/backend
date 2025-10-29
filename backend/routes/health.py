# backend.routes.health
from fastapi import APIRouter
from tortoise import Tortoise

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    try:
        await Tortoise.get_connection("users_connection").execute_query("SELECT 1")
        return {"status": "healthy", "db": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "db": str(e)}