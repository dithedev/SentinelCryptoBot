"""Inline keyboard builders for whale alerts."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.callbacks.whales import build_whale_events_page_callback
from app.bot.constants import (
    CB_MAIN_MENU,
    CB_WHALES_BACK_TO_MENU,
    CB_WHALES_CANCEL,
    CB_WHALES_CHANGE_THRESHOLD,
    CB_WHALES_EVENTS,
    CB_WHALES_IGNORE,
    CB_WHALES_TOGGLE,
)
from app.bot.texts.buttons import (
    BACK_TO_MAIN_MENU_BUTTON,
    CANCEL_BUTTON,
    WHALES_CHANGE_THRESHOLD_BUTTON,
    WHALES_DISABLE_BUTTON,
    WHALES_ENABLE_BUTTON,
    WHALES_EVENTS_BUTTON,
    WHALES_NEXT_PAGE_BUTTON,
    WHALES_PAGE_BUTTON_TEMPLATE,
    WHALES_PREVIOUS_PAGE_BUTTON,
)
from app.database.models.whale import WhaleAlertSettings


def build_whales_menu_keyboard(settings: WhaleAlertSettings) -> InlineKeyboardMarkup:
    """Build whale alerts settings menu."""
    toggle_button = InlineKeyboardButton(
        text=WHALES_DISABLE_BUTTON if settings.is_enabled else WHALES_ENABLE_BUTTON,
        callback_data=CB_WHALES_TOGGLE,
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [toggle_button],
            [
                InlineKeyboardButton(
                    text=WHALES_CHANGE_THRESHOLD_BUTTON,
                    callback_data=CB_WHALES_CHANGE_THRESHOLD,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=WHALES_EVENTS_BUTTON,
                    callback_data=CB_WHALES_EVENTS,
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


def build_whale_threshold_input_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard shown while waiting for threshold input."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CANCEL_BUTTON,
                    callback_data=CB_WHALES_CANCEL,
                ),
            ],
        ],
    )


def build_whale_events_page_keyboard(
    *,
    page_number: int,
    total_pages: int,
    has_more: bool,
) -> InlineKeyboardMarkup:
    """Build paginated whale events keyboard."""
    safe_total_pages = max(total_pages, 1)
    safe_page_number = min(max(page_number, 0), safe_total_pages - 1)

    previous_callback = CB_WHALES_IGNORE
    if safe_page_number > 0:
        previous_callback = build_whale_events_page_callback(
            page_number=safe_page_number - 1,
        )

    next_callback = CB_WHALES_IGNORE
    if has_more and safe_page_number < safe_total_pages - 1:
        next_callback = build_whale_events_page_callback(
            page_number=safe_page_number + 1,
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=WHALES_PREVIOUS_PAGE_BUTTON,
                    callback_data=previous_callback,
                ),
                InlineKeyboardButton(
                    text=WHALES_PAGE_BUTTON_TEMPLATE.format(
                        page=safe_page_number + 1,
                        total_pages=safe_total_pages,
                    ),
                    callback_data=CB_WHALES_IGNORE,
                ),
                InlineKeyboardButton(
                    text=WHALES_NEXT_PAGE_BUTTON,
                    callback_data=next_callback,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BACK_TO_MAIN_MENU_BUTTON,
                    callback_data=CB_WHALES_BACK_TO_MENU,
                ),
            ],
        ],
    )
