"""Pydantic schemas for price alert API endpoints."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.database.models.alert import AlertCondition, AlertStatus


class AlertResponse(BaseModel):
    """Price alert representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    coin_id: str
    symbol: str
    target_price: Decimal
    condition: AlertCondition
    status: AlertStatus
    triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PaginatedAlertsResponse(BaseModel):
    """Paginated alert list response.

    The API returns has_more instead of total count because it is cheaper and
    enough for a mobile Load more interface.
    """

    items: list[AlertResponse]
    limit: int
    offset: int
    has_more: bool


class AlertActionResponse(BaseModel):
    """Response returned after an alert action."""

    message: str
