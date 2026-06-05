"""Text constants and templates for bot market price messages."""

PRICES_TITLE = "📈 <b>Market prices</b>"

PRICES_DESCRIPTION = "Current USD prices for supported coins."

PRICES_LOADING_TEXT = (
    "📈 <b>Market prices</b>\n\n"
    "⏳ Loading latest prices...\n\n"
    "<b>BTC</b> - ...\n"
    "<b>ETH</b> - ...\n"
    "<b>TON</b> - ...\n"
    "<b>SOL</b> - ...\n"
    "<b>BNB</b> - ..."
)

PRICES_EMPTY_TEXT = (
    "📭 <b>No prices available</b>\n\n"
    "I could not find prices for supported coins right now."
)

PRICES_FAILED_TEXT = "⚠️ <b>Could not load prices</b>\n\nPlease try again later."

PRICES_REFRESH_COOLDOWN_TEXT_TEMPLATE = "Prices can be refreshed again in {seconds}s."

PRICE_ROW_TEMPLATE = "<b>{symbol}</b> - ${price}"
PRICES_TEXT_TEMPLATE = "{title}\n\n{description}\n\n{rows}"
