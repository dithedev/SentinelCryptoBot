"""Rate limiting middleware for Mini App API routes."""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import Settings, get_settings
from app.core.rate_limit import FixedWindowRateLimiter

MINIAPP_API_PREFIX = "/miniapp-api"
API_RATE_LIMIT_PERIOD_SECONDS = 60.0

_api_rate_limiter: FixedWindowRateLimiter | None = None


def build_api_rate_limiter(*, settings: Settings) -> FixedWindowRateLimiter:
    """Create a fixed-window limiter from application settings."""
    return FixedWindowRateLimiter(
        max_calls=settings.miniapp_api_requests_per_minute,
        period_seconds=API_RATE_LIMIT_PERIOD_SECONDS,
    )


def configure_api_rate_limiter(limiter: FixedWindowRateLimiter) -> None:
    """Replace the process-wide Mini App API limiter (used in tests)."""
    global _api_rate_limiter
    _api_rate_limiter = limiter


def get_api_rate_limiter() -> FixedWindowRateLimiter:
    """Return the shared Mini App API limiter for this process."""
    global _api_rate_limiter

    if _api_rate_limiter is None:
        _api_rate_limiter = build_api_rate_limiter(settings=get_settings())

    return _api_rate_limiter


def _client_key(request: Request) -> str:
    """Build a rate-limit key from the client address."""
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client is not None:
        return request.client.host

    return "unknown"


class MiniAppRateLimitMiddleware(BaseHTTPMiddleware):
    """Return HTTP 429 when Mini App API clients exceed the configured rate."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        limiter: FixedWindowRateLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not request.url.path.startswith(MINIAPP_API_PREFIX):
            return await call_next(request)

        limiter = self._limiter or get_api_rate_limiter()

        if not limiter.allow(_client_key(request)):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
            )

        return await call_next(request)
