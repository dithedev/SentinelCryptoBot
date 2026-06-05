"""Main menu router.

The router only maps callback data to navigation use cases.
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.constants import (
    CB_ABOUT,
    CB_ALERTS_MENU,
    CB_MAIN_MENU,
    CB_RISK_CHECK_MENU,
)
from app.bot.services import (
    handle_unknown_callback_flow,
    show_about_flow,
    show_alerts_menu_navigation_flow,
    show_main_menu_flow,
    show_risk_check_menu_navigation_flow,
)

router = Router(name="menu")


@router.callback_query(F.data == CB_MAIN_MENU)
async def show_main_menu(callback: CallbackQuery) -> None:
    """Show the root navigation menu."""
    await show_main_menu_flow(callback=callback)


@router.callback_query(F.data == CB_ABOUT)
async def show_about(callback: CallbackQuery) -> None:
    """Show project information."""
    await show_about_flow(callback=callback)


@router.callback_query(F.data == CB_ALERTS_MENU)
async def show_alerts_menu(callback: CallbackQuery) -> None:
    """Show price alert menu."""
    await show_alerts_menu_navigation_flow(callback=callback)


@router.callback_query(F.data == CB_RISK_CHECK_MENU)
async def show_risk_check_menu(callback: CallbackQuery) -> None:
    """Show token risk check menu."""
    await show_risk_check_menu_navigation_flow(callback=callback)


@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery) -> None:
    """Handle unsupported callback actions safely."""
    await handle_unknown_callback_flow(callback=callback)
