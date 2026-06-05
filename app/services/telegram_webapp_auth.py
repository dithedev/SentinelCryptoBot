"""Telegram Mini App initData validation.

Telegram Mini Apps send signed initData to the frontend. The frontend must pass
that exact string to the backend. The backend validates the signature using the
bot token and then trusts the Telegram user id from the signed payload.

This prevents users from manually sending another telegram_id to access or
modify somebody else's alerts.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from time import time
from typing import Any
from urllib.parse import parse_qsl

from app.core.constants import TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS
from app.core.error_messages import (
    TELEGRAM_INIT_DATA_EXPIRED_ERROR,
    TELEGRAM_INIT_DATA_HASH_MISSING_ERROR,
    TELEGRAM_INIT_DATA_INVALID_ERROR,
    TELEGRAM_INIT_DATA_MISSING_ERROR,
    TELEGRAM_INIT_DATA_USER_INVALID_ERROR,
    TELEGRAM_INIT_DATA_USER_MISSING_ERROR,
)
from app.core.exceptions import AuthenticationError


@dataclass(frozen=True)
class TelegramWebAppUser:
    """Telegram user extracted from validated WebApp initData."""

    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None


def validate_telegram_webapp_init_data(
    *,
    init_data: str,
    bot_token: str,
    max_age_seconds: int = TELEGRAM_WEBAPP_AUTH_MAX_AGE_SECONDS,
) -> TelegramWebAppUser:
    """Validate Telegram WebApp initData and return the signed user.

    Validation steps:
    1. Parse the URL-encoded initData string.
    2. Rebuild Telegram's data_check_string from all fields except hash.
    3. Verify HMAC-SHA256 signature using the bot token.
    4. Reject expired initData using auth_date.
    5. Parse and validate the signed user object.
    """
    if not init_data.strip():
        raise AuthenticationError(TELEGRAM_INIT_DATA_MISSING_ERROR)

    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        raise AuthenticationError(TELEGRAM_INIT_DATA_HASH_MISSING_ERROR)

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise AuthenticationError(TELEGRAM_INIT_DATA_INVALID_ERROR)

    _validate_auth_date(
        raw_auth_date=parsed_data.get("auth_date"),
        max_age_seconds=max_age_seconds,
    )

    return _parse_user(parsed_data.get("user"))


def _validate_auth_date(
    *,
    raw_auth_date: str | None,
    max_age_seconds: int,
) -> None:
    """Validate auth_date from Telegram signed payload."""
    if raw_auth_date is None:
        raise AuthenticationError(TELEGRAM_INIT_DATA_INVALID_ERROR)

    try:
        auth_date = int(raw_auth_date)
    except ValueError as exc:
        raise AuthenticationError(TELEGRAM_INIT_DATA_INVALID_ERROR) from exc

    if auth_date > int(time()):
        raise AuthenticationError(TELEGRAM_INIT_DATA_INVALID_ERROR)

    if int(time()) - auth_date > max_age_seconds:
        raise AuthenticationError(TELEGRAM_INIT_DATA_EXPIRED_ERROR)


def _parse_user(raw_user: str | None) -> TelegramWebAppUser:
    """Parse Telegram user JSON from validated initData."""
    if raw_user is None:
        raise AuthenticationError(TELEGRAM_INIT_DATA_USER_MISSING_ERROR)

    try:
        user_data: Any = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise AuthenticationError(TELEGRAM_INIT_DATA_USER_INVALID_ERROR) from exc

    if not isinstance(user_data, dict):
        raise AuthenticationError(TELEGRAM_INIT_DATA_USER_INVALID_ERROR)

    telegram_id = user_data.get("id")

    if not isinstance(telegram_id, int):
        raise AuthenticationError(TELEGRAM_INIT_DATA_USER_INVALID_ERROR)

    return TelegramWebAppUser(
        telegram_id=telegram_id,
        username=_optional_str(user_data.get("username")),
        first_name=_optional_str(user_data.get("first_name")),
        last_name=_optional_str(user_data.get("last_name")),
        language_code=_optional_str(user_data.get("language_code")),
    )


def _optional_str(value: Any) -> str | None:
    """Return a clean optional string from Telegram user fields."""
    if value is None:
        return None

    if not isinstance(value, str):
        return None

    cleaned_value = value.strip()
    return cleaned_value or None
