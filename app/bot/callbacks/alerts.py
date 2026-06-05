"""Callback payload helpers for price alert screens.

Routers and keyboard builders should not manually build or parse callback data.
Keeping callback serialization here makes button payloads consistent and easier
to change later.
"""

from dataclasses import dataclass

from app.bot.constants import (
    CB_ALERTS_DELETE_PREFIX,
    CB_ALERTS_PAGE_PREFIX,
    CB_ALERTS_VIEW_PREFIX,
)
from app.bot.text_builders.alerts import ALERT_FILTER_ALL, normalize_alert_filter


@dataclass(frozen=True)
class AlertPagePayload:
    """Parsed payload for opening a paginated alert list."""

    filter_value: str
    page_number: int


@dataclass(frozen=True)
class AlertActionPayload:
    """Parsed payload for an alert row action."""

    alert_id: int | None
    filter_value: str
    page_number: int
    selected_alert_id: int | None


def build_alert_page_callback(
    *,
    filter_value: str,
    page_number: int,
) -> str:
    """Build callback data for opening a selected alert page."""
    safe_filter = normalize_alert_filter(filter_value)
    safe_page_number = max(page_number, 0)

    return f"{CB_ALERTS_PAGE_PREFIX}{safe_filter}:{safe_page_number}"


def build_alert_view_callback(
    *,
    alert_id: int,
    filter_value: str,
    page_number: int,
    selected_alert_id: int | None = None,
) -> str:
    """Build callback data for toggling inline alert details."""
    safe_filter = normalize_alert_filter(filter_value)
    safe_page_number = max(page_number, 0)
    safe_selected_alert_id = selected_alert_id or 0

    return (
        f"{CB_ALERTS_VIEW_PREFIX}"
        f"{alert_id}:{safe_filter}:{safe_page_number}:{safe_selected_alert_id}"
    )


def build_alert_delete_callback(
    *,
    alert_id: int,
    filter_value: str,
    page_number: int,
    selected_alert_id: int | None = None,
) -> str:
    """Build callback data for deleting an alert from the inline list."""
    safe_filter = normalize_alert_filter(filter_value)
    safe_page_number = max(page_number, 0)
    safe_selected_alert_id = selected_alert_id or 0

    return (
        f"{CB_ALERTS_DELETE_PREFIX}"
        f"{alert_id}:{safe_filter}:{safe_page_number}:{safe_selected_alert_id}"
    )


def parse_alert_page_payload(payload: str) -> AlertPagePayload:
    """Parse page callback payload.

    Expected raw format after prefix removal:
    filter:page

    Invalid data safely falls back to the first page of all alerts.
    """
    parts = payload.split(":", maxsplit=1)

    if len(parts) != 2:
        return AlertPagePayload(
            filter_value=ALERT_FILTER_ALL,
            page_number=0,
        )

    return AlertPagePayload(
        filter_value=normalize_alert_filter(parts[0]),
        page_number=_parse_non_negative_int(parts[1]),
    )


def parse_alert_action_payload(payload: str) -> AlertActionPayload:
    """Parse alert action callback payload.

    Supported raw formats after prefix removal:
    - alert_id
    - alert_id:filter:page
    - alert_id:filter:page:selected_alert_id
    """
    parts = payload.split(":")

    alert_id = _parse_positive_int(_get_part(parts, 0))

    if alert_id is None:
        return AlertActionPayload(
            alert_id=None,
            filter_value=ALERT_FILTER_ALL,
            page_number=0,
            selected_alert_id=None,
        )

    if len(parts) < 3:
        return AlertActionPayload(
            alert_id=alert_id,
            filter_value=ALERT_FILTER_ALL,
            page_number=0,
            selected_alert_id=None,
        )

    selected_alert_id = _parse_positive_int(_get_part(parts, 3))

    return AlertActionPayload(
        alert_id=alert_id,
        filter_value=normalize_alert_filter(parts[1]),
        page_number=_parse_non_negative_int(parts[2]),
        selected_alert_id=selected_alert_id,
    )


def _get_part(parts: list[str], index: int) -> str | None:
    """Return a payload part by index without raising IndexError."""
    try:
        return parts[index]
    except IndexError:
        return None


def _parse_non_negative_int(value: str | None) -> int:
    """Parse a non-negative integer with a safe zero fallback."""
    if value is None:
        return 0

    try:
        parsed_value = int(value)
    except ValueError:
        return 0

    return max(parsed_value, 0)


def _parse_positive_int(value: str | None) -> int | None:
    """Parse a positive integer or return None."""
    if value is None:
        return None

    try:
        parsed_value = int(value)
    except ValueError:
        return None

    if parsed_value <= 0:
        return None

    return parsed_value
