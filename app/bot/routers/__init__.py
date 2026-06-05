from aiogram import Router

from app.bot.middlewares.fsm_callback_guard import FsmCallbackGuardMiddleware
from app.bot.routers.alerts import router as alerts_router
from app.bot.routers.menu import router as menu_router
from app.bot.routers.notifications import router as notifications_router
from app.bot.routers.prices import router as prices_router
from app.bot.routers.risk_check import router as risk_check_router
from app.bot.routers.start import router as start_router
from app.bot.routers.whales import router as whales_router


def setup_routers() -> Router:
    """Collect all bot routers into one root router."""
    root_router = Router(name="root")
    root_router.callback_query.middleware(FsmCallbackGuardMiddleware())

    root_router.include_router(start_router)
    root_router.include_router(notifications_router)
    root_router.include_router(prices_router)
    root_router.include_router(alerts_router)
    root_router.include_router(risk_check_router)
    root_router.include_router(whales_router)

    # Menu router stays last because it contains a fallback callback handler.
    root_router.include_router(menu_router)

    return root_router


__all__ = ("setup_routers",)
