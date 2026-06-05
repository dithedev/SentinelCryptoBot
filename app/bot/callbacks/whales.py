"""Callback payload helpers for whale alert screens."""

from dataclasses import dataclass

from app.bot.constants import CB_WHALES_EVENTS_PAGE_PREFIX


@dataclass(frozen=True)
class WhaleEventsPagePayload:
    """Parsed payload for opening a paginated whale events list."""

    page_number: int


def build_whale_events_page_callback(*, page_number: int) -> str:
    """Build callback data for opening a whale events page."""
    safe_page_number = max(page_number, 0)
    return f"{CB_WHALES_EVENTS_PAGE_PREFIX}{safe_page_number}"


def parse_whale_events_page_payload(payload: str) -> WhaleEventsPagePayload:
    """Parse whale events page callback payload."""
    try:
        page_number = int(payload)
    except ValueError:
        page_number = 0

    return WhaleEventsPagePayload(
        page_number=max(page_number, 0),
    )
