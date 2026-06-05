from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.miniapp import router as miniapp_router
from app.api.routes.prices import router as prices_router


def setup_api_routes() -> APIRouter:
    """Collect all public API routes into one root router.

    User alert management is intentionally exposed only through
    /miniapp-api/alerts because it is protected by Telegram WebApp initData.

    The old public /alerts route is not registered because accepting
    telegram_id from query parameters would allow users to access or modify
    alerts that do not belong to them.
    """
    router = APIRouter()

    router.include_router(health_router)
    router.include_router(prices_router)
    router.include_router(miniapp_router)

    return router


__all__ = ("setup_api_routes",)
