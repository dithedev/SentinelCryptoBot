"""Integration tests for Telegram Mini App API endpoints.

The Mini App route layer is tested through FastAPI TestClient. Database and
service calls are patched so tests stay deterministic and do not require a real
PostgreSQL connection.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.api.deps import get_current_miniapp_user
from app.api.main import create_app
from app.api.texts import ALERT_DISABLED_MESSAGE
from app.core.constants import SUPPORTED_COINS
from app.core.error_messages import TELEGRAM_INIT_DATA_MISSING_ERROR
from app.core.exceptions import AlertNotFoundError, ValidationError
from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.database.models.user import User
from app.services.alerts_service import AlertCreateData, AlertHistoryPage
from fastapi.testclient import TestClient


def _build_user() -> User:
    """Build a deterministic authenticated Mini App user."""
    return User(
        id=1,
        telegram_id=123456789,
        username="sentinel_user",
        first_name="Sentinel",
        last_name="User",
        is_active=True,
    )


def _build_other_user() -> User:
    """Build a second deterministic user for ownership tests."""
    return User(
        id=2,
        telegram_id=987654321,
        username="other_user",
        first_name="Other",
        last_name="User",
        is_active=True,
    )


def _build_alert(
    *,
    alert_id: int = 1,
    user_id: int = 1,
    status: AlertStatus = AlertStatus.ACTIVE,
) -> Alert:
    """Build a deterministic alert object for Mini App responses."""
    created_at = datetime(2026, 5, 11, 10, 0, tzinfo=UTC)

    return Alert(
        id=alert_id,
        user_id=user_id,
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("100000.00000000"),
        condition=AlertCondition.ABOVE,
        status=status,
        triggered_at=None,
        created_at=created_at,
        updated_at=created_at,
    )


def _create_test_client_with_user(user: User | None = None) -> TestClient:
    """Create a TestClient and override Mini App authentication."""
    app = create_app()

    async def fake_get_current_miniapp_user() -> User:
        """Return a deterministic user instead of validating initData."""
        return user or _build_user()

    app.dependency_overrides[get_current_miniapp_user] = fake_get_current_miniapp_user

    return TestClient(app)


def test_miniapp_config_returns_public_static_config() -> None:
    """GET /miniapp-api/config should be public and return UI config."""
    client = TestClient(create_app())

    response = client.get("/miniapp-api/config")

    assert response.status_code == 200

    payload = response.json()

    assert payload["supported_coins"] == [
        {
            "coin_id": coin.coin_id,
            "symbol": coin.symbol,
            "name": coin.name,
        }
        for coin in SUPPORTED_COINS
    ]
    assert payload["alert_conditions"] == ["above", "below"]


def test_miniapp_me_requires_telegram_init_data_without_override() -> None:
    """GET /miniapp-api/me should reject requests without signed initData."""
    client = TestClient(create_app())

    response = client.get("/miniapp-api/me")

    assert response.status_code == 401
    assert response.json() == {"detail": TELEGRAM_INIT_DATA_MISSING_ERROR}


def test_miniapp_me_returns_authenticated_user() -> None:
    """GET /miniapp-api/me should return the authenticated Mini App user."""
    client = _create_test_client_with_user()

    response = client.get("/miniapp-api/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "telegram_id": 123456789,
        "username": "sentinel_user",
        "first_name": "Sentinel",
        "last_name": "User",
    }


def test_miniapp_list_alerts_uses_authenticated_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /miniapp-api/alerts should list only current user's alerts."""

    async def fake_get_active_user_alerts(
        _session: object,
        *,
        user_id: int,
    ) -> list[Alert]:
        """Verify that route uses authenticated user's internal id."""
        assert user_id == 1
        return [_build_alert(user_id=user_id)]

    monkeypatch.setattr(
        "app.api.routes.miniapp.get_active_user_alerts",
        fake_get_active_user_alerts,
    )

    client = _create_test_client_with_user()
    response = client.get("/miniapp-api/alerts")

    assert response.status_code == 200
    assert response.json()[0]["user_id"] == 1
    assert response.json()[0]["coin_id"] == "bitcoin"


def test_miniapp_list_alerts_can_return_history_for_backward_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /miniapp-api/alerts can still include full history when requested."""

    async def fake_get_user_alert_history(
        _session: object,
        *,
        user_id: int,
    ) -> list[Alert]:
        """Return deterministic history for the authenticated user."""
        assert user_id == 1
        return [
            _build_alert(alert_id=1, status=AlertStatus.ACTIVE),
            _build_alert(alert_id=2, status=AlertStatus.TRIGGERED),
        ]

    monkeypatch.setattr(
        "app.api.routes.miniapp.get_user_alert_history",
        fake_get_user_alert_history,
    )

    client = _create_test_client_with_user()
    response = client.get(
        "/miniapp-api/alerts",
        params={"include_inactive": True},
    )

    assert response.status_code == 200
    assert [alert["status"] for alert in response.json()] == [
        "active",
        "triggered",
    ]


def test_miniapp_alert_history_returns_paginated_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /miniapp-api/alerts/history should return one history page."""

    async def fake_get_user_alert_history_page(
        _session: object,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> AlertHistoryPage:
        """Verify pagination parameters and return deterministic data."""
        assert user_id == 1
        assert limit == 2
        assert offset == 0

        return AlertHistoryPage(
            items=[
                _build_alert(alert_id=1, status=AlertStatus.TRIGGERED),
                _build_alert(alert_id=2, status=AlertStatus.DISABLED),
            ],
            limit=2,
            offset=0,
            has_more=True,
        )

    monkeypatch.setattr(
        "app.api.routes.miniapp.get_user_alert_history_page",
        fake_get_user_alert_history_page,
    )

    client = _create_test_client_with_user()
    response = client.get(
        "/miniapp-api/alerts/history",
        params={
            "limit": 2,
            "offset": 0,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert payload["has_more"] is True
    assert [alert["status"] for alert in payload["items"]] == [
        "triggered",
        "disabled",
    ]


def test_miniapp_alert_history_validates_limit() -> None:
    """GET /miniapp-api/alerts/history should reject too large page size."""
    client = _create_test_client_with_user()

    response = client.get(
        "/miniapp-api/alerts/history",
        params={
            "limit": 1000,
            "offset": 0,
        },
    )

    assert response.status_code == 422


def test_miniapp_create_alert_uses_authenticated_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /miniapp-api/alerts should create an alert for current user."""

    async def fake_create_price_alert(
        _session: object,
        *,
        data: AlertCreateData,
    ) -> Alert:
        """Verify that the payload cannot override user ownership."""
        assert data.user_id == 1
        assert data.coin_id == "bitcoin"
        assert data.target_price == Decimal("100000")
        assert data.condition == AlertCondition.ABOVE

        return _build_alert(user_id=data.user_id)

    monkeypatch.setattr(
        "app.api.routes.miniapp.create_price_alert",
        fake_create_price_alert,
    )

    client = _create_test_client_with_user()
    response = client.post(
        "/miniapp-api/alerts",
        json={
            "coin_id": "bitcoin",
            "target_price": "100000",
            "condition": "above",
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == 1
    assert response.json()["coin_id"] == "bitcoin"
    assert response.json()["condition"] == "above"


def test_miniapp_create_alert_returns_bad_request_for_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /miniapp-api/alerts should map domain validation to HTTP 400."""

    async def fake_create_price_alert(
        _session: object,
        *,
        data: AlertCreateData,
    ) -> Alert:
        """Simulate validation failure from the domain layer."""
        assert data.user_id == 1
        raise ValidationError("Unsupported coin id.")

    monkeypatch.setattr(
        "app.api.routes.miniapp.create_price_alert",
        fake_create_price_alert,
    )

    client = _create_test_client_with_user()
    response = client.post(
        "/miniapp-api/alerts",
        json={
            "coin_id": "dogecoin",
            "target_price": "100000",
            "condition": "above",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported coin id."}


def test_miniapp_disable_alert_uses_authenticated_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH /miniapp-api/alerts/{id}/disable should use current user id."""

    async def fake_disable_user_alert(
        _session: object,
        *,
        user_id: int,
        alert_id: int,
    ) -> Alert:
        """Verify route passes authenticated user's internal id."""
        assert user_id == 1
        assert alert_id == 10
        return _build_alert(
            alert_id=alert_id, user_id=user_id, status=AlertStatus.DISABLED
        )

    monkeypatch.setattr(
        "app.api.routes.miniapp.disable_user_alert",
        fake_disable_user_alert,
    )

    client = _create_test_client_with_user()
    response = client.patch("/miniapp-api/alerts/10/disable")

    assert response.status_code == 200
    assert response.json() == {"message": ALERT_DISABLED_MESSAGE}


def test_miniapp_disable_alert_returns_not_found_for_missing_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH /miniapp-api/alerts/{id}/disable should return 404 for missing alert."""

    async def fake_disable_user_alert(
        _session: object,
        *,
        user_id: int,
        alert_id: int,
    ) -> Alert:
        """Simulate missing alert or alert owned by another user."""
        assert user_id == 2
        assert alert_id == 10
        raise AlertNotFoundError

    monkeypatch.setattr(
        "app.api.routes.miniapp.disable_user_alert",
        fake_disable_user_alert,
    )

    client = _create_test_client_with_user(_build_other_user())
    response = client.patch("/miniapp-api/alerts/10/disable")

    assert response.status_code == 404
    assert response.json() == {"detail": "Alert was not found."}
