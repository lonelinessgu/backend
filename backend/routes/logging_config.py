# backend.routes.logging_config
from fastapi.routing import APIRoute


def get_all_route_paths() -> list:
    """Получает все пути из API роутера"""
    try:
        # Отложенный импорт, чтобы избежать циклических зависимостей
        from backend.routes.route_manager import api_router

        paths = set()
        if api_router:
            for route in api_router.routes:
                if isinstance(route, APIRoute):
                    full_path = route.path  # Используем просто route.path
                    paths.add(full_path)

        path_list = list(paths)
        return path_list

    except Exception as e:
        print(f"ERROR in get_all_route_paths: {e}")
        import traceback
        traceback.print_exc()
        return []


# Глобальная переменная с путями
EXCLUDED_200_URLS = get_all_route_paths()