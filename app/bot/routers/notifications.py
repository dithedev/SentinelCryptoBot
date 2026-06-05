"""Notification callback router."""

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.bot.constants import CB_NOTIFICATION_DISMISS
from app.bot.utils import safe_callback_answer

router = Router(name="notifications")


@router.callback_query(F.data == CB_NOTIFICATION_DISMISS)
async def dismiss_notification(callback: CallbackQuery) -> None:
    """Delete one notification message when the user dismisses it."""
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            await safe_callback_answer(callback)
            return

    await safe_callback_answer(callback)
