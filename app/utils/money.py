from decimal import ROUND_DOWN, Decimal, InvalidOperation

from app.core.constants import (
    MAX_ALERT_PRICE,
    MAX_WHALE_MIN_USD_VALUE,
    MIN_ALERT_PRICE,
    MIN_WHALE_MIN_USD_VALUE,
)
from app.core.error_messages import (
    PRICE_EMPTY_ERROR,
    PRICE_INVALID_NUMBER_ERROR,
    PRICE_TOO_HIGH_ERROR_TEMPLATE,
    PRICE_TOO_LOW_ERROR_TEMPLATE,
    WHALE_MIN_USD_VALUE_TOO_HIGH_ERROR_TEMPLATE,
    WHALE_MIN_USD_VALUE_TOO_LOW_ERROR_TEMPLATE,
)
from app.core.exceptions import ValidationError

PRICE_QUANT = Decimal("0.00000001")
USD_QUANT = Decimal("0.01")


def parse_decimal(value: str) -> Decimal:
    """Parse user input into Decimal.

    Commas are accepted because users often type prices like 100,5.
    """
    cleaned_value = value.strip().replace(",", ".")

    if not cleaned_value:
        raise ValidationError(PRICE_EMPTY_ERROR)

    try:
        return Decimal(cleaned_value)
    except InvalidOperation as exc:
        raise ValidationError(PRICE_INVALID_NUMBER_ERROR) from exc


def normalize_price(value: Decimal) -> Decimal:
    """Normalize a price to 8 decimal places."""
    return value.quantize(PRICE_QUANT, rounding=ROUND_DOWN)


def validate_alert_price(value: Decimal) -> Decimal:
    """Validate and normalize a user alert price."""
    if value < MIN_ALERT_PRICE:
        message = PRICE_TOO_LOW_ERROR_TEMPLATE.format(
            min_price=MIN_ALERT_PRICE,
        )
        raise ValidationError(message)

    if value > MAX_ALERT_PRICE:
        message = PRICE_TOO_HIGH_ERROR_TEMPLATE.format(
            max_price=MAX_ALERT_PRICE,
        )
        raise ValidationError(message)

    return normalize_price(value)


def parse_alert_price(value: str) -> Decimal:
    """Parse, validate, and normalize user price input."""
    parsed = parse_decimal(value)
    return validate_alert_price(parsed)


def validate_whale_min_usd_value(value: Decimal) -> Decimal:
    """Validate and normalize a whale alert threshold."""
    if value < MIN_WHALE_MIN_USD_VALUE:
        message = WHALE_MIN_USD_VALUE_TOO_LOW_ERROR_TEMPLATE.format(
            min_value=MIN_WHALE_MIN_USD_VALUE,
        )
        raise ValidationError(message)

    if value > MAX_WHALE_MIN_USD_VALUE:
        message = WHALE_MIN_USD_VALUE_TOO_HIGH_ERROR_TEMPLATE.format(
            max_value=MAX_WHALE_MIN_USD_VALUE,
        )
        raise ValidationError(message)

    return value.quantize(USD_QUANT)


def parse_whale_min_usd_value(value: str) -> Decimal:
    """Parse, validate, and normalize whale threshold input."""
    parsed = parse_decimal(value)
    return validate_whale_min_usd_value(parsed)


def format_price(value: Decimal | float | int | str) -> str:
    """Format price for user-facing messages.

    The formatting logic is kept here, but all surrounding text lives in
    app.bot.texts.
    """
    decimal_value = Decimal(str(value))

    if decimal_value >= Decimal("1"):
        formatted = f"{decimal_value:,.2f}"
    else:
        formatted = f"{decimal_value:.8f}"

    return formatted.rstrip("0").rstrip(".")
