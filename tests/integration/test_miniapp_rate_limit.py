"""Integration tests for Mini App API rate limiting."""

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from app.api.deps import get_current_miniapp_user
from app.api.main import create_app
from app.api.middlewares import rate_limit as rate_limit_module
from app.api.middlewares.rate_limit import (
    build_api_rate_limiter,
    configure_api_rate_limiter,
)
from app.core.config import get_settings
from app.core.rate_limit import FixedWindowRateLimiter
from app.database.models.user import User
from fastapi.testclient import TestClient


def _build_user() -> User:
    """Build a deterministic authenticated Mini App user."""
    created_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return User(
        id=1,
        telegram_id=123456789,
        username="sentinel_user",
        first_name="Sentinel",
        last_name="User",
        is_active=True,
        created_at=created_at,
        updated_at=created_at,
    )


@pytest.fixture(autouse=True)
def reset_api_rate_limiter() -> Generator[None]:
    """Reset shared API limiter state between tests."""
    yield
    rate_limit_module._api_rate_limiter = None
    configure_api_rate_limiter(build_api_rate_limiter(settings=get_settings()))


def _create_test_client() -> TestClient:
    """Create a TestClient with Mini App auth override."""
    app = create_app()

    async def fake_get_current_miniapp_user() -> User:
        return _build_user()

    app.dependency_overrides[get_current_miniapp_user] = fake_get_current_miniapp_user

    return TestClient(app)


def test_miniapp_api_returns_429_after_rate_limit() -> None:
    """Mini App API should reject requests above the configured per-minute cap."""
    configure_api_rate_limiter(
        FixedWindowRateLimiter(max_calls=2, period_seconds=60.0),
    )
    client = _create_test_client()

    first = client.get("/miniapp-api/me")
    second = client.get("/miniapp-api/me")
    third = client.get("/miniapp-api/me")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json() == {"detail": "Too many requests"}


def test_static_miniapp_assets_are_not_rate_limited() -> None:
    """Static Mini App files should bypass API rate limiting."""
    configure_api_rate_limiter(
        FixedWindowRateLimiter(max_calls=1, period_seconds=60.0),
    )
    client = _create_test_client()

    first = client.get("/miniapp/index.html")
    second = client.get("/miniapp/index.html")

    assert first.status_code == 200
    assert second.status_code == 200
