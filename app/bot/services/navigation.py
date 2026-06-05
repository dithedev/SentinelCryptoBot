"""Bot-level navigation screen use cases.

Routers should not build static screens directly. This service owns simple
navigation rendering for menu, about, alerts entry, risk check entry, and
unsupported callbacks.
"""

from aiogram.types import CallbackQuery

from app.bot.keyboards import (
    build_alerts_menu_keyboard,
    build_back_to_main_menu_keyboard,
    build_main_menu_keyboard,
    build_risk_check_menu_keyboard,
)
from app.bot.texts import (
    ABOUT_TEXT,
    ALERTS_MENU_TEXT,
    MAIN_MENU_TEXT,
    RISK_CHECK_MENU_TEXT,
    UNKNOWN_ACTION_TEXT,
)
from app.bot.utils import edit_callback_message


async def show_main_menu_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show the root navigation menu."""
    await edit_callback_message(
        callback,
        text=MAIN_MENU_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


async def show_about_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show project information screen."""
    await edit_callback_message(
        callback,
        text=ABOUT_TEXT,
        reply_markup=build_back_to_main_menu_keyboard(),
    )


async def show_alerts_menu_navigation_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show price alert menu from global navigation."""
    await edit_callback_message(
        callback,
        text=ALERTS_MENU_TEXT,
        reply_markup=build_alerts_menu_keyboard(),
    )


async def show_risk_check_menu_navigation_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show token risk check menu from global navigation."""
    await edit_callback_message(
        callback,
        text=RISK_CHECK_MENU_TEXT,
        reply_markup=build_risk_check_menu_keyboard(),
    )


async def handle_unknown_callback_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Handle unsupported callback actions safely."""
    await edit_callback_message(
        callback,
        text=UNKNOWN_ACTION_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
