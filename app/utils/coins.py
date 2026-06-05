"""Helpers for supported coin metadata."""

from app.core.constants import SUPPORTED_COIN_IDS, SUPPORTED_COINS_BY_ID
from app.core.error_messages import UNSUPPORTED_COIN_ID_ERROR_TEMPLATE
from app.core.exceptions import ValidationError


def get_coin_symbol(coin_id: str) -> str:
    """Return the display symbol for a supported coin id."""
    coin = SUPPORTED_COINS_BY_ID.get(coin_id)

    if coin is None:
        message = UNSUPPORTED_COIN_ID_ERROR_TEMPLATE.format(
            supported_coin_ids=", ".join(sorted(SUPPORTED_COIN_IDS)),
        )
        raise ValidationError(message)

    return coin.symbol
