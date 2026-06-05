"""Pydantic schemas for market price API responses."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MarketPriceResponse(BaseModel):
    """Public market price representation."""

    model_config = ConfigDict(from_attributes=True)

    coin_id: str
    symbol: str
    name: str
    price_usd: Decimal
