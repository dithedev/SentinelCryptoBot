"""Integration tests for Telegram Mini App whale API endpoints."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.api.deps import get_current_miniapp_user
from app.api.main import create_app
from app.core.exceptions import ValidationError
from app.database.models.user import User
from app.database.models.whale import WhaleAlertSettings, WhaleEvent, WhaleEventType
from app.services.whales_service import WhaleEventsPage
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


def _build_settings() -> WhaleAlertSettings:
    """Build deterministic whale settings."""
    created_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleAlertSettings(
        id=1,
        user_id=1,
        is_enabled=False,
        min_usd_value=Decimal("1000000"),
        created_at=created_at,
        updated_at=created_at,
    )


def _build_event() -> WhaleEvent:
    """Build deterministic whale event."""
    detected_at = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    return WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="sim-abc",
        from_address=None,
        to_address=None,
        amount=Decimal("10"),
        amount_usd=Decimal("1500000"),
        event_type=WhaleEventType.EXCHANGE_OUTFLOW,
        detected_at=detected_at,
        raw_payload={"source": "simulator"},
        created_at=detected_at,
    )


def _create_test_client_with_user() -> TestClient:
    """Create a TestClient and override Mini App authentication."""
    app = create_app()

    async def fake_get_current_miniapp_user() -> User:
        return _build_user()

    app.dependency_overrides[get_current_miniapp_user] = fake_get_current_miniapp_user

    return TestClient(app)


def test_miniapp_get_whale_settings_returns_user_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /miniapp-api/whales/settings should return current user settings."""

    async def fake_get_or_create(
        _session: object,
        *,
        user_id: int,
    ) -> WhaleAlertSettings:
        assert user_id == 1
        return _build_settings()

    monkeypatch.setattr(
        "app.api.routes.miniapp.get_or_create_user_whale_settings",
        fake_get_or_create,
    )

    client = _create_test_client_with_user()
    response = client.get("/miniapp-api/whales/settings")

    assert response.status_code == 200
    assert response.json()["user_id"] == 1
    assert response.json()["is_enabled"] is False
    assert response.json()["min_usd_value"].startswith("1000000")


def test_miniapp_patch_whale_settings_updates_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH /miniapp-api/whales/settings should update user settings."""

    async def fake_update_settings(
        _session: object,
        *,
        data: object,
    ) -> WhaleAlertSettings:
        settings = _build_settings()
        settings.is_enabled = True
        settings.min_usd_value = Decimal("2500000.00")
        return settings

    monkeypatch.setattr(
        "app.api.routes.miniapp.update_user_whale_settings",
        fake_update_settings,
    )

    client = _create_test_client_with_user()
    response = client.patch(
        "/miniapp-api/whales/settings",
        json={
            "is_enabled": True,
            "min_usd_value": "2500000",
        },
    )

    assert response.status_code == 200
    assert response.json()["is_enabled"] is True
    assert response.json()["min_usd_value"].startswith("2500000")


def test_miniapp_patch_whale_settings_can_disable_alerts_without_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH /miniapp-api/whales/settings should allow toggle-only updates."""

    async def fake_update_settings(
        _session: object,
        *,
        data: object,
    ) -> WhaleAlertSettings:
        settings = _build_settings()
        settings.is_enabled = False
        return settings

    monkeypatch.setattr(
        "app.api.routes.miniapp.update_user_whale_settings",
        fake_update_settings,
    )

    client = _create_test_client_with_user()
    response = client.patch(
        "/miniapp-api/whales/settings",
        json={"is_enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["is_enabled"] is False


def test_miniapp_patch_whale_settings_returns_unprocessable_for_schema_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH /miniapp-api/whales/settings rejects invalid payloads at schema level."""

    async def fake_update_settings(
        _session: object,
        *,
        data: object,
    ) -> WhaleAlertSettings:
        raise ValidationError("Minimum whale alert value must be at least 1000 USD.")

    monkeypatch.setattr(
        "app.api.routes.miniapp.update_user_whale_settings",
        fake_update_settings,
    )

    client = _create_test_client_with_user()
    response = client.patch(
        "/miniapp-api/whales/settings",
        json={"min_usd_value": "10"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "min_usd_value"]


def test_miniapp_list_whale_events_returns_paginated_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /miniapp-api/whales/events should return paginated whale events."""

    async def fake_get_latest_whale_events_page(
        _session: object,
        *,
        limit: int,
        offset: int,
    ) -> WhaleEventsPage:
        assert limit == 2
        assert offset == 0

        return WhaleEventsPage(
            items=[_build_event()],
            limit=2,
            offset=0,
            has_more=True,
        )

    monkeypatch.setattr(
        "app.api.routes.miniapp.get_latest_whale_events_page",
        fake_get_latest_whale_events_page,
    )

    client = _create_test_client_with_user()
    response = client.get(
        "/miniapp-api/whales/events",
        params={"limit": 2, "offset": 0},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["has_more"] is True
    assert payload["items"][0]["symbol"] == "BTC"
    assert payload["items"][0]["transaction_hash"] == "sim-abc"
