"""Message builders for whale alert notifications and bot screens."""

from app.bot.texts.whales import (
    WHALE_ALERT_NOTIFICATION_TEMPLATE,
    WHALE_EVENT_CARD_TEMPLATE,
    WHALE_EVENT_TYPE_LABELS,
    WHALES_EVENTS_DESCRIPTION,
    WHALES_EVENTS_EMPTY_TEXT,
    WHALES_EVENTS_PAGE_TEXT_TEMPLATE,
    WHALES_EVENTS_TITLE,
    WHALES_MENU_TEXT,
    WHALES_STATUS_DISABLED,
    WHALES_STATUS_ENABLED,
)
from app.core.constants import SUPPORTED_COINS
from app.database.models.whale import WhaleAlertSettings, WhaleEvent
from app.utils.money import format_price


def build_whale_alert_notification_text(event: WhaleEvent) -> str:
    """Build a readable whale movement notification."""
    return WHALE_ALERT_NOTIFICATION_TEMPLATE.format(
        event_type=_get_event_type_label(event),
        symbol=event.symbol,
        network=event.network.upper(),
        amount=format_price(event.amount),
        amount_usd=format_price(event.amount_usd),
        transaction_hash=event.transaction_hash,
    )


def build_whales_menu_text(settings: WhaleAlertSettings) -> str:
    """Build whale alerts settings menu text."""
    status = WHALES_STATUS_ENABLED if settings.is_enabled else WHALES_STATUS_DISABLED

    return WHALES_MENU_TEXT.format(
        status=status,
        min_usd_value=format_price(settings.min_usd_value),
        tracked_assets=_format_tracked_assets(),
        event_types=_format_whale_event_types(),
    )


def build_whale_events_page_text(events: list[WhaleEvent]) -> str:
    """Build paginated whale events screen text."""
    if not events:
        return WHALES_EVENTS_PAGE_TEXT_TEMPLATE.format(
            title=WHALES_EVENTS_TITLE,
            description=WHALES_EVENTS_DESCRIPTION,
            events_block=WHALES_EVENTS_EMPTY_TEXT,
        ).rstrip()

    events_block = "\n".join(build_whale_event_card_text(event) for event in events)

    return WHALES_EVENTS_PAGE_TEXT_TEMPLATE.format(
        title=WHALES_EVENTS_TITLE,
        description=WHALES_EVENTS_DESCRIPTION,
        events_block=events_block,
    ).rstrip()


def build_whale_event_card_text(event: WhaleEvent) -> str:
    """Build one compact whale event card for bot screens."""
    return WHALE_EVENT_CARD_TEMPLATE.format(
        event_type=_get_event_type_label(event),
        symbol=event.symbol,
        amount_usd=format_price(event.amount_usd),
        network=event.network.upper(),
        detected_at=event.detected_at.strftime("%Y-%m-%d %H:%M UTC"),
    )


def _get_event_type_label(event: WhaleEvent) -> str:
    """Return a user-facing label for a whale event type."""
    return WHALE_EVENT_TYPE_LABELS.get(
        event.event_type.value,
        WHALE_EVENT_TYPE_LABELS["unknown"],
    )


def _format_tracked_assets() -> str:
    """Return supported whale-tracked asset symbols."""
    return ", ".join(coin.symbol for coin in SUPPORTED_COINS)


def _format_whale_event_types() -> str:
    """Return supported whale event type labels."""
    return ", ".join(
        WHALE_EVENT_TYPE_LABELS[event_type]
        for event_type in WHALE_EVENT_TYPE_LABELS
        if event_type != "unknown"
    )
