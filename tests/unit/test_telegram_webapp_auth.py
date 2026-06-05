"""Unit tests for Telegram Mini App initData validation."""

import hashlib
import hmac
import json
from time import time
from urllib.parse import urlencode

import pytest
from app.core.error_messages import (
    TELEGRAM_INIT_DATA_EXPIRED_ERROR,
    TELEGRAM_INIT_DATA_HASH_MISSING_ERROR,
    TELEGRAM_INIT_DATA_INVALID_ERROR,
    TELEGRAM_INIT_DATA_MISSING_ERROR,
    TELEGRAM_INIT_DATA_USER_INVALID_ERROR,
    TELEGRAM_INIT_DATA_USER_MISSING_ERROR,
)
from app.core.exceptions import AuthenticationError
from app.services.telegram_webapp_auth import validate_telegram_webapp_init_data

BOT_TOKEN = "123456:test-bot-token"

_MISSING = object()


def _build_init_data(
    *,
    bot_token: str = BOT_TOKEN,
    auth_date: int | None = None,
    user_payload: dict[str, object] | str | None | object = _MISSING,
    include_hash: bool = True,
    hash_override: str | None = None,
) -> str:
    """Build signed Telegram WebApp initData for deterministic tests.

    The helper uses a sentinel object to distinguish two cases:

    1. user_payload was not passed.
       In this case a default valid Telegram user is added.

    2. user_payload=None was passed explicitly.
       In this case the user field is intentionally omitted from initData.
    """
    if auth_date is None:
        auth_date = int(time())

    if user_payload is _MISSING:
        user_payload = {
            "id": 123456789,
            "username": "sentinel_user",
            "first_name": "Sentinel",
            "last_name": "User",
            "language_code": "en",
        }

    data: dict[str, str] = {
        "auth_date": str(auth_date),
    }

    if user_payload is not None:
        if isinstance(user_payload, str):
            data["user"] = user_payload
        else:
            data["user"] = json.dumps(
                user_payload,
                separators=(",", ":"),
            )

    if include_hash:
        data["hash"] = hash_override or _calculate_hash(
            data=data,
            bot_token=bot_token,
        )

    return urlencode(data)


def _calculate_hash(
    *,
    data: dict[str, str],
    bot_token: str,
) -> str:
    """Calculate Telegram WebApp HMAC hash for test initData."""
    data_without_hash = {key: value for key, value in data.items() if key != "hash"}
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data_without_hash.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    return hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def test_validate_telegram_webapp_init_data_accepts_valid_payload() -> None:
    init_data = _build_init_data()

    user = validate_telegram_webapp_init_data(
        init_data=init_data,
        bot_token=BOT_TOKEN,
    )

    assert user.telegram_id == 123456789
    assert user.username == "sentinel_user"
    assert user.first_name == "Sentinel"
    assert user.last_name == "User"
    assert user.language_code == "en"


def test_validate_telegram_webapp_init_data_accepts_optional_user_fields() -> None:
    init_data = _build_init_data(
        user_payload={
            "id": 123456789,
            "username": "",
            "first_name": "Sentinel",
            "last_name": None,
        },
    )

    user = validate_telegram_webapp_init_data(
        init_data=init_data,
        bot_token=BOT_TOKEN,
    )

    assert user.telegram_id == 123456789
    assert user.username is None
    assert user.first_name == "Sentinel"
    assert user.last_name is None
    assert user.language_code is None


def test_validate_telegram_webapp_init_data_rejects_empty_payload() -> None:
    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data="   ",
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_MISSING_ERROR


def test_validate_telegram_webapp_init_data_rejects_missing_hash() -> None:
    init_data = _build_init_data(include_hash=False)

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_HASH_MISSING_ERROR


def test_validate_telegram_webapp_init_data_rejects_invalid_hash() -> None:
    init_data = _build_init_data(hash_override="invalid-hash")

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_INVALID_ERROR


def test_validate_telegram_webapp_init_data_rejects_future_auth_date() -> None:
    init_data = _build_init_data(auth_date=int(time()) + 60)

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_INVALID_ERROR


def test_validate_telegram_webapp_init_data_rejects_expired_auth_date() -> None:
    init_data = _build_init_data(auth_date=int(time()) - 3600)

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
            max_age_seconds=60,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_EXPIRED_ERROR


def test_validate_telegram_webapp_init_data_rejects_missing_user() -> None:
    init_data = _build_init_data(user_payload=None)

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_USER_MISSING_ERROR


def test_validate_telegram_webapp_init_data_rejects_invalid_user_json() -> None:
    init_data = _build_init_data(user_payload="{not-json}")

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_USER_INVALID_ERROR


def test_validate_telegram_webapp_init_data_rejects_invalid_user_shape() -> None:
    init_data = _build_init_data(user_payload='["not", "object"]')

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_USER_INVALID_ERROR


def test_validate_telegram_webapp_init_data_rejects_missing_user_id() -> None:
    init_data = _build_init_data(
        user_payload={
            "username": "sentinel_user",
        },
    )

    with pytest.raises(AuthenticationError) as exc_info:
        validate_telegram_webapp_init_data(
            init_data=init_data,
            bot_token=BOT_TOKEN,
        )

    assert str(exc_info.value) == TELEGRAM_INIT_DATA_USER_INVALID_ERROR
