from dataclasses import dataclass
from decimal import Decimal

DEFAULT_APP_NAME = "Sentinel Crypto"
DEFAULT_ENVIRONMENT = "local"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
DEFAULT_GOPLUS_BASE_URL = "https://api.gopluslabs.io/api/v1"

DEFAULT_PRICE_CHECK_INTERVAL_SECONDS = 60
MIN_PRICE_CHECK_INTERVAL_SECONDS = 10

DEFAULT_WHALE_CHECK_INTERVAL_SECONDS = 120
MIN_WHALE_CHECK_INTERVAL_SECONDS = 30
DEFAULT_WHALE_PROVIDER = "simulated"
DEFAULT_WHALE_SIMULATED_EVENTS_PER_CYCLE = 1
BOT_WHALE_EVENTS_PAGE_SIZE = 5

MARKET_PRICES_API_CACHE_TTL_SECONDS = 15

TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS = 60 * 60 * 24

DEFAULT_ALERT_HISTORY_LIMIT = 20
MAX_ALERT_HISTORY_LIMIT = 50

BOT_ALERTS_PAGE_SIZE = 10
MAX_BOT_ALERTS_VISIBLE_PAGES = 20

DEFAULT_WHALE_EVENTS_LIMIT = 20
MAX_WHALE_EVENTS_LIMIT = 50
MAX_BOT_WHALE_EVENTS_VISIBLE_PAGES = 20

DEFAULT_WHALE_MIN_USD_VALUE = Decimal("1000000")
MIN_WHALE_MIN_USD_VALUE = Decimal("1000")
MAX_WHALE_MIN_USD_VALUE = Decimal("100000000000")

MAX_WHALE_NOTIFICATION_ATTEMPTS = 5

DEFAULT_TELEGRAM_SEND_RATE_PER_SECOND = 20.0
DEFAULT_BOT_USER_MIN_INTERVAL_SECONDS = 1.0
DEFAULT_MINIAPP_API_REQUESTS_PER_MINUTE = 60


@dataclass(frozen=True)
class SupportedCoin:
    """Coin available for price tracking and alert creation."""

    coin_id: str
    symbol: str
    name: str


SUPPORTED_COINS: tuple[SupportedCoin, ...] = (
    SupportedCoin(
        coin_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
    ),
    SupportedCoin(
        coin_id="ethereum",
        symbol="ETH",
        name="Ethereum",
    ),
    SupportedCoin(
        coin_id="the-open-network",
        symbol="TON",
        name="Toncoin",
    ),
    SupportedCoin(
        coin_id="solana",
        symbol="SOL",
        name="Solana",
    ),
    SupportedCoin(
        coin_id="binancecoin",
        symbol="BNB",
        name="BNB",
    ),
)

SUPPORTED_COINS_BY_ID: dict[str, SupportedCoin] = {
    coin.coin_id: coin for coin in SUPPORTED_COINS
}

SUPPORTED_COINS_BY_SYMBOL: dict[str, SupportedCoin] = {
    coin.symbol: coin for coin in SUPPORTED_COINS
}

SUPPORTED_COIN_IDS: set[str] = set(SUPPORTED_COINS_BY_ID)
SUPPORTED_COIN_SYMBOLS: set[str] = set(SUPPORTED_COINS_BY_SYMBOL)

MIN_ALERT_PRICE = Decimal("0.00000001")
MAX_ALERT_PRICE = Decimal("1000000000")

SUPPORTED_CHAINS: set[str] = {
    "eth",
    "bsc",
    "polygon",
    "arbitrum",
    "optimism",
    "base",
}
