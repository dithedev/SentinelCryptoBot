"""Whale event provider contract and factory.

Worker and future real integrations depend on this module instead of importing
concrete provider classes directly from the worker layer.
"""

from typing import Protocol

from app.core.config import Settings
from app.integrations.whales.schemas import WhaleProviderEvent
from app.integrations.whales.simulator import SimulatedWhaleProvider

WHALE_PROVIDER_SIMULATED = "simulated"


class WhaleEventProvider(Protocol):
    """Protocol for whale event providers."""

    async def get_latest_events(self) -> list[WhaleProviderEvent]:
        """Return latest whale events from a provider."""
        ...


def build_whale_event_provider(settings: Settings) -> WhaleEventProvider:
    """Build a whale provider from application settings.

    Only the simulated provider is implemented for the portfolio MVP. Later a
    real adapter can be added here without changing worker notification logic.
    """
    provider_name = settings.whale_provider.strip().lower()

    if provider_name == WHALE_PROVIDER_SIMULATED:
        return SimulatedWhaleProvider(
            events_per_cycle=settings.whale_simulated_events_per_cycle,
        )

    raise ValueError(f"Unsupported whale provider: {settings.whale_provider}")
