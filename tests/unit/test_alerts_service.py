from decimal import Decimal

from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.services.alerts_service import should_trigger_alert


def test_should_trigger_alert_returns_true_for_above_condition() -> None:
    alert = Alert(
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("100000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.ACTIVE,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("100001"),
    )

    assert result is True


def test_should_trigger_alert_returns_false_when_above_price_is_too_low() -> None:
    alert = Alert(
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("100000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.ACTIVE,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("99999"),
    )

    assert result is False


def test_should_trigger_alert_returns_true_for_below_condition() -> None:
    alert = Alert(
        coin_id="ethereum",
        symbol="ETH",
        target_price=Decimal("3000"),
        condition=AlertCondition.BELOW,
        status=AlertStatus.ACTIVE,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("2999"),
    )

    assert result is True


def test_should_trigger_alert_returns_false_when_below_price_is_too_high() -> None:
    alert = Alert(
        coin_id="ethereum",
        symbol="ETH",
        target_price=Decimal("3000"),
        condition=AlertCondition.BELOW,
        status=AlertStatus.ACTIVE,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("3001"),
    )

    assert result is False


def test_should_trigger_alert_returns_false_for_disabled_alert() -> None:
    alert = Alert(
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("100000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.DISABLED,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("200000"),
    )

    assert result is False


def test_should_trigger_alert_returns_false_for_triggered_alert() -> None:
    alert = Alert(
        coin_id="bitcoin",
        symbol="BTC",
        target_price=Decimal("100000"),
        condition=AlertCondition.ABOVE,
        status=AlertStatus.TRIGGERED,
        user_id=1,
    )

    result = should_trigger_alert(
        alert=alert,
        current_price=Decimal("200000"),
    )

    assert result is False
