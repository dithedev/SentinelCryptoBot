"""Per-user throttling for incoming Telegram bot updates."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User

from app.bot.texts.common import BOT_TOO_MANY_REQUESTS_TEXT
from app.bot.utils.callbacks import safe_callback_answer
from app.core.rate_limit import MinIntervalRateLimiter


def _extract_user(event: TelegramObject) -> User | None:
    """Return Telegram user from supported update types."""
    if isinstance(event, CallbackQuery):
        return event.from_user

    if isinstance(event, Message):
        return event.from_user

    if isinstance(event, Update):
        if event.callback_query is not None:
            return event.callback_query.from_user

        if event.message is not None:
            return event.message.from_user

        if event.edited_message is not None:
            return event.edited_message.from_user

    return None


def _extract_callback(event: TelegramObject) -> CallbackQuery | None:
    """Return callback query when the update is a button press."""
    if isinstance(event, CallbackQuery):
        return event

    if isinstance(event, Update) and event.callback_query is not None:
        return event.callback_query

    return None


class BotUserThrottleMiddleware(BaseMiddleware):
    """Limit how fast one Telegram user can trigger bot handlers."""

    def __init__(
        self,
        *,
        limiter: MinIntervalRateLimiter,
    ) -> None:
        self._limiter = limiter

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = _extract_user(event)

        if user is None:
            return await handler(event, data)

        if self._limiter.allow(str(user.id)):
            return await handler(event, data)

        callback = _extract_callback(event)

        if callback is not None:
            await safe_callback_answer(
                callback,
                BOT_TOO_MANY_REQUESTS_TEXT,
                show_alert=False,
            )

        return None
