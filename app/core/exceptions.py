class AppError(Exception):
    """Base application exception.

    Domain and integration exceptions inherit from this class so handlers can
    catch expected application errors separately from unexpected bugs.
    """


class ValidationError(AppError):
    """Raised when user input cannot be accepted."""


class AuthenticationError(AppError):
    """Raised when request authentication data is missing or invalid."""


class NotFoundError(AppError):
    """Raised when requested data does not exist."""


class ExternalAPIError(AppError):
    """Raised when an external API request fails."""


class PriceProviderError(ExternalAPIError):
    """Raised when the price provider cannot return market data."""


class SecurityProviderError(ExternalAPIError):
    """Raised when the token security provider cannot return risk data."""


class AlertError(AppError):
    """Base error for price alert operations."""


class AlertNotFoundError(AlertError, NotFoundError):
    """Raised when a price alert cannot be found."""


class AlertAlreadyInactiveError(AlertError):
    """Raised when a disabled or triggered alert is modified as active."""


class UserNotFoundError(NotFoundError):
    """Raised when a Telegram user is not registered in the database."""


class TelegramDeliveryBlockedError(AppError):
    """Raised when Telegram rejects messages for a user."""

    def __init__(self, *, telegram_id: int) -> None:
        self.telegram_id = telegram_id
        super().__init__(f"Telegram delivery blocked for user {telegram_id}")
