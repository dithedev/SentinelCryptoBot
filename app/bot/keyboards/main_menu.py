"""Main menu inline keyboard builders."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.bot.constants import (
    CB_ABOUT,
    CB_ALERTS_MENU,
    CB_PRICES_MENU,
    CB_RISK_CHECK_MENU,
    CB_WHALES_MENU,
)
from app.bot.texts.buttons import (
    MAIN_MENU_ABOUT_BUTTON,
    MAIN_MENU_ALERTS_BUTTON,
    MAIN_MENU_MINI_APP_BUTTON,
    MAIN_MENU_PRICES_BUTTON,
    MAIN_MENU_RISK_CHECK_BUTTON,
    MAIN_MENU_WHALES_BUTTON,
)
from app.core.config import get_settings


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main navigation keyboard.

    The Mini App button is added only when MINIAPP_URL is configured. This keeps
    local development safe: the bot can work without a public HTTPS Mini App URL.
    """
    settings = get_settings()

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=MAIN_MENU_PRICES_BUTTON,
                callback_data=CB_PRICES_MENU,
            ),
        ],
        [
            InlineKeyboardButton(
                text=MAIN_MENU_ALERTS_BUTTON,
                callback_data=CB_ALERTS_MENU,
            ),
        ],
        [
            InlineKeyboardButton(
                text=MAIN_MENU_WHALES_BUTTON,
                callback_data=CB_WHALES_MENU,
            ),
        ],
        [
            InlineKeyboardButton(
                text=MAIN_MENU_RISK_CHECK_BUTTON,
                callback_data=CB_RISK_CHECK_MENU,
            ),
        ],
    ]

    bottom_row = [
        InlineKeyboardButton(
            text=MAIN_MENU_ABOUT_BUTTON,
            callback_data=CB_ABOUT,
        ),
    ]

    if settings.miniapp_url is not None:
        bottom_row.append(
            InlineKeyboardButton(
                text=MAIN_MENU_MINI_APP_BUTTON,
                web_app=WebAppInfo(url=settings.miniapp_url),
            ),
        )

    rows.append(bottom_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)
