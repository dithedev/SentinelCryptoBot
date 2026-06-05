"""Schemas and parsing helpers for CoinGecko responses."""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.error_messages import COINGECKO_INVALID_RESPONSE_ERROR
from app.core.exceptions import PriceProviderError
from app.integrations.coingecko.constants import COINGECKO_USD_CURRENCY


def parse_simple_price_response(
    payload: dict[str, Any],
) -> dict[str, Decimal]:
    """Parse CoinGecko simple price response into a Decimal price map.

    Expected provider shape:

    {
        "bitcoin": {"usd": 100000},
        "ethereum": {"usd": 4000}
    }
    """
    prices: dict[str, Decimal] = {}

    for coin_id, coin_data in payload.items():
        if not isinstance(coin_data, dict):
            raise PriceProviderError(COINGECKO_INVALID_RESPONSE_ERROR)

        raw_price = coin_data.get(COINGECKO_USD_CURRENCY)

        if raw_price is None:
            continue

        try:
            prices[coin_id] = Decimal(str(raw_price))
        except (InvalidOperation, ValueError) as exc:
            raise PriceProviderError(COINGECKO_INVALID_RESPONSE_ERROR) from exc

    return prices
