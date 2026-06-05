"""Unit tests for the simulated whale event provider."""

from random import Random

import pytest
from app.database.models.whale import WhaleEventType
from app.integrations.whales import SimulatedWhaleProvider


@pytest.mark.asyncio
async def test_simulated_whale_provider_returns_configured_number_of_events() -> None:
    """The simulator should return the configured number of normalized events."""
    provider = SimulatedWhaleProvider(
        events_per_cycle=3,
        random=Random(1),
    )

    events = await provider.get_latest_events()

    assert len(events) == 3

    for event in events:
        assert event.coin_id
        assert event.network
        assert event.transaction_hash.startswith("sim-")
        assert event.amount > 0
        assert event.amount_usd > 0
        assert isinstance(event.event_type, WhaleEventType)
        assert event.raw_payload["source"] == "simulator"


@pytest.mark.asyncio
async def test_simulated_whale_provider_allows_zero_events() -> None:
    """Zero events per cycle is useful for tests and quiet local runs."""
    provider = SimulatedWhaleProvider(events_per_cycle=0)

    events = await provider.get_latest_events()

    assert events == []
