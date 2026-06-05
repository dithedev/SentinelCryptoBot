"""Unit tests for whale notification text rendering."""

from datetime import UTC, datetime
from decimal import Decimal

from app.bot.text_builders.whales import (
    build_whale_alert_notification_text,
    build_whale_event_card_text,
    build_whales_menu_text,
)
from app.database.models.whale import WhaleAlertSettings, WhaleEvent, WhaleEventType


def test_build_whale_alert_notification_text_contains_event_data() -> None:
    """Whale notification text should contain all key event details."""
    event = WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="0xabc",
        from_address="from",
        to_address="to",
        amount=Decimal("12.5"),
        amount_usd=Decimal("1250000"),
        event_type=WhaleEventType.EXCHANGE_OUTFLOW,
        detected_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        raw_payload={},
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )

    text = build_whale_alert_notification_text(event)

    assert "Whale movement detected" in text
    assert "Exchange outflow" in text
    assert "BTC" in text
    assert "BTC" in text
    assert "$1,250,000" in text
    assert "0xabc" in text


def test_build_whales_menu_text_contains_status_and_threshold() -> None:
    """Whale menu text should show current status and threshold."""
    settings = WhaleAlertSettings(
        id=1,
        user_id=1,
        is_enabled=True,
        min_usd_value=Decimal("1000000"),
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )

    text = build_whales_menu_text(settings)

    assert "Enabled" in text
    assert "1,000,000" in text
    assert "simulated whale provider" in text
    assert "BTC, ETH, TON, SOL, BNB" in text
    assert "Large transfer" in text
    assert "Exchange inflow" in text
    assert "Exchange outflow" in text


def test_build_whale_event_card_text_contains_event_details() -> None:
    """Whale event card should contain compact event details."""
    event = WhaleEvent(
        id=1,
        coin_id="bitcoin",
        symbol="BTC",
        network="btc",
        transaction_hash="sim-abc",
        from_address=None,
        to_address=None,
        amount=Decimal("10"),
        amount_usd=Decimal("1500000"),
        event_type=WhaleEventType.EXCHANGE_OUTFLOW,
        detected_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
        raw_payload={},
        created_at=datetime(2026, 5, 20, 10, 0, tzinfo=UTC),
    )

    text = build_whale_event_card_text(event)

    assert "Exchange outflow" in text
    assert "BTC" in text
    assert "1,500,000" in text
