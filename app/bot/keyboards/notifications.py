"""Inline keyboard builders for one-off notification messages."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.constants import CB_NOTIFICATION_DISMISS
from app.bot.texts.buttons import NOTIFICATION_DISMISS_BUTTON


def build_notification_dismiss_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard that lets users delete a notification message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=NOTIFICATION_DISMISS_BUTTON,
                    callback_data=CB_NOTIFICATION_DISMISS,
                ),
            ],
        ],
    )
