"""Message builders for bot market price texts."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from app.bot.texts.prices import (
    PRICE_ROW_TEMPLATE,
    PRICES_DESCRIPTION,
    PRICES_EMPTY_TEXT,
    PRICES_TEXT_TEMPLATE,
    PRICES_TITLE,
)
from app.utils.money import format_price


class MarketPriceLike(Protocol):
    """Minimal read-only market price shape required by the text builder.

    The builder does not need the concrete MarketPrice dataclass. It only needs
    a symbol and a USD price. Read-only properties avoid mypy invariance issues
    when callers pass list[MarketPrice].
    """

    @property
    def symbol(self) -> str:
        """Return the coin symbol shown to the user."""

    @property
    def price_usd(self) -> Decimal | float | int | str:
        """Return the USD price value accepted by format_price."""


def build_market_prices_text(prices: Sequence[MarketPriceLike]) -> str:
    """Build a compact Telegram message with supported market prices.

    Sequence is used because the builder only reads items. This also allows
    callers to pass list[MarketPrice] without exposing the concrete service
    dataclass to the bot text builder.
    """
    if not prices:
        return PRICES_EMPTY_TEXT

    rows = "\n".join(
        PRICE_ROW_TEMPLATE.format(
            symbol=price.symbol,
            price=format_price(price.price_usd),
        )
        for price in prices
    )

    return PRICES_TEXT_TEMPLATE.format(
        title=PRICES_TITLE,
        description=PRICES_DESCRIPTION,
        rows=rows,
    )
