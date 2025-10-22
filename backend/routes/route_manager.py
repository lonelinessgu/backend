# routes/route_manager
from fastapi import APIRouter
from fastapi.routing import APIRoute

from backend.routes.user_modules.login import login_router
from backend.routes.user_modules.create_user import create_user_router
from backend.routes.health import health_router

api_router = APIRouter(prefix="/api")

api_router.include_router(login_router, tags=["user_modules"])
api_router.include_router(create_user_router, tags=["user_modules"])

api_router.include_router(health_router, tags=["health"])
#Улучшение читаемости документации путём хуманизации тегов и упразднения повторов
def add_route_tags(router: APIRouter):
    for route in router.routes:
        if isinstance(route, APIRoute):
            route.tags = list(set(route.tags))  # Убираем дубликаты
            route.name = route.name.replace("_", " ").title()
add_route_tags(api_router)
