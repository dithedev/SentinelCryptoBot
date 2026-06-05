"""Integration tests for Mini App token risk check endpoint.

The route is tested through FastAPI TestClient. Authentication and domain
service calls are patched so the test verifies HTTP behavior without a real
database or external GoPlus request.
"""

from datetime import UTC, datetime

import pytest
from app.api.deps import get_current_miniapp_user
from app.api.main import create_app
from app.api.texts import RISK_CHECK_PROVIDER_ERROR_MESSAGE
from app.core.exceptions import SecurityProviderError, ValidationError
from app.database.models.token_check import RiskLevel, TokenCheck
from app.database.models.user import User
from app.services.token_risk_service import TokenRiskCheckData
from fastapi.testclient import TestClient


def build_user() -> User:
    """Build a deterministic authenticated Mini App user."""
    return User(
        id=1,
        telegram_id=123456789,
        username="sentinel_user",
        first_name="Sentinel",
        last_name="User",
        is_active=True,
    )


def build_token_check(
    *,
    user_id: int = 1,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
) -> TokenCheck:
    """Build a deterministic token check response object."""
    return TokenCheck(
        id=10,
        user_id=user_id,
        chain="eth",
        contract_address="0x0000000000000000000000000000000000000000",
        risk_level=risk_level,
        flags={
            "slippage_modifiable": True,
            "buy_tax": 15.0,
        },
        raw_response={
            "slippage_modifiable": "1",
            "buy_tax": "15",
        },
        created_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
    )


def create_test_client_with_user(user: User | None = None) -> TestClient:
    """Create a TestClient with Mini App authentication overridden."""
    app = create_app()

    async def fake_get_current_miniapp_user() -> User:
        """Return a deterministic user instead of validating initData."""
        return user or build_user()

    app.dependency_overrides[get_current_miniapp_user] = fake_get_current_miniapp_user

    return TestClient(app)


def test_miniapp_risk_check_uses_authenticated_user_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /miniapp-api/risk-check should use authenticated user ownership."""

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Verify route passes current user id into the service."""
        assert data.user_id == 1
        assert data.chain == "eth"
        assert data.contract_address == "0x0000000000000000000000000000000000000000"

        return build_token_check(user_id=data.user_id)

    monkeypatch.setattr(
        "app.api.routes.miniapp.check_token_risk",
        fake_check_token_risk,
    )

    client = create_test_client_with_user()

    response = client.post(
        "/miniapp-api/risk-check",
        json={
            "chain": "eth",
            "contract_address": "0x0000000000000000000000000000000000000000",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload == {
        "id": 10,
        "chain": "eth",
        "contract_address": "0x0000000000000000000000000000000000000000",
        "risk_level": "medium",
        "flags": {
            "slippage_modifiable": True,
            "buy_tax": 15.0,
        },
        "created_at": "2026-05-18T10:00:00Z",
    }

    assert "score" not in payload
    assert "raw_response" not in payload


def test_miniapp_risk_check_returns_bad_request_for_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Domain validation errors should become HTTP 400."""

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Simulate validation failure."""
        assert data.user_id == 1
        raise ValidationError("Unsupported chain.")

    monkeypatch.setattr(
        "app.api.routes.miniapp.check_token_risk",
        fake_check_token_risk,
    )

    client = create_test_client_with_user()

    response = client.post(
        "/miniapp-api/risk-check",
        json={
            "chain": "ton",
            "contract_address": "not-a-contract",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported chain."}


def test_miniapp_risk_check_returns_bad_gateway_for_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider errors should become HTTP 502."""

    async def fake_check_token_risk(
        _session: object,
        *,
        data: TokenRiskCheckData,
    ) -> TokenCheck:
        """Simulate external provider failure."""
        assert data.user_id == 1
        raise SecurityProviderError("provider failed")

    monkeypatch.setattr(
        "app.api.routes.miniapp.check_token_risk",
        fake_check_token_risk,
    )

    client = create_test_client_with_user()

    response = client.post(
        "/miniapp-api/risk-check",
        json={
            "chain": "eth",
            "contract_address": "0x0000000000000000000000000000000000000000",
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": RISK_CHECK_PROVIDER_ERROR_MESSAGE}
