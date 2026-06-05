"""Text constants and templates for whale alert messages."""

WHALE_EVENT_TYPE_LABELS: dict[str, str] = {
    "transfer": "Large transfer",
    "exchange_inflow": "Exchange inflow",
    "exchange_outflow": "Exchange outflow",
    "unknown": "Unknown movement",
}

WHALE_ALERT_NOTIFICATION_TEMPLATE = (
    "🐋 <b>Whale movement detected</b>\n\n"
    "<b>{event_type}</b>\n"
    "<b>Asset:</b> {symbol}\n"
    "<b>Network:</b> {network}\n"
    "<b>Amount:</b> {amount} {symbol}\n"
    "<b>Value:</b> ${amount_usd}\n\n"
    "Transaction: <code>{transaction_hash}</code>\n\n"
    "This is an automated market movement alert.\n\n"
    "You can delete this notification with the button below to keep the chat "
    "clean.\n\n"
    "<b>Find it later:</b> Main menu > Whales > Recent events."
)

WHALE_SIMULATED_PROVIDER_WARNING = (
    "⚠️ This MVP uses a <b>simulated whale provider</b>. Events are demo market "
    "movements, not live on-chain tracking."
)

WHALES_MENU_TEXT = (
    "🐋 <b>Whale alerts</b>\n\n"
    "<b>Status:</b> {status}\n"
    "<b>Minimum value:</b> ${min_usd_value}\n\n"
    "<b>Tracked assets:</b> {tracked_assets}\n"
    "<b>Event types:</b> {event_types}\n\n"
    f"{WHALE_SIMULATED_PROVIDER_WARNING}"
)

WHALES_STATUS_ENABLED = "Enabled"
WHALES_STATUS_DISABLED = "Disabled"

WHALES_ENTER_THRESHOLD_TEXT = (
    "💵 <b>Change minimum USD value</b>\n\n"
    "Send the minimum event value in USD.\n"
    "Example: <code>1000000</code>"
)

WHALES_THRESHOLD_LOADING_TEXT = (
    "⏳ <b>Updating whale threshold</b>\n\n"
    "I am saving the new minimum event value. This can take a moment."
)

WHALES_THRESHOLD_UPDATED_TEXT = "Whale alert threshold updated."
WHALES_ALERTS_ENABLED_TEXT = "Whale alerts enabled."
WHALES_ALERTS_DISABLED_TEXT = "Whale alerts disabled."
WHALES_SETTINGS_CANCELLED_TEXT = "Whale alert settings update cancelled."

WHALES_EVENTS_TITLE = "🐋 <b>Latest whale events</b>"
WHALES_EVENTS_DESCRIPTION = "Newest stored whale movements from the demo provider."
WHALES_EVENTS_EMPTY_TEXT = "No whale events have been detected yet."
WHALES_EVENTS_PAGE_TEXT_TEMPLATE = "{title}\n\n{description}\n\n{events_block}"

WHALE_EVENT_CARD_TEMPLATE = (
    "<b>{event_type}</b> - {symbol}\n"
    "Value: <b>${amount_usd}</b> | Network: <b>{network}</b>\n"
    "Detected: {detected_at}\n"
)
