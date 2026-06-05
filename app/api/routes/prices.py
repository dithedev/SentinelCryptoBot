"""Market price API routes."""

import logging

from fastapi import APIRouter

from app.api.http_deps import HttpClient
from app.api.schemas import MarketPriceResponse
from app.integrations.coingecko import CoinGeckoClient
from app.services.prices_service import (
    get_coin_price,
    get_supported_market_prices,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=list[MarketPriceResponse])
async def list_prices(http_client: HttpClient) -> list[MarketPriceResponse]:
    """Return current USD prices for all supported coins."""
    provider = CoinGeckoClient(http_client=http_client)
    prices = await get_supported_market_prices(provider)

    return [MarketPriceResponse.model_validate(price) for price in prices]


@router.get("/{coin_id}", response_model=MarketPriceResponse)
async def get_price(
    coin_id: str,
    http_client: HttpClient,
) -> MarketPriceResponse:
    """Return current USD price for one supported coin."""
    provider = CoinGeckoClient(http_client=http_client)
    price = await get_coin_price(provider, coin_id=coin_id)

    return MarketPriceResponse.model_validate(price)
