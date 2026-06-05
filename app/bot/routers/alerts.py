"""Price alert router.

The router only maps Telegram updates to bot-level alert use cases.
All FSM, parsing, domain calls, and rendering live in app.bot.services.alerts.
"""

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants import (
    CB_ALERTS_BACK_TO_MENU,
    CB_ALERTS_CANCEL,
    CB_ALERTS_COIN_PREFIX,
    CB_ALERTS_CONDITION_ABOVE,
    CB_ALERTS_CONDITION_BELOW,
    CB_ALERTS_CREATE,
    CB_ALERTS_DELETE_PREFIX,
    CB_ALERTS_HISTORY,
    CB_ALERTS_IGNORE,
    CB_ALERTS_LIST,
    CB_ALERTS_PAGE_PREFIX,
    CB_ALERTS_VIEW_PREFIX,
)
from app.bot.services import (
    cancel_alert_creation_flow,
    choose_alert_coin_flow,
    choose_alert_condition_flow,
    delete_alert_from_callback_flow,
    handle_alert_price_input_flow,
    ignore_alerts_callback_flow,
    show_alerts_menu_flow,
    show_alerts_page_from_callback_flow,
    show_default_alerts_page_flow,
    start_alert_creation_flow,
    toggle_alert_details_flow,
)
from app.bot.states import AlertCreationStates

router = Router(name="alerts")


@router.callback_query(F.data == CB_ALERTS_CREATE)
async def start_alert_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start price alert creation flow."""
    await start_alert_creation_flow(
        callback=callback,
        state=state,
    )


@router.callback_query(F.data.startswith(CB_ALERTS_COIN_PREFIX))
async def choose_alert_coin(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle coin selection."""
    await choose_alert_coin_flow(
        callback=callback,
        state=state,
    )


@router.callback_query(
    F.data.in_(
        {
            CB_ALERTS_CONDITION_ABOVE,
            CB_ALERTS_CONDITION_BELOW,
        },
    ),
)
async def choose_alert_condition(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle condition selection."""
    await choose_alert_condition_flow(
        callback=callback,
        state=state,
    )


@router.message(StateFilter(AlertCreationStates.entering_price), F.text)
async def handle_alert_price_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle target price input."""
    await handle_alert_price_input_flow(
        message=message,
        state=state,
        session=session,
    )


@router.callback_query(F.data == CB_ALERTS_BACK_TO_MENU)
async def back_to_alerts_menu(callback: CallbackQuery) -> None:
    """Return to the top-level alerts menu."""
    await show_alerts_menu_flow(callback=callback)


@router.callback_query(F.data == CB_ALERTS_LIST)
async def show_user_alerts(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show user alerts."""
    await show_default_alerts_page_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data == CB_ALERTS_HISTORY)
async def show_alert_history(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show legacy alert history callback as all alerts."""
    await show_default_alerts_page_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data.startswith(CB_ALERTS_PAGE_PREFIX))
async def change_alert_page(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Open a selected alert list page."""
    await show_alerts_page_from_callback_flow(
        callback=callback,
        session=session,
    )


@router.callback_query(F.data.startswith(CB_ALERTS_VIEW_PREFIX))
async def toggle_alert_details(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Toggle inline details for one alert."""
    await toggle_alert_details_flow(
        callback=callback,
        session=session,
        callback_prefix=CB_ALERTS_VIEW_PREFIX,
    )


@router.callback_query(F.data.startswith(CB_ALERTS_DELETE_PREFIX))
async def delete_alert_callback(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Delete a selected alert."""
    await delete_alert_from_callback_flow(
        callback=callback,
        session=session,
        callback_prefix=CB_ALERTS_DELETE_PREFIX,
    )


@router.callback_query(F.data == CB_ALERTS_CANCEL)
async def cancel_alert_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel alert creation."""
    await cancel_alert_creation_flow(
        callback=callback,
        state=state,
    )


@router.callback_query(F.data == CB_ALERTS_IGNORE)
async def ignore_alerts_callback(callback: CallbackQuery) -> None:
    """Answer no-op alert callbacks."""
    await ignore_alerts_callback_flow(callback=callback)
