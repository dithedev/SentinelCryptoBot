from decimal import Decimal

import pytest
from app.core.exceptions import ValidationError
from app.utils.money import format_price, parse_alert_price
from app.utils.validators import (
    normalize_chain,
    normalize_coin_id,
    normalize_symbol,
    validate_alert_price_range,
    validate_evm_address,
)


def test_normalize_symbol_accepts_supported_symbol() -> None:
    assert normalize_symbol(" btc ") == "BTC"


def test_normalize_symbol_rejects_unsupported_symbol() -> None:
    with pytest.raises(ValidationError):
        normalize_symbol("DOGE")


def test_normalize_coin_id_accepts_supported_coin_id() -> None:
    assert normalize_coin_id(" Bitcoin ") == "bitcoin"


def test_normalize_coin_id_rejects_unsupported_coin_id() -> None:
    with pytest.raises(ValidationError):
        normalize_coin_id("dogecoin")


def test_normalize_chain_accepts_supported_chain() -> None:
    assert normalize_chain(" ETH ") == "eth"


def test_normalize_chain_rejects_unsupported_chain() -> None:
    with pytest.raises(ValidationError):
        normalize_chain("ton")


def test_validate_evm_address_accepts_valid_address() -> None:
    address = "0x0000000000000000000000000000000000000000"

    assert validate_evm_address(address) == address


def test_validate_evm_address_rejects_invalid_address() -> None:
    with pytest.raises(ValidationError):
        validate_evm_address("not-a-contract")


def test_validate_alert_price_range_accepts_valid_price() -> None:
    price = Decimal("100.50")

    assert validate_alert_price_range(price) == price


def test_validate_alert_price_range_rejects_too_low_price() -> None:
    with pytest.raises(ValidationError):
        validate_alert_price_range(Decimal("0"))


def test_validate_alert_price_range_rejects_too_high_price() -> None:
    with pytest.raises(ValidationError):
        validate_alert_price_range(Decimal("1000000001"))


def test_parse_alert_price_accepts_comma_decimal_separator() -> None:
    assert parse_alert_price("100,50") == Decimal("100.50000000")


def test_parse_alert_price_rejects_empty_value() -> None:
    with pytest.raises(ValidationError):
        parse_alert_price("   ")


def test_format_price_formats_large_price() -> None:
    assert format_price(Decimal("1234.50000000")) == "1,234.5"


def test_format_price_formats_small_price() -> None:
    assert format_price(Decimal("0.00001234")) == "0.00001234"
