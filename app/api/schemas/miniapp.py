"""Pydantic schemas for Telegram Mini App API endpoints."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.database.models.alert import AlertCondition


class MiniAppUserResponse(BaseModel):
    """Current authenticated Mini App user."""

    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


class SupportedCoinResponse(BaseModel):
    """Coin available in the Mini App UI."""

    coin_id: str
    symbol: str
    name: str


class MiniAppConfigResponse(BaseModel):
    """Static config required by the Mini App frontend."""

    supported_coins: list[SupportedCoinResponse]
    alert_conditions: list[AlertCondition]
    supported_chains: list[str]


class MiniAppAlertCreateRequest(BaseModel):
    """Payload for creating an alert from authenticated Mini App user."""

    coin_id: str
    target_price: Decimal = Field(..., gt=0)
    condition: AlertCondition
