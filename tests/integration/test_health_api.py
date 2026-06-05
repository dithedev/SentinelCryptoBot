"""Integration tests for health check API endpoints."""

from unittest.mock import AsyncMock

import pytest
from app.api.main import create_app
from fastapi.testclient import TestClient


def test_health_check_returns_ok() -> None:
    """GET /health should return liveness status without dependencies."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_ready_when_database_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /health/ready should report ready when database check passes."""
    client = TestClient(create_app())

    mocked_database_check = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "app.api.routes.health.check_database_health",
        mocked_database_check,
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
    }


def test_readiness_check_returns_not_ready_when_database_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /health/ready should report not_ready when database check fails."""
    client = TestClient(create_app())

    mocked_database_check = AsyncMock(return_value=False)
    monkeypatch.setattr(
        "app.api.routes.health.check_database_health",
        mocked_database_check,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }
