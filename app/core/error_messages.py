"""Centralized validation, domain, and integration error messages.

These messages are intentionally separated from validators, services, and API
clients so user-facing and loggable text is easy to find and update.
"""

PRICE_EMPTY_ERROR = "Price cannot be empty."
PRICE_INVALID_NUMBER_ERROR = "Price must be a valid number."
PRICE_TOO_LOW_ERROR_TEMPLATE = "Price must be at least {min_price}."
PRICE_TOO_HIGH_ERROR_TEMPLATE = "Price must be lower than {max_price}."

PRICE_NOT_FOUND_ERROR_TEMPLATE = "Price was not found for coin id: {coin_id}."

PRICE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE = (
    "PRICE_CHECK_INTERVAL_SECONDS must be at least {min_seconds} seconds."
)

WHALE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE = (
    "WHALE_CHECK_INTERVAL_SECONDS must be at least {min_seconds} seconds."
)

UNSUPPORTED_WHALE_PROVIDER_ERROR_TEMPLATE = (
    "Unsupported whale provider. Supported providers: {supported_providers}."
)

MINIAPP_URL_INVALID_ERROR = "MINIAPP_URL must start with http:// or https://."

UNSUPPORTED_COIN_SYMBOL_ERROR_TEMPLATE = (
    "Unsupported coin symbol. Supported symbols: {supported_symbols}."
)

UNSUPPORTED_COIN_ID_ERROR_TEMPLATE = (
    "Unsupported coin id. Supported ids: {supported_coin_ids}."
)

UNSUPPORTED_CHAIN_ERROR_TEMPLATE = (
    "Unsupported chain. Supported chains: {supported_chains}."
)

INVALID_EVM_ADDRESS_ERROR = "Contract address must be a valid EVM address."

TELEGRAM_INIT_DATA_MISSING_ERROR = "Telegram Mini App init data is missing."
TELEGRAM_INIT_DATA_HASH_MISSING_ERROR = "Telegram Mini App init data hash is missing."
TELEGRAM_INIT_DATA_INVALID_ERROR = "Telegram Mini App init data is invalid."
TELEGRAM_INIT_DATA_EXPIRED_ERROR = "Telegram Mini App init data has expired."
TELEGRAM_INIT_DATA_USER_MISSING_ERROR = "Telegram Mini App user data is missing."
TELEGRAM_INIT_DATA_USER_INVALID_ERROR = "Telegram Mini App user data is invalid."

COINGECKO_REQUEST_FAILED_ERROR = "CoinGecko request failed."
COINGECKO_INVALID_RESPONSE_ERROR = "CoinGecko returned an invalid response."

GOPLUS_REQUEST_FAILED_ERROR = "GoPlus request failed."
GOPLUS_INVALID_RESPONSE_ERROR = "GoPlus returned an invalid response."
GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR = "GoPlus token data was not found."

WHALE_MIN_USD_VALUE_TOO_LOW_ERROR_TEMPLATE = (
    "Minimum whale alert value must be at least {min_value} USD."
)
WHALE_MIN_USD_VALUE_TOO_HIGH_ERROR_TEMPLATE = (
    "Minimum whale alert value must be lower than {max_value} USD."
)
WHALE_NETWORK_EMPTY_ERROR = "Whale event network cannot be empty."
WHALE_TRANSACTION_HASH_EMPTY_ERROR = "Whale transaction hash cannot be empty."
WHALE_AMOUNT_TOO_LOW_ERROR = "Whale event amount must be greater than zero."
WHALE_AMOUNT_USD_TOO_LOW_ERROR = "Whale event USD value must be greater than zero."
