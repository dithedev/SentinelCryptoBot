"""Helpers for safe Telegram callback message editing.

Telegram callback messages can be regular Message objects, inaccessible
messages, or None. Routers should not duplicate this defensive logic.
"""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

MESSAGE_NOT_MODIFIED_ERROR_MARKER = "message is not modified"
STALE_CALLBACK_ERROR_MARKERS = (
    "query is too old",
    "query id is invalid",
    "response timeout expired",
)


async def safe_callback_answer(
    callback: CallbackQuery,
    text: str | None = None,
    *,
    show_alert: bool = False,
) -> None:
    """Answer a callback query and ignore harmless Telegram stale-query errors."""
    try:
        if text is None:
            await callback.answer()
            return

        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as exc:
        if _is_harmless_callback_answer_error(exc):
            return

        raise


async def edit_callback_message(
    callback: CallbackQuery,
    *,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    answer_callback: bool = True,
) -> None:
    """Edit a callback message when Telegram allows it.

    If the original message is inaccessible, the callback is still answered so
    Telegram does not keep the loading spinner active for the user.

    Telegram also raises TelegramBadRequest when the new message text and
    keyboard are exactly the same as the current message. This is a harmless
    no-op case, for example when the user presses Refresh and prices have not
    changed yet. In that case we only answer the callback and do not treat it as
    an application error.

    answer_callback can be disabled when the caller has already answered the
    callback with a popup notification.
    """
    if not isinstance(callback.message, Message):
        if answer_callback:
            await safe_callback_answer(callback)
        return

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as exc:
        if _is_message_not_modified_error(exc):
            if answer_callback:
                await safe_callback_answer(callback)
            return

        raise

    if answer_callback:
        await safe_callback_answer(callback)


def _is_message_not_modified_error(error: TelegramBadRequest) -> bool:
    """Return True for Telegram's harmless no-op edit error."""
    return MESSAGE_NOT_MODIFIED_ERROR_MARKER in str(error).lower()


def _is_stale_callback_error(error: TelegramBadRequest) -> bool:
    """Return True when Telegram rejects an expired callback answer."""
    lowered_error = str(error).lower()
    return any(marker in lowered_error for marker in STALE_CALLBACK_ERROR_MARKERS)


def _is_harmless_callback_answer_error(error: TelegramBadRequest) -> bool:
    """Return True for callback answer errors that can be ignored safely."""
    return _is_stale_callback_error(error) or _is_message_not_modified_error(error)
