"""Normalized schemas for whale event providers."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.database.models.whale import WhaleEventType


@dataclass(frozen=True)
class WhaleProviderEvent:
    """Provider-independent whale event payload.

    The worker receives events in this normalized shape regardless of whether
    events came from a real API later or from the local simulator now.
    """

    coin_id: str
    network: str
    transaction_hash: str
    amount: Decimal
    amount_usd: Decimal
    event_type: WhaleEventType
    from_address: str | None = None
    to_address: str | None = None
    detected_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
