"""Unit tests for the reusable token risk check service."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from app.core.exceptions import SecurityProviderError
from app.database.models.token_check import RiskLevel, TokenCheck
from app.services import token_risk_service
from app.services.token_risk_service import TokenRiskCheckData, check_token_risk

UNKNOWN_ADDRESS = "0x0000000000000000000000000000000000000000"


class FakeTokenSecurityProvider:
    """Deterministic fake token security provider."""

    def __init__(
        self,
        raw_data: dict[str, Any] | None = None,
    ) -> None:
        self.raw_data = raw_data or {}
        self.calls: list[dict[str, str]] = []

    async def get_token_security_data(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """Return fake raw provider data and remember the call."""
        self.calls.append(
            {
                "chain": chain,
                "contract_address": contract_address,
            },
        )
        return self.raw_data


class FailingTokenSecurityProvider:
    """Fake provider that simulates an external API failure."""

    async def get_token_security_data(
        self,
        *,
        chain: str,
        contract_address: str,
    ) -> dict[str, Any]:
        """Raise a provider error."""
        raise SecurityProviderError("provider failed")


def run_async(result: Any) -> Any:
    """Run one async test helper without requiring pytest-asyncio."""
    return asyncio.run(result)


def test_check_token_risk_calls_provider_analyzes_and_stores_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service should call provider, analyze raw data, and store the result."""
    stored_payloads: list[dict[str, Any]] = []

    async def fake_create_token_check(
        _session: object,
        *,
        user_id: int,
        chain: str,
        contract_address: str,
        risk_level: RiskLevel,
        flags: dict[str, Any],
        raw_response: dict[str, Any],
    ) -> TokenCheck:
        """Capture repository input and return a TokenCheck object."""
        stored_payloads.append(
            {
                "user_id": user_id,
                "chain": chain,
                "contract_address": contract_address,
                "risk_level": risk_level,
                "flags": flags,
                "raw_response": raw_response,
            },
        )

        return TokenCheck(
            id=10,
            user_id=user_id,
            chain=chain,
            contract_address=contract_address,
            risk_level=risk_level,
            flags=flags,
            raw_response=raw_response,
            created_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
        )

    monkeypatch.setattr(
        token_risk_service,
        "create_token_check",
        fake_create_token_check,
    )

    provider = FakeTokenSecurityProvider(
        raw_data={
            "is_honeypot": "1",
        },
    )

    result = run_async(
        check_token_risk(
            object(),  # type: ignore[arg-type]
            data=TokenRiskCheckData(
                user_id=1,
                chain=" ETH ",
                contract_address=f" {UNKNOWN_ADDRESS} ",
            ),
            provider=provider,
        ),
    )

    assert provider.calls == [
        {
            "chain": " ETH ",
            "contract_address": f" {UNKNOWN_ADDRESS} ",
        },
    ]

    assert stored_payloads == [
        {
            "user_id": 1,
            "chain": "eth",
            "contract_address": UNKNOWN_ADDRESS,
            "risk_level": RiskLevel.HIGH,
            "flags": {"is_honeypot": True},
            "raw_response": {"is_honeypot": "1"},
        },
    ]

    assert isinstance(result, TokenCheck)
    assert result.id == 10
    assert result.risk_level == RiskLevel.HIGH
    assert result.flags == {"is_honeypot": True}


def test_check_token_risk_does_not_store_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider errors should propagate and skip database writes."""
    create_was_called = False

    async def fake_create_token_check(
        *_args: object,
        **_kwargs: object,
    ) -> TokenCheck:
        """Fail the test if storage is attempted."""
        nonlocal create_was_called
        create_was_called = True
        raise AssertionError("create_token_check should not be called")

    monkeypatch.setattr(
        token_risk_service,
        "create_token_check",
        fake_create_token_check,
    )

    with pytest.raises(SecurityProviderError):
        run_async(
            check_token_risk(
                object(),  # type: ignore[arg-type]
                data=TokenRiskCheckData(
                    user_id=1,
                    chain="eth",
                    contract_address=UNKNOWN_ADDRESS,
                ),
                provider=FailingTokenSecurityProvider(),
            ),
        )

    assert create_was_called is False
