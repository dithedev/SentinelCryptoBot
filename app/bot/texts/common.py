"""Common bot texts used by multiple routers."""

START_TEXT = (
    "🛰 <b>Welcome to Sentinel Crypto</b>\n\n"
    "This bot helps you track crypto prices, create alerts, and check token "
    "contracts for risk signals.\n\n"
    "Use the menu below to get started."
)

GENERIC_ERROR_TEXT = (
    "⚠️ Something went wrong.\n\nPlease try again later or return to the main menu."
)

VALIDATION_ERROR_TEMPLATE = "⚠️ <b>Invalid input</b>\n\n{message}"

FSM_LOCKED_CALLBACK_TEXT = (
    "Finish the current step or tap Cancel before using other buttons."
)

BOT_TOO_MANY_REQUESTS_TEXT = "Too many requests. Please wait a moment."
