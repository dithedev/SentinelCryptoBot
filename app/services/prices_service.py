"""Market price service.

This service uses a provider interface instead of depending directly on
CoinGecko. That keeps the business logic testable and makes it easy to swap
providers later.
"""

import asyncio
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from app.core.constants import (
    MARKET_PRICES_API_CACHE_TTL_SECONDS,
    SUPPORTED_COINS,
)
from app.core.error_messages import PRICE_NOT_FOUND_ERROR_TEMPLATE
from app.core.exceptions import PriceProviderError
from app.utils.validators import normalize_coin_id


@dataclass(frozen=True)
class MarketPrice:
    """Normalized market price returned to API routes, bot, or worker."""

    coin_id: str
    symbol: str
    name: str
    price_usd: Decimal


class PriceProvider(Protocol):
    """Protocol that every market price provider must implement."""

    async def get_prices_usd(
        self,
        coin_ids: set[str],
    ) -> dict[str, Decimal]:
        """Return USD prices by CoinGecko coin id."""


@dataclass
class SupportedMarketPricesCache:
    """Small in-memory cache for public supported market prices.

    The cache is process-local. It protects CoinGecko from repeated requests
    when many API, bot, or Mini App users refresh prices at the same time.
    """

    ttl_seconds: int = MARKET_PRICES_API_CACHE_TTL_SECONDS
    _prices: list[MarketPrice] = field(default_factory=list)
    _updated_at: datetime | None = None

    def get(self) -> list[MarketPrice] | None:
        """Return cached prices when they are still fresh."""
        if not self._prices:
            return None

        if self.is_expired():
            return None

        return list(self._prices)

    def set(self, prices: list[MarketPrice]) -> None:
        """Store prices and refresh cache timestamp."""
        self._prices = list(prices)
        self._updated_at = datetime.now(UTC)

    def clear(self) -> None:
        """Clear all cached prices."""
        self._prices.clear()
        self._updated_at = None

    def is_expired(self) -> bool:
        """Return True when cache is empty or older than TTL."""
        if not self._prices:
            return True

        if self._updated_at is None:
            return True

        return datetime.now(UTC) >= self._get_expires_at()

    def get_remaining_ttl_seconds(self) -> int:
        """Return seconds until cached prices can be refreshed again.

        Zero means there is no usable cache or the cache has already expired.
        This helper is used by the Telegram bot to show a small callback popup
        instead of editing the message when Refresh is pressed too early.
        """
        if self.is_expired():
            return 0

        remaining = self._get_expires_at() - datetime.now(UTC)
        return max(0, math.ceil(remaining.total_seconds()))

    def _get_expires_at(self) -> datetime:
        """Return datetime when the current cache entry expires."""
        if self._updated_at is None:
            return datetime.now(UTC)

        return self._updated_at + timedelta(seconds=self.ttl_seconds)


_supported_market_prices_cache = SupportedMarketPricesCache()
_supported_market_prices_cache_lock = asyncio.Lock()


def get_supported_market_prices_cache_remaining_seconds() -> int:
    """Return seconds until supported market prices cache expires.

    This function intentionally exposes only cache timing, not the cached data.
    Consumers still use get_supported_market_prices to load the actual prices.
    """
    return _supported_market_prices_cache.get_remaining_ttl_seconds()


async def get_supported_market_prices(
    provider: PriceProvider,
) -> list[MarketPrice]:
    """Return prices for all coins supported by this application.

    The public prices endpoint can be refreshed by many users. To avoid hitting
    the external provider too often, this function uses a short shared backend
    cache. If several requests arrive at once after cache expiry, only the
    first one fetches fresh data while the others wait and reuse the new result.
    """
    cached_prices = _supported_market_prices_cache.get()

    if cached_prices is not None:
        return cached_prices

    async with _supported_market_prices_cache_lock:
        cached_prices = _supported_market_prices_cache.get()

        if cached_prices is not None:
            return cached_prices

        fresh_prices = await _fetch_supported_market_prices(provider)
        _supported_market_prices_cache.set(fresh_prices)

        return fresh_prices


async def _fetch_supported_market_prices(
    provider: PriceProvider,
) -> list[MarketPrice]:
    """Fetch supported market prices directly from the provider."""
    coin_ids = {coin.coin_id for coin in SUPPORTED_COINS}
    prices = await provider.get_prices_usd(coin_ids)

    result: list[MarketPrice] = []

    for coin in SUPPORTED_COINS:
        price = prices.get(coin.coin_id)

        if price is None:
            continue

        result.append(
            MarketPrice(
                coin_id=coin.coin_id,
                symbol=coin.symbol,
                name=coin.name,
                price_usd=price,
            ),
        )

    return result


async def get_coin_price(
    provider: PriceProvider,
    *,
    coin_id: str,
) -> MarketPrice:
    """Return price for one supported coin or raise a provider error."""
    normalized_coin_id = normalize_coin_id(coin_id)

    for market_price in await get_supported_market_prices(provider):
        if market_price.coin_id == normalized_coin_id:
            return market_price

    message = PRICE_NOT_FOUND_ERROR_TEMPLATE.format(
        coin_id=normalized_coin_id,
    )
    raise PriceProviderError(message)


async def get_price_map_for_alerts(
    provider: PriceProvider,
    *,
    coin_ids: set[str],
) -> dict[str, Decimal]:
    """Return a normalized price map for alert checking."""
    normalized_coin_ids = {normalize_coin_id(coin_id) for coin_id in coin_ids}

    if not normalized_coin_ids:
        return {}

    return await provider.get_prices_usd(normalized_coin_ids)
