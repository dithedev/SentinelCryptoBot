"""Inline keyboard builders for token risk checks."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.constants import (
    CB_MAIN_MENU,
    CB_RISK_CHECK_CANCEL,
    CB_RISK_CHECK_CHAIN_PREFIX,
    CB_RISK_CHECK_START,
)
from app.bot.texts.buttons import (
    BACK_TO_MAIN_MENU_BUTTON,
    CANCEL_BUTTON,
    RISK_CHECK_START_BUTTON,
)
from app.core.constants import (
    SUPPORTED_CHAINS,
)


def build_risk_check_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the token risk check menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=RISK_CHECK_START_BUTTON,
                    callback_data=CB_RISK_CHECK_START,
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


def build_risk_check_chain_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard with supported chains."""
    rows: list[list[InlineKeyboardButton]] = []

    for chain in sorted(SUPPORTED_CHAINS):
        rows.append(
            [
                InlineKeyboardButton(
                    text=chain.upper(),
                    callback_data=f"{CB_RISK_CHECK_CHAIN_PREFIX}{chain}",
                ),
            ],
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=CANCEL_BUTTON,
                callback_data=CB_RISK_CHECK_CANCEL,
            ),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_risk_check_address_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard shown while waiting for contract address input."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CANCEL_BUTTON,
                    callback_data=CB_RISK_CHECK_CANCEL,
                ),
            ],
        ],
    )
