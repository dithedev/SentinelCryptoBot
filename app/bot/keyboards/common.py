"""Shared inline keyboard builders."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.constants import CB_CANCEL, CB_MAIN_MENU
from app.bot.texts.buttons import (
    BACK_BUTTON,
    BACK_TO_MAIN_MENU_BUTTON,
    CANCEL_BUTTON,
)


def build_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard with one button returning to the main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=BACK_TO_MAIN_MENU_BUTTON,
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ],
    )


def build_back_keyboard(
    *,
    callback_data: str,
) -> InlineKeyboardMarkup:
    """Build a keyboard with one custom back button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=BACK_BUTTON,
                    callback_data=callback_data,
                ),
            ],
        ],
    )


def build_cancel_keyboard(
    *,
    callback_data: str = CB_CANCEL,
) -> InlineKeyboardMarkup:
    """Build a keyboard with one cancel button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CANCEL_BUTTON,
                    callback_data=callback_data,
                ),
            ],
        ],
    )
