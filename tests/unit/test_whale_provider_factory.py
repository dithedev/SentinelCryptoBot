"""Unit tests for whale provider factory and settings."""

from dataclasses import dataclass

import pytest
from app.core.config import Settings
from app.integrations.whales import (
    WHALE_PROVIDER_SIMULATED,
    SimulatedWhaleProvider,
    build_whale_event_provider,
)
from pydantic import ValidationError as PydanticValidationError


@dataclass
class FakeWhaleSettings:
    """Minimal settings object for provider factory tests."""

    whale_provider: str = WHALE_PROVIDER_SIMULATED
    whale_simulated_events_per_cycle: int = 1


def test_build_whale_event_provider_returns_simulated_provider() -> None:
    """Simulated provider should be selected by default."""
    settings = FakeWhaleSettings(whale_provider=WHALE_PROVIDER_SIMULATED)

    provider = build_whale_event_provider(settings)  # type: ignore[arg-type]

    assert isinstance(provider, SimulatedWhaleProvider)


def test_build_whale_event_provider_rejects_unknown_provider() -> None:
    """Unsupported provider names should fail fast at startup."""
    settings = FakeWhaleSettings(whale_provider="real_whale_alert")

    with pytest.raises(ValueError, match="Unsupported whale provider"):
        build_whale_event_provider(settings)  # type: ignore[arg-type]


def test_settings_validate_whale_check_interval() -> None:
    """Too small whale worker intervals should be rejected."""
    with pytest.raises(PydanticValidationError):
        Settings(
            BOT_TOKEN="123456:TEST",
            DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/test",
            WHALE_CHECK_INTERVAL_SECONDS=5,
        )
