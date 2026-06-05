"""Async CoinGecko API client."""

from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.error_messages import (
    COINGECKO_INVALID_RESPONSE_ERROR,
    COINGECKO_REQUEST_FAILED_ERROR,
)
from app.core.exceptions import PriceProviderError
from app.integrations.coingecko.constants import (
    COINGECKO_REQUEST_TIMEOUT_SECONDS,
    COINGECKO_SIMPLE_PRICE_PATH,
    COINGECKO_USD_CURRENCY,
)
from app.integrations.coingecko.schemas import parse_simple_price_response


class CoinGeckoClient:
    """Small provider client for market prices.

    The class implements the PriceProvider protocol from prices_service.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = COINGECKO_REQUEST_TIMEOUT_SECONDS,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()

        self._base_url = (base_url or settings.coingecko_base_url).rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client

    async def get_prices_usd(
        self,
        coin_ids: set[str],
    ) -> dict[str, Decimal]:
        """Return USD prices by CoinGecko coin id."""
        if not coin_ids:
            return {}

        payload = await self._get_simple_price_payload(coin_ids)
        return parse_simple_price_response(payload)

    async def _get_simple_price_payload(
        self,
        coin_ids: set[str],
    ) -> dict[str, Any]:
        """Fetch raw simple price payload from CoinGecko."""
        url = f"{self._base_url}{COINGECKO_SIMPLE_PRICE_PATH}"

        params = {
            "ids": ",".join(sorted(coin_ids)),
            "vs_currencies": COINGECKO_USD_CURRENCY,
        }

        try:
            if self._http_client is not None:
                response = await self._http_client.get(
                    url,
                    params=params,
                    timeout=self._timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds,
                ) as client:
                    response = await client.get(url, params=params)

            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PriceProviderError(COINGECKO_REQUEST_FAILED_ERROR) from exc

        payload = response.json()

        if not isinstance(payload, dict):
            raise PriceProviderError(COINGECKO_INVALID_RESPONSE_ERROR)

        return payload
