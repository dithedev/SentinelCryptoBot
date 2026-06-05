"""Unit tests for bot user throttling middleware."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from aiogram.types import CallbackQuery, Update
from app.bot.middlewares.throttling import BotUserThrottleMiddleware
from app.bot.texts.common import BOT_TOO_MANY_REQUESTS_TEXT
from app.core.rate_limit import MinIntervalRateLimiter


class FakeUser:
    """Minimal Telegram user."""

    def __init__(self, *, user_id: int) -> None:
        self.id = user_id


def _build_callback(*, user_id: int) -> MagicMock:
    """Build a CallbackQuery-like object for middleware tests."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = FakeUser(user_id=user_id)
    callback.answers = []

    async def answer(text: str, *, show_alert: bool = False) -> None:
        callback.answers.append(text)

    callback.answer = answer
    return callback


@pytest.mark.asyncio
async def test_bot_throttle_middleware_blocks_second_callback_from_same_user() -> None:
    """Rapid callbacks from one user should be throttled."""
    middleware = BotUserThrottleMiddleware(
        limiter=MinIntervalRateLimiter(min_interval_seconds=10.0),
    )
    callback = _build_callback(user_id=42)
    handler_calls = 0

    async def handler(
        _event: object,
        _data: dict[str, Any],
    ) -> str:
        nonlocal handler_calls
        handler_calls += 1
        return "ok"

    await middleware(handler, callback, {})
    await middleware(handler, callback, {})

    assert handler_calls == 1
    assert callback.answers == [BOT_TOO_MANY_REQUESTS_TEXT]


@pytest.mark.asyncio
async def test_bot_throttle_middleware_blocks_second_update_callback() -> None:
    """Throttling should work when middleware receives a full Update object."""
    middleware = BotUserThrottleMiddleware(
        limiter=MinIntervalRateLimiter(min_interval_seconds=10.0),
    )
    callback = _build_callback(user_id=99)
    update = MagicMock(spec=Update)
    update.callback_query = callback
    update.message = None
    update.edited_message = None
    handler_calls = 0

    async def handler(
        _event: object,
        _data: dict[str, Any],
    ) -> str:
        nonlocal handler_calls
        handler_calls += 1
        return "ok"

    await middleware(handler, update, {})
    await middleware(handler, update, {})

    assert handler_calls == 1
    assert callback.answers == [BOT_TOO_MANY_REQUESTS_TEXT]


@pytest.mark.asyncio
async def test_bot_throttle_middleware_allows_different_users() -> None:
    """Different users should not share the same throttle bucket."""
    middleware = BotUserThrottleMiddleware(
        limiter=MinIntervalRateLimiter(min_interval_seconds=10.0),
    )
    first_callback = _build_callback(user_id=1)
    second_callback = _build_callback(user_id=2)
    handler_calls = 0

    async def handler(
        _event: object,
        _data: dict[str, Any],
    ) -> str:
        nonlocal handler_calls
        handler_calls += 1
        return "ok"

    await middleware(handler, first_callback, {})
    await middleware(handler, second_callback, {})

    assert handler_calls == 2
    assert first_callback.answers == []
    assert second_callback.answers == []
