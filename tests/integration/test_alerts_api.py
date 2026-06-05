"""Integration tests for deprecated public alert API routes.

Public alert management must stay unavailable because ownership cannot be safely
verified from a user-supplied telegram_id query parameter.

Authenticated alert management is covered by tests for /miniapp-api/alerts.
"""

from app.api.main import create_app
from fastapi.testclient import TestClient


def test_public_alerts_list_route_is_not_registered() -> None:
    """GET /alerts should not expose user alerts publicly."""
    client = TestClient(create_app())

    response = client.get("/alerts", params={"telegram_id": 123456789})

    assert response.status_code == 404


def test_public_alerts_create_route_is_not_registered() -> None:
    """POST /alerts should not create alerts from public telegram_id input."""
    client = TestClient(create_app())

    response = client.post(
        "/alerts",
        json={
            "telegram_id": 123456789,
            "coin_id": "bitcoin",
            "target_price": "100000",
            "condition": "above",
        },
    )

    assert response.status_code == 404


def test_public_alerts_delete_route_is_not_registered() -> None:
    """DELETE /alerts/{id} should not modify alerts from public telegram_id input."""
    client = TestClient(create_app())

    response = client.delete(
        "/alerts/10",
        params={"telegram_id": 123456789},
    )

    assert response.status_code == 404
