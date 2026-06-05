"""Unit tests for price alert message builders."""

from decimal import Decimal

from app.bot.text_builders.alerts import build_alert_triggered_text
from app.database.models.alert import AlertCondition


def test_build_alert_triggered_text_bolds_labels_not_prices() -> None:
    """Target and current labels should be bold while prices stay plain."""
    text = build_alert_triggered_text(
        symbol="BTC",
        condition=AlertCondition.ABOVE,
        target_price=Decimal("50000"),
        current_price=Decimal("60000"),
    )

    assert "<b>Target:</b> $50,000" in text
    assert "<b>Current:</b> $60,000" in text
    assert "<b>Target: $50,000</b>" not in text
