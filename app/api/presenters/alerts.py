"""Alert API presenters.

Presenters convert ORM/domain objects into API response schemas.

Keeping this mapping outside route modules makes routes thinner and prevents
duplicating response formatting logic across Mini App and future API endpoints.
"""

from app.api.schemas import AlertResponse
from app.database.models.alert import Alert


def to_alert_response(alert: Alert) -> AlertResponse:
    """Convert an Alert ORM object into an API response schema."""
    return AlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        coin_id=alert.coin_id,
        symbol=alert.symbol,
        target_price=alert.target_price,
        condition=alert.condition,
        status=alert.status,
        triggered_at=alert.triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def to_alert_response_list(alerts: list[Alert]) -> list[AlertResponse]:
    """Convert a list of Alert ORM objects into API response schemas."""
    return [to_alert_response(alert) for alert in alerts]
