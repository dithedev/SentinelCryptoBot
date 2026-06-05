"""Shared pytest fixtures."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.api.main import create_app
from app.database.models.user import User
from fastapi.testclient import TestClient

pytest_plugins = ["tests.conftest_db"]


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    """Return a TestClient with FastAPI lifespan enabled."""
    with TestClient(create_app()) as client:
        yield client


@pytest.fixture
def sample_user() -> User:
    """Return a deterministic Telegram user for API tests."""
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
