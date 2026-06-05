import re
from decimal import Decimal

from app.core.constants import (
    MAX_ALERT_PRICE,
    MIN_ALERT_PRICE,
    SUPPORTED_CHAINS,
    SUPPORTED_COIN_IDS,
    SUPPORTED_COIN_SYMBOLS,
)
from app.core.error_messages import (
    INVALID_EVM_ADDRESS_ERROR,
    PRICE_TOO_HIGH_ERROR_TEMPLATE,
    PRICE_TOO_LOW_ERROR_TEMPLATE,
    UNSUPPORTED_CHAIN_ERROR_TEMPLATE,
    UNSUPPORTED_COIN_ID_ERROR_TEMPLATE,
    UNSUPPORTED_COIN_SYMBOL_ERROR_TEMPLATE,
)
from app.core.exceptions import ValidationError

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def normalize_symbol(symbol: str) -> str:
    """Normalize and validate a supported coin symbol."""
    normalized = symbol.strip().upper()

    if normalized not in SUPPORTED_COIN_SYMBOLS:
        supported_symbols = ", ".join(sorted(SUPPORTED_COIN_SYMBOLS))
        message = UNSUPPORTED_COIN_SYMBOL_ERROR_TEMPLATE.format(
            supported_symbols=supported_symbols,
        )
        raise ValidationError(message)

    return normalized


def normalize_coin_id(coin_id: str) -> str:
    """Normalize and validate a supported CoinGecko coin id."""
    normalized = coin_id.strip().lower()

    if normalized not in SUPPORTED_COIN_IDS:
        supported_coin_ids = ", ".join(sorted(SUPPORTED_COIN_IDS))
        message = UNSUPPORTED_COIN_ID_ERROR_TEMPLATE.format(
            supported_coin_ids=supported_coin_ids,
        )
        raise ValidationError(message)

    return normalized


def normalize_chain(chain: str) -> str:
    """Normalize and validate blockchain alias."""
    normalized = chain.strip().lower()

    if normalized not in SUPPORTED_CHAINS:
        supported_chains = ", ".join(sorted(SUPPORTED_CHAINS))
        message = UNSUPPORTED_CHAIN_ERROR_TEMPLATE.format(
            supported_chains=supported_chains,
        )
        raise ValidationError(message)

    return normalized


def validate_evm_address(address: str) -> str:
    """Validate an EVM contract address."""
    normalized = address.strip()

    if not EVM_ADDRESS_RE.fullmatch(normalized):
        raise ValidationError(INVALID_EVM_ADDRESS_ERROR)

    return normalized


def validate_alert_price_range(price: Decimal) -> Decimal:
    """Validate alert price range without changing precision."""
    if price < MIN_ALERT_PRICE:
        message = PRICE_TOO_LOW_ERROR_TEMPLATE.format(
            min_price=MIN_ALERT_PRICE,
        )
        raise ValidationError(message)

    if price > MAX_ALERT_PRICE:
        message = PRICE_TOO_HIGH_ERROR_TEMPLATE.format(
            max_price=MAX_ALERT_PRICE,
        )
        raise ValidationError(message)

    return price


def is_supported_coin_symbol(symbol: str) -> bool:
    """Return True if symbol is available for alerts."""
    return symbol.strip().upper() in SUPPORTED_COIN_SYMBOLS


def is_supported_coin_id(coin_id: str) -> bool:
    """Return True if CoinGecko coin id is available for alerts."""
    return coin_id.strip().lower() in SUPPORTED_COIN_IDS
