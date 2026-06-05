"""Bot-level token risk check use cases.

This module keeps Telegram FSM and rendering logic out of routers.
Reusable token checking logic lives in app.services.token_risk_service.
"""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.constants import CB_RISK_CHECK_CHAIN_PREFIX
from app.bot.keyboards import (
    build_main_menu_keyboard,
    build_risk_check_address_keyboard,
    build_risk_check_chain_keyboard,
    build_risk_check_menu_keyboard,
)
from app.bot.states import RiskCheckStates
from app.bot.text_builders import build_token_check_result_text
from app.bot.texts import (
    GENERIC_ERROR_TEXT,
    INVALID_CONTRACT_ADDRESS_TEXT,
    MAIN_MENU_TEXT,
    RISK_CHECK_ENTER_ADDRESS_TEXT,
    RISK_CHECK_ENTER_CHAIN_TEXT,
    RISK_CHECK_FAILED_TEXT,
    RISK_CHECK_LOADING_TEXT,
    RISK_CHECK_MENU_TEXT,
    RISK_CHECK_TOKEN_NOT_FOUND_TEXT,
)
from app.bot.utils import edit_callback_message, safe_callback_answer
from app.bot.utils.fsm_screens import (
    delete_user_message,
    edit_fsm_screen_or_answer,
    remember_fsm_screen,
)
from app.core.error_messages import GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR
from app.core.exceptions import (
    SecurityProviderError,
    UserNotFoundError,
    ValidationError,
)
from app.services.token_risk_service import TokenRiskCheckData, check_token_risk
from app.services.users_service import get_user_by_telegram_id_or_raise
from app.utils.validators import validate_evm_address

RISK_CHECK_SCREEN_CHAT_ID_KEY = "risk_check_screen_chat_id"
RISK_CHECK_SCREEN_MESSAGE_ID_KEY = "risk_check_screen_message_id"


async def start_risk_check_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start token risk check and show chain picker."""
    await state.clear()
    await state.set_state(RiskCheckStates.choosing_chain)

    await edit_callback_message(
        callback,
        text=RISK_CHECK_ENTER_CHAIN_TEXT,
        reply_markup=build_risk_check_chain_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=RISK_CHECK_SCREEN_CHAT_ID_KEY,
        message_id_key=RISK_CHECK_SCREEN_MESSAGE_ID_KEY,
    )


async def choose_risk_check_chain_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Store selected chain and ask for contract address."""
    if callback.data is None:
        await safe_callback_answer(callback)
        return

    chain = callback.data.removeprefix(CB_RISK_CHECK_CHAIN_PREFIX)

    await state.update_data(chain=chain)
    await state.set_state(RiskCheckStates.entering_contract_address)

    await edit_callback_message(
        callback,
        text=RISK_CHECK_ENTER_ADDRESS_TEXT,
        reply_markup=build_risk_check_address_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=RISK_CHECK_SCREEN_CHAT_ID_KEY,
        message_id_key=RISK_CHECK_SCREEN_MESSAGE_ID_KEY,
    )


async def handle_contract_address_flow(
    *,
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Check a contract address and store the result."""
    if message.text is None:
        return

    if message.from_user is None:
        await _clear_state_and_show_main_menu_error(
            message=message,
            state=state,
        )
        return

    data = await state.get_data()
    chain = str(data.get("chain", ""))
    screen_chat_id = data.get(RISK_CHECK_SCREEN_CHAT_ID_KEY)
    screen_message_id = data.get(RISK_CHECK_SCREEN_MESSAGE_ID_KEY)

    await delete_user_message(message)

    try:
        contract_address = validate_evm_address(message.text)
    except ValidationError:
        await edit_fsm_screen_or_answer(
            message=message,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=INVALID_CONTRACT_ADDRESS_TEXT,
            reply_markup=build_risk_check_address_keyboard(),
        )
        return

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=RISK_CHECK_LOADING_TEXT,
        reply_markup=None,
    )

    try:
        user = await get_user_by_telegram_id_or_raise(
            session,
            telegram_id=message.from_user.id,
        )
    except UserNotFoundError:
        await _clear_state_and_show_main_menu_error(
            message=message,
            state=state,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
        )
        return

    try:
        token_check = await check_token_risk(
            session,
            data=TokenRiskCheckData(
                user_id=user.id,
                chain=chain,
                contract_address=contract_address,
            ),
        )
    except SecurityProviderError as exc:
        await _clear_state_and_show_risk_check_error(
            message=message,
            state=state,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=_get_security_provider_error_text(exc),
        )
        return
    except ValidationError:
        await _clear_state_and_show_risk_check_error(
            message=message,
            state=state,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=GENERIC_ERROR_TEXT,
        )
        return

    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=build_token_check_result_text(token_check),
        reply_markup=build_risk_check_menu_keyboard(),
    )


async def cancel_risk_check_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel token risk check and return to the main menu."""
    await state.clear()

    await edit_callback_message(
        callback,
        text=MAIN_MENU_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


async def show_risk_check_menu_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show token risk check menu."""
    await edit_callback_message(
        callback,
        text=RISK_CHECK_MENU_TEXT,
        reply_markup=build_risk_check_menu_keyboard(),
    )


async def _clear_state_and_show_main_menu_error(
    *,
    message: Message,
    state: FSMContext,
    chat_id: object | None = None,
    message_id: object | None = None,
) -> None:
    """Clear FSM state and show a generic main menu error."""
    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=chat_id,
        message_id=message_id,
        text=GENERIC_ERROR_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


async def _clear_state_and_show_risk_check_error(
    *,
    message: Message,
    state: FSMContext,
    text: str,
    chat_id: object | None = None,
    message_id: object | None = None,
) -> None:
    """Clear FSM state and show an error inside risk check flow."""
    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=build_risk_check_menu_keyboard(),
    )


def _get_security_provider_error_text(error: SecurityProviderError) -> str:
    """Return user-facing text for expected token security provider errors."""
    if str(error) == GOPLUS_TOKEN_DATA_NOT_FOUND_ERROR:
        return RISK_CHECK_TOKEN_NOT_FOUND_TEXT

    return RISK_CHECK_FAILED_TEXT
