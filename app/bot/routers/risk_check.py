"""Token risk check router.

The router only maps Telegram updates to bot-level risk check use cases.
All FSM, validation, provider calls, database writes, and rendering live in
app.bot.services.risk_check.
"""

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants import (
    CB_RISK_CHECK_CANCEL,
    CB_RISK_CHECK_CHAIN_PREFIX,
    CB_RISK_CHECK_MENU,
    CB_RISK_CHECK_START,
)
from app.bot.services import (
    cancel_risk_check_flow,
    choose_risk_check_chain_flow,
    handle_contract_address_flow,
    show_risk_check_menu_flow,
    start_risk_check_flow,
)
from app.bot.states import RiskCheckStates

router = Router(name="risk_check")


@router.callback_query(F.data == CB_RISK_CHECK_START)
async def start_risk_check(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start token risk check flow."""
    await start_risk_check_flow(
        callback=callback,
        state=state,
    )


@router.callback_query(F.data.startswith(CB_RISK_CHECK_CHAIN_PREFIX))
async def choose_chain(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Handle chain selection."""
    await choose_risk_check_chain_flow(
        callback=callback,
        state=state,
    )


@router.message(StateFilter(RiskCheckStates.entering_contract_address), F.text)
async def handle_contract_address(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Handle contract address input."""
    await handle_contract_address_flow(
        message=message,
        state=state,
        session=session,
    )


@router.callback_query(F.data == CB_RISK_CHECK_CANCEL)
async def cancel_risk_check(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel token risk check flow."""
    await cancel_risk_check_flow(
        callback=callback,
        state=state,
    )


@router.callback_query(F.data == CB_RISK_CHECK_MENU)
async def back_to_risk_check_menu(callback: CallbackQuery) -> None:
    """Return to token risk check menu."""
    await show_risk_check_menu_flow(callback=callback)
