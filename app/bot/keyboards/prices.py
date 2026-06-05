"""Inline keyboard builders for market price screens."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.constants import CB_MAIN_MENU, CB_PRICES_IGNORE, CB_PRICES_REFRESH
from app.bot.texts.buttons import (
    BACK_TO_MAIN_MENU_BUTTON,
    PRICES_REFRESH_BUTTON,
)


def build_prices_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for the bot market prices screen."""
    return _build_prices_keyboard(refresh_callback_data=CB_PRICES_REFRESH)


def build_prices_loading_keyboard() -> InlineKeyboardMarkup:
    """Build a stable prices keyboard with disabled refresh while loading."""
    return _build_prices_keyboard(refresh_callback_data=CB_PRICES_IGNORE)


def _build_prices_keyboard(
    *,
    refresh_callback_data: str,
) -> InlineKeyboardMarkup:
    """Build keyboard for the bot market prices screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=PRICES_REFRESH_BUTTON,
                    callback_data=refresh_callback_data,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BACK_TO_MAIN_MENU_BUTTON,
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ],
    )
