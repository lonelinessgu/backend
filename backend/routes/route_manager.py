# backend.routes.route_manager
from fastapi import APIRouter
from fastapi.routing import APIRoute

route_groups = {
    "documentation": {"info"},
    "user_modules": {"login", "create_user"},
    "test":{"rate_test"},
}

api_router = APIRouter(prefix="/api")

for tag, route_names in route_groups.items():
    for route_name in route_names:
        module_path = f"backend.routes.{tag}.{route_name}"
        module = __import__(module_path, fromlist=[f"{route_name}_router"])
        router = getattr(module, f"{route_name}_router")
        api_router.include_router(router, tags=[tag])

from backend.routes.health import health_router
api_router.include_router(health_router, tags=["health"])

#Улучшение читаемости документации путём хуманизации тегов и упразднения повторов
def add_route_tags(router: APIRouter):
    for route in router.routes:
        if isinstance(route, APIRoute):
            route.tags = list(set(route.tags))  # Убираем дубликаты
            route.name = route.name.replace("_", " ").title()
add_route_tags(api_router)