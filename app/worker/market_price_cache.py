"""In-memory market price cache.

The cache is intentionally simple. It reduces repeated external API calls while
keeping the project easy to understand for an open-source portfolio demo.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.worker.constants import MARKET_PRICE_CACHE_TTL_SECONDS


@dataclass
class MarketPriceCache:
    """Small TTL cache for market prices."""

    ttl_seconds: int = MARKET_PRICE_CACHE_TTL_SECONDS
    _prices: dict[str, Decimal] = field(default_factory=dict)
    _updated_at: datetime | None = None

    def get_many(self, coin_ids: set[str]) -> dict[str, Decimal] | None:
        """Return cached prices if all requested coin ids are present."""
        if not coin_ids:
            return {}

        if self.is_expired():
            return None

        missing_coin_ids = coin_ids - set(self._prices)

        if missing_coin_ids:
            return None

        return {coin_id: self._prices[coin_id] for coin_id in coin_ids}

    def set_many(self, prices: dict[str, Decimal]) -> None:
        """Store prices and refresh cache timestamp."""
        self._prices.update(prices)
        self._updated_at = datetime.now(UTC)

    def clear(self) -> None:
        """Clear all cached prices."""
        self._prices.clear()
        self._updated_at = None

    def is_expired(self) -> bool:
        """Return True when cache is empty or older than TTL."""
        if self._updated_at is None:
            return True

        expires_at = self._updated_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(UTC) >= expires_at
