"""Static file serving helpers for the Telegram Mini App."""

from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class MiniAppStaticFiles(StaticFiles):
    """Serve Mini App assets with safe cache headers for ES module graphs.

    The HTML entrypoint can still use a manual query version, but child module
    imports must not remain cached forever after deploy.
    """

    _NO_CACHE_PATH_SUFFIXES = (".js", ".css", ".html")

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)

        if path.endswith(self._NO_CACHE_PATH_SUFFIXES):
            response.headers["Cache-Control"] = "no-cache, must-revalidate"

        return response
