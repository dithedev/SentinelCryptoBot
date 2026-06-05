"""Message builders for price alert texts."""

from datetime import datetime
from decimal import Decimal

from app.bot.text_builders.labels import (
    get_alert_condition_label,
    get_alert_status_emoji,
    get_alert_status_label,
)
from app.bot.texts.alerts import (
    ALERT_BUTTON_TITLE_TEMPLATE,
    ALERT_CREATED_TEMPLATE,
    ALERT_DETAILS_TEMPLATE,
    ALERT_FILTER_ACTIVE_TITLE,
    ALERT_FILTER_ALL_TITLE,
    ALERT_FILTER_HISTORY_TITLE,
    ALERT_TITLE_TEMPLATE,
    ALERT_TRIGGERED_LINE_TEMPLATE,
    ALERT_TRIGGERED_TEMPLATE,
    ALERTS_PAGE_DESCRIPTION,
    ALERTS_PAGE_EMPTY_TEMPLATE,
    ALERTS_PAGE_TEXT_TEMPLATE,
    ALERTS_PAGE_TITLE_TEMPLATE,
)
from app.database.models.alert import Alert, AlertCondition, AlertStatus
from app.utils.money import format_price

ALERT_FILTER_ACTIVE = "active"
ALERT_FILTER_ALL = "all"
ALERT_FILTER_HISTORY = ALERT_FILTER_ALL

# Kept for backward callback/import compatibility. New keyboards do not render it.
ALERT_FILTER_TRIGGERED = "triggered"

ALERT_FILTER_TITLES: dict[str, str] = {
    ALERT_FILTER_ACTIVE: ALERT_FILTER_ACTIVE_TITLE,
    ALERT_FILTER_ALL: ALERT_FILTER_HISTORY_TITLE,
}


def build_alert_title(alert: Alert) -> str:
    """Build a short alert title for messages."""
    return ALERT_TITLE_TEMPLATE.format(
        symbol=alert.symbol,
        condition=get_alert_condition_label(alert.condition),
        price=format_price(alert.target_price),
    )


def build_alert_button_title(
    alert: Alert,
    *,
    show_status_emoji: bool,
) -> str:
    """Build alert button text.

    Status emoji can be enabled by the keyboard builder for any alert list.
    This keeps the text format consistent between Active and History filters.
    """
    status_prefix = ""

    if show_status_emoji:
        status_prefix = f"{get_alert_status_emoji(alert.status)} "

    return ALERT_BUTTON_TITLE_TEMPLATE.format(
        status_prefix=status_prefix,
        symbol=alert.symbol,
        condition=get_alert_condition_label(alert.condition),
        price=format_price(alert.target_price),
    )


def build_alert_details_text(alert: Alert) -> str:
    """Build a compact alert details message.

    The details card intentionally shows only the title, status, creation date,
    and trigger date when the alert has already been triggered.
    """
    return ALERT_DETAILS_TEMPLATE.format(
        title=build_alert_title(alert),
        status=get_alert_status_label(alert.status),
        created_at=format_alert_datetime(alert.created_at),
        triggered_line=build_alert_triggered_line(alert),
    )


def build_alert_triggered_line(alert: Alert) -> str:
    """Build the triggered date line only for triggered alerts."""
    if alert.triggered_at is None:
        return ""

    return ALERT_TRIGGERED_LINE_TEMPLATE.format(
        triggered_at=format_alert_datetime(alert.triggered_at),
    )


def build_alert_created_text(alert: Alert) -> str:
    """Build text shown after successful alert creation."""
    return ALERT_CREATED_TEMPLATE.format(
        title=build_alert_title(alert),
    )


def build_alert_triggered_text(
    *,
    symbol: str,
    condition: AlertCondition,
    target_price: Decimal,
    current_price: Decimal,
) -> str:
    """Build notification text for a triggered alert."""
    return ALERT_TRIGGERED_TEMPLATE.format(
        symbol=symbol,
        condition=get_alert_condition_label(condition),
        target_price=format_price(target_price),
        current_price=format_price(current_price),
    )


def build_alerts_page_text(
    *,
    alerts: list[Alert],
    selected_alert: Alert | None = None,
) -> str:
    """Build the main message for the paginated My alerts screen.

    When no alert is selected, the message explains filters and details.
    When an alert is selected, its details replace the explanation text.
    """
    if selected_alert is not None:
        return build_alert_details_text(selected_alert)

    empty_line = ""

    if not alerts:
        empty_line = ALERTS_PAGE_EMPTY_TEMPLATE

    return ALERTS_PAGE_TEXT_TEMPLATE.format(
        title=ALERTS_PAGE_TITLE_TEMPLATE,
        description=ALERTS_PAGE_DESCRIPTION,
        empty_line=empty_line,
    ).rstrip()


def get_alert_filter_title(filter_value: str) -> str:
    """Return a user-facing title for a bot alert filter."""
    return ALERT_FILTER_TITLES.get(filter_value, ALERT_FILTER_ALL_TITLE)


def get_alert_status_filter(filter_value: str) -> AlertStatus | None:
    """Convert a bot filter value into an AlertStatus filter.

    None means full alert history.
    """
    if filter_value == ALERT_FILTER_ACTIVE:
        return AlertStatus.ACTIVE

    return None


def normalize_alert_filter(filter_value: str) -> str:
    """Return a safe alert filter value for callback payloads.

    The old triggered filter is intentionally normalized to History because the
    bot now has only two visible filters: Active and History.
    """
    if filter_value in ALERT_FILTER_TITLES:
        return filter_value

    return ALERT_FILTER_ALL


def format_alert_datetime(value: datetime) -> str:
    """Format alert datetime for compact Telegram messages."""
    return value.strftime("%Y-%m-%d %H:%M")
