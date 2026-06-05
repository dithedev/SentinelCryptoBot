"""Text constants and templates for price alert messages."""

ALERTS_MENU_TEXT = (
    "📋 <b>Alerts</b>\n\n"
    "Here you can create a new price alert or open your existing alerts.\n\n"
    "🔘 <b>Create alert</b> starts a new alert setup.\n"
    "🔘 <b>My alerts</b> opens the list with pagination, filters, and alert details."
)

NO_ACTIVE_ALERTS_TEXT = (
    "📭 <b>No active alerts yet</b>\n\nYou do not have active alerts yet."
)

NO_FILTERED_ALERTS_TEXT = (
    "📭 <b>No alerts found</b>\n\nThere are no alerts for this filter yet."
)

CHOOSE_ALERT_COIN_TEXT = (
    "🪙 <b>Choose a coin</b>\n\nSelect the cryptocurrency you want to track."
)

CHOOSE_ALERT_CONDITION_TEXT = (
    "📊 <b>Choose a condition</b>\n\n"
    "Should the alert trigger when the price goes above or below your target?"
)

ENTER_ALERT_PRICE_TEXT = (
    "💵 <b>Enter target price</b>\n\n"
    "Send the price in USD. Example: <code>100000</code>"
)

ALERT_CREATION_LOADING_TEXT = (
    "⏳ <b>Creating alert</b>\n\nI am saving your price alert. This can take a moment."
)

ALERT_CREATION_CANCELLED_TEXT = "Alert creation cancelled."
ALERT_DISABLED_TEXT = "❌ Alert disabled."
ALERT_DELETED_TEXT = ALERT_DISABLED_TEXT
ALERT_NOT_FOUND_TEXT = "The alert was not found. It may have already been changed."

ALERT_TITLE_TEMPLATE = "{symbol} {condition} ${price}"
ALERT_BUTTON_TITLE_TEMPLATE = "{status_prefix}{symbol} {condition} ${price}"

ALERTS_PAGE_TITLE_TEMPLATE = "📋 <b>My alerts</b>"
ALERTS_PAGE_DESCRIPTION = (
    "🔘 Use the filters above to switch between active alerts and alert history.\n"
    "🔘 Tap any alert to view details. Active alerts can be disabled from the list."
)
ALERTS_PAGE_EMPTY_TEMPLATE = "📭 No alerts found for the selected filter."
ALERTS_PAGE_TEXT_TEMPLATE = "{title}\n\n{description}\n\n{empty_line}"

ALERT_DETAILS_TEMPLATE = (
    "📈 <b>{title}</b>\n\n"
    "<b>Status:</b> {status}\n"
    "<b>Created at:</b> {created_at}"
    "{triggered_line}"
)

ALERT_CREATED_TEMPLATE = (
    "✅ <b>Alert created</b>\n\n{title}\n\nI will notify you when the condition is met."
)

ALERT_TRIGGERED_TEMPLATE = (
    "🚨 <b>Price alert triggered</b>\n\n"
    "{symbol} is now <b>{condition}</b> your target price.\n\n"
    "<b>Target:</b> ${target_price}\n"
    "<b>Current:</b> ${current_price}\n\n"
    "You can delete this notification with the button below to keep the chat "
    "clean.\n\n"
    "<b>Find it later:</b> Main menu > Alerts > My alerts > History."
)

ALERT_FILTER_ACTIVE_TITLE = "Active alerts"
ALERT_FILTER_HISTORY_TITLE = "Alert history"
ALERT_FILTER_ALL_TITLE = ALERT_FILTER_HISTORY_TITLE

ALERT_FILTER_TRIGGERED_TITLE = "Triggered alerts"

ALERT_TRIGGERED_LINE_TEMPLATE = "\n<b>Triggered at:</b> {triggered_at}"
ALERT_NOT_TRIGGERED_LABEL = "Not triggered yet"
