from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    DEFAULT_APP_NAME,
    DEFAULT_BOT_USER_MIN_INTERVAL_SECONDS,
    DEFAULT_COINGECKO_BASE_URL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_GOPLUS_BASE_URL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MINIAPP_API_REQUESTS_PER_MINUTE,
    DEFAULT_PRICE_CHECK_INTERVAL_SECONDS,
    DEFAULT_TELEGRAM_SEND_RATE_PER_SECOND,
    DEFAULT_WHALE_CHECK_INTERVAL_SECONDS,
    DEFAULT_WHALE_PROVIDER,
    DEFAULT_WHALE_SIMULATED_EVENTS_PER_CYCLE,
    MIN_PRICE_CHECK_INTERVAL_SECONDS,
    MIN_WHALE_CHECK_INTERVAL_SECONDS,
)
from app.core.error_messages import (
    MINIAPP_URL_INVALID_ERROR,
    PRICE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE,
    WHALE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    The project uses one shared settings object for the bot, API, worker,
    database, and external integrations.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")

    # Database
    database_url: str = Field(alias="DATABASE_URL")

    # External APIs
    coingecko_base_url: str = Field(
        default=DEFAULT_COINGECKO_BASE_URL,
        alias="COINGECKO_BASE_URL",
    )
    goplus_base_url: str = Field(
        default=DEFAULT_GOPLUS_BASE_URL,
        alias="GOPLUS_BASE_URL",
    )

    # Application
    app_name: str = Field(default=DEFAULT_APP_NAME, alias="APP_NAME")
    environment: str = Field(default=DEFAULT_ENVIRONMENT, alias="ENVIRONMENT")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")

    # Worker
    price_check_interval_seconds: int = Field(
        default=DEFAULT_PRICE_CHECK_INTERVAL_SECONDS,
        alias="PRICE_CHECK_INTERVAL_SECONDS",
    )
    whale_check_interval_seconds: int = Field(
        default=DEFAULT_WHALE_CHECK_INTERVAL_SECONDS,
        alias="WHALE_CHECK_INTERVAL_SECONDS",
    )
    whale_provider: str = Field(
        default=DEFAULT_WHALE_PROVIDER,
        alias="WHALE_PROVIDER",
    )
    whale_simulated_events_per_cycle: int = Field(
        default=DEFAULT_WHALE_SIMULATED_EVENTS_PER_CYCLE,
        alias="WHALE_SIMULATED_EVENTS_PER_CYCLE",
        ge=0,
    )
    telegram_send_rate_per_second: float = Field(
        default=DEFAULT_TELEGRAM_SEND_RATE_PER_SECOND,
        alias="TELEGRAM_SEND_RATE_PER_SECOND",
        gt=0,
    )

    # Throttling
    bot_user_min_interval_seconds: float = Field(
        default=DEFAULT_BOT_USER_MIN_INTERVAL_SECONDS,
        alias="BOT_USER_MIN_INTERVAL_SECONDS",
        gt=0,
    )
    miniapp_api_requests_per_minute: int = Field(
        default=DEFAULT_MINIAPP_API_REQUESTS_PER_MINUTE,
        alias="MINIAPP_API_REQUESTS_PER_MINUTE",
        ge=1,
    )

    # Mini App
    miniapp_url: str | None = Field(default=None, alias="MINIAPP_URL")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log level to uppercase for logging configuration."""
        return value.strip().upper()

    @field_validator("coingecko_base_url", "goplus_base_url")
    @classmethod
    def validate_external_api_base_url(cls, value: str) -> str:
        """Validate and normalize external API base URLs.

        Empty values are rejected because an empty environment variable would
        otherwise override the safe default value from constants.
        """
        normalized_value = value.strip().rstrip("/")

        if not normalized_value:
            raise ValueError("External API base URL cannot be empty.")

        if not normalized_value.startswith(("http://", "https://")):
            raise ValueError(
                "External API base URL must start with http:// or https://."
            )

        return normalized_value

    @field_validator("price_check_interval_seconds")
    @classmethod
    def validate_price_check_interval(cls, value: int) -> int:
        """Prevent too aggressive polling of external APIs."""
        if value < MIN_PRICE_CHECK_INTERVAL_SECONDS:
            message = PRICE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE.format(
                min_seconds=MIN_PRICE_CHECK_INTERVAL_SECONDS,
            )
            raise ValueError(message)

        return value

    @field_validator("whale_check_interval_seconds")
    @classmethod
    def validate_whale_check_interval(cls, value: int) -> int:
        """Prevent too aggressive whale worker polling."""
        if value < MIN_WHALE_CHECK_INTERVAL_SECONDS:
            message = WHALE_CHECK_INTERVAL_TOO_LOW_ERROR_TEMPLATE.format(
                min_seconds=MIN_WHALE_CHECK_INTERVAL_SECONDS,
            )
            raise ValueError(message)

        return value

    @field_validator("whale_provider")
    @classmethod
    def validate_whale_provider(cls, value: str) -> str:
        """Normalize whale provider name."""
        return value.strip().lower()

    @field_validator("miniapp_url")
    @classmethod
    def validate_miniapp_url(cls, value: str | None) -> str | None:
        """Normalize optional Telegram Mini App URL.

        The bot shows the Mini App button only when this value is configured.
        Telegram requires Web App URLs to be HTTPS in production. HTTP is kept
        accepted here for local development tunnels or local reverse proxies.
        """
        if value is None:
            return None

        normalized_value = value.strip().rstrip("/")

        if not normalized_value:
            return None

        if not normalized_value.startswith(("http://", "https://")):
            raise ValueError(MINIAPP_URL_INVALID_ERROR)

        return normalized_value


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Caching prevents repeated .env parsing and keeps configuration consistent
    across the application lifetime.
    """
    return Settings()  # type: ignore[call-arg]
