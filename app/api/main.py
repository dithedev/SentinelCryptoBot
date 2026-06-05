"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.lifespan import app_lifespan
from app.api.middlewares import MiniAppRateLimitMiddleware
from app.api.miniapp_static import MiniAppStaticFiles
from app.api.routes import setup_api_routes
from app.api.texts import API_DESCRIPTION, API_TITLE, API_VERSION


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=app_lifespan,
    )

    register_exception_handlers(application)
    application.add_middleware(MiniAppRateLimitMiddleware)
    application.include_router(setup_api_routes())
    _mount_miniapp(application)

    return application


def _mount_miniapp(application: FastAPI) -> None:
    """Serve Mini App static files from app/miniapp.

    In production, the Mini App can also be hosted separately on any HTTPS
    static hosting. Keeping it mounted here makes local testing simple.
    """
    miniapp_dir = Path(__file__).resolve().parents[1] / "miniapp"

    application.mount(
        "/miniapp",
        MiniAppStaticFiles(directory=miniapp_dir, html=True),
        name="miniapp",
    )


app = create_app()
