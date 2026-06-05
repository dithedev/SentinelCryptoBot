"""Local whale event simulator.

The project does not depend on a paid whale-tracking API for the portfolio MVP.
This simulator produces realistic-looking events through the same provider
interface that a real integration can implement later.
"""

from datetime import UTC, datetime
from decimal import Decimal
from random import Random
from uuid import uuid4

from app.core.constants import SUPPORTED_COINS
from app.database.models.whale import WhaleEventType
from app.integrations.whales.schemas import WhaleProviderEvent

DEFAULT_SIMULATED_WHALE_EVENTS_PER_CYCLE = 1

SIMULATED_WHALE_AMOUNT_USD_VALUES: tuple[Decimal, ...] = (
    Decimal("250000"),
    Decimal("750000"),
    Decimal("1250000"),
    Decimal("2500000"),
    Decimal("5000000"),
    Decimal("10000000"),
)

SIMULATED_WHALE_EVENT_TYPES: tuple[WhaleEventType, ...] = (
    WhaleEventType.TRANSFER,
    WhaleEventType.EXCHANGE_INFLOW,
    WhaleEventType.EXCHANGE_OUTFLOW,
)

NETWORK_BY_COIN_ID: dict[str, str] = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "the-open-network": "ton",
    "solana": "sol",
    "binancecoin": "bsc",
}


class SimulatedWhaleProvider:
    """Generate demo whale events.

    A dedicated provider class keeps the worker independent from event source.
    Later this class can be replaced with Arkham, Whale Alert, Etherscan, or
    any other real data provider without changing notification logic.
    """

    def __init__(
        self,
        *,
        events_per_cycle: int = DEFAULT_SIMULATED_WHALE_EVENTS_PER_CYCLE,
        random: Random | None = None,
    ) -> None:
        self._events_per_cycle = max(events_per_cycle, 0)
        self._random = random or Random()

    async def get_latest_events(self) -> list[WhaleProviderEvent]:
        """Return simulated whale events for one worker cycle."""
        return [self._build_event() for _ in range(self._events_per_cycle)]

    def _build_event(self) -> WhaleProviderEvent:
        """Build one realistic-looking simulated whale event."""
        coin = self._random.choice(SUPPORTED_COINS)
        amount_usd = self._random.choice(SIMULATED_WHALE_AMOUNT_USD_VALUES)
        token_price = self._get_demo_token_price(coin.coin_id)
        amount = (amount_usd / token_price).quantize(Decimal("0.000000000000000001"))
        event_type = self._random.choice(SIMULATED_WHALE_EVENT_TYPES)
        detected_at = datetime.now(UTC)
        transaction_hash = self._build_transaction_hash()

        return WhaleProviderEvent(
            coin_id=coin.coin_id,
            network=NETWORK_BY_COIN_ID.get(coin.coin_id, coin.symbol.lower()),
            transaction_hash=transaction_hash,
            amount=amount,
            amount_usd=amount_usd,
            event_type=event_type,
            from_address=self._build_demo_address("from"),
            to_address=self._build_demo_address("to"),
            detected_at=detected_at,
            raw_payload={
                "source": "simulator",
                "coin_id": coin.coin_id,
                "symbol": coin.symbol,
                "amount_usd": str(amount_usd),
                "event_type": event_type.value,
                "detected_at": detected_at.isoformat(),
                "transaction_hash": transaction_hash,
            },
        )

    def _get_demo_token_price(self, coin_id: str) -> Decimal:
        """Return a rough demo price used only to calculate token amount."""
        demo_prices = {
            "bitcoin": Decimal("100000"),
            "ethereum": Decimal("3500"),
            "the-open-network": Decimal("5"),
            "solana": Decimal("180"),
            "binancecoin": Decimal("650"),
        }

        return demo_prices.get(coin_id, Decimal("1"))

    def _build_transaction_hash(self) -> str:
        """Build a unique transaction-like id."""
        return f"sim-{uuid4().hex}"

    def _build_demo_address(self, prefix: str) -> str:
        """Build a short readable simulated address."""
        return f"{prefix}-{uuid4().hex[:16]}"
