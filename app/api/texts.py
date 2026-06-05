"""API response and error text constants.

API routes import text from here instead of keeping response messages inside
handlers. This keeps route code focused on request handling.
"""

API_TITLE = "Sentinel Crypto API"
API_DESCRIPTION = (
    "HTTP API for Sentinel Crypto Telegram bot and Mini App. "
    "It exposes health checks, supported market prices, Mini App alerts, "
    "and token risk checks."
)
API_VERSION = "0.1.0"

HEALTH_STATUS_OK = "ok"
HEALTH_STATUS_READY = "ready"
HEALTH_STATUS_NOT_READY = "not_ready"

HEALTH_COMPONENT_OK = "ok"
HEALTH_COMPONENT_UNAVAILABLE = "unavailable"

ALERT_DISABLED_MESSAGE = "Alert disabled."
USER_NOT_FOUND_MESSAGE = "User was not found."
ALERT_NOT_FOUND_MESSAGE = "Alert was not found."
VALIDATION_ERROR_MESSAGE = "Invalid input."
PRICE_PROVIDER_ERROR_MESSAGE = "Price provider error."
RISK_CHECK_PROVIDER_ERROR_MESSAGE = "Token risk provider error."

AUTHORIZATION_HEADER_NAME = "X-Telegram-Init-Data"
AUTHENTICATION_FAILED_MESSAGE = "Telegram Mini App authentication failed."
