"""Unit tests for whale callback payload helpers."""

from app.bot.callbacks.whales import (
    build_whale_events_page_callback,
    parse_whale_events_page_payload,
)


def test_build_and_parse_whale_events_page_callback() -> None:
    """Whale events page callbacks should round-trip safely."""
    callback_data = build_whale_events_page_callback(page_number=2)

    payload = parse_whale_events_page_payload(
        callback_data.removeprefix("whales:events_page:"),
    )

    assert payload.page_number == 2


def test_parse_whale_events_page_callback_falls_back_to_zero() -> None:
    """Invalid page payloads should fall back to page zero."""
    payload = parse_whale_events_page_payload("invalid")

    assert payload.page_number == 0
