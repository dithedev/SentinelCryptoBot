"""Whale API presenters."""

from app.api.schemas import WhaleEventResponse, WhaleSettingsResponse
from app.database.models.whale import WhaleAlertSettings, WhaleEvent


def to_whale_settings_response(
    settings: WhaleAlertSettings,
) -> WhaleSettingsResponse:
    """Convert WhaleAlertSettings ORM object into an API response schema."""
    return WhaleSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        is_enabled=settings.is_enabled,
        min_usd_value=settings.min_usd_value,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


def to_whale_event_response(event: WhaleEvent) -> WhaleEventResponse:
    """Convert WhaleEvent ORM object into an API response schema."""
    return WhaleEventResponse(
        id=event.id,
        coin_id=event.coin_id,
        symbol=event.symbol,
        network=event.network,
        transaction_hash=event.transaction_hash,
        from_address=event.from_address,
        to_address=event.to_address,
        amount=event.amount,
        amount_usd=event.amount_usd,
        event_type=event.event_type,
        detected_at=event.detected_at,
        created_at=event.created_at,
    )


def to_whale_event_response_list(events: list[WhaleEvent]) -> list[WhaleEventResponse]:
    """Convert a list of WhaleEvent ORM objects into API response schemas."""
    return [to_whale_event_response(event) for event in events]
