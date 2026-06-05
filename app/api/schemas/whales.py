"""Pydantic schemas for whale alert Mini App API endpoints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.constants import MAX_WHALE_MIN_USD_VALUE, MIN_WHALE_MIN_USD_VALUE
from app.database.models.whale import WhaleEventType


class WhaleSettingsResponse(BaseModel):
    """Whale alert settings for the authenticated Mini App user."""

    id: int
    user_id: int
    is_enabled: bool
    min_usd_value: Decimal
    created_at: datetime
    updated_at: datetime


class WhaleSettingsUpdateRequest(BaseModel):
    """Payload for updating whale alert settings."""

    is_enabled: bool | None = None
    min_usd_value: Decimal | None = Field(
        default=None,
        ge=MIN_WHALE_MIN_USD_VALUE,
        le=MAX_WHALE_MIN_USD_VALUE,
    )


class WhaleEventResponse(BaseModel):
    """Stored whale event representation."""

    id: int
    coin_id: str
    symbol: str
    network: str
    transaction_hash: str
    from_address: str | None
    to_address: str | None
    amount: Decimal
    amount_usd: Decimal
    event_type: WhaleEventType
    detected_at: datetime
    created_at: datetime


class PaginatedWhaleEventsResponse(BaseModel):
    """Paginated whale event list response."""

    items: list[WhaleEventResponse]
    limit: int
    offset: int
    has_more: bool
