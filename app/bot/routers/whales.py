"""Whale alerts router.

The router only maps Telegram updates to bot-level whale use cases.
"""

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants import (
    CB_WHALES_BACK_TO_MENU,
    CB_WHALES_CANCEL,
    CB_WHALES_CHANGE_THRESHOLD,
    CB_WHALES_EVENTS,
    CB_WHALES_EVENTS_PAGE_PREFIX,
    CB_WHALES_IGNORE,
    CB_WHALES_MENU,
    CB_WHALES_TOGGLE,
)
from app.bot.services.whales import (
    cancel_whale_settings_flow,
    handle_whale_threshold_input_flow,
    ignore_whales_callback_flow,
    show_whale_events_from_callback_flow,
    show_whale_events_page_flow,
    show_whales_menu_flow,
    start_whale_threshold_change_flow,
    toggle_whale_alerts_flow,
)
from app.bot.states import WhaleSettingsStates

router = Router(name="whales")


@router.callback_query(F.data == CB_WHALES_MENU)
async def show_whales_menu(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show whale alerts menu."""
    await show_whales_menu_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data == CB_WHALES_TOGGLE)
async def toggle_whale_alerts(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Toggle whale alerts for the current user."""
    await toggle_whale_alerts_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data == CB_WHALES_CHANGE_THRESHOLD)
async def start_threshold_change(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start whale threshold update flow."""
    await start_whale_threshold_change_flow(
        callback=callback,
        state=state,
    )


@router.message(StateFilter(WhaleSettingsStates.entering_threshold), F.text)
async def handle_threshold_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle whale threshold input."""
    await handle_whale_threshold_input_flow(
        message=message,
        state=state,
        session=session,
    )


@router.callback_query(F.data == CB_WHALES_CANCEL)
async def cancel_whale_settings(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Cancel whale settings update."""
    await cancel_whale_settings_flow(
        callback=callback,
        state=state,
        session=session,
    )


@router.callback_query(F.data == CB_WHALES_EVENTS)
async def show_whale_events(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show the first page of whale events."""
    await show_whale_events_page_flow(
        callback=callback,
        session=session,
        page_number=0,
    )


@router.callback_query(F.data.startswith(CB_WHALES_EVENTS_PAGE_PREFIX))
async def change_whale_events_page(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Open a selected whale events page."""
    await show_whale_events_from_callback_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data == CB_WHALES_IGNORE)
async def ignore_whales_callback(callback: CallbackQuery) -> None:
    """Answer disabled or no-op whale callbacks."""
    await ignore_whales_callback_flow(callback=callback)


@router.callback_query(F.data == CB_WHALES_BACK_TO_MENU)
async def back_to_whales_menu(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Return to whale alerts menu from events browser."""
    await show_whales_menu_flow(
        callback=callback,
        session=session,
    )
