"""Helpers that block unrelated callbacks during active FSM flows."""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.constants import (
    CB_ALERTS_CANCEL,
    CB_ALERTS_COIN_PREFIX,
    CB_ALERTS_CONDITION_ABOVE,
    CB_ALERTS_CONDITION_BELOW,
    CB_ALERTS_IGNORE,
    CB_NOTIFICATION_DISMISS,
    CB_RISK_CHECK_CANCEL,
    CB_RISK_CHECK_CHAIN_PREFIX,
    CB_WHALES_CANCEL,
    CB_WHALES_IGNORE,
)
from app.bot.states import AlertCreationStates, RiskCheckStates, WhaleSettingsStates
from app.bot.texts.common import FSM_LOCKED_CALLBACK_TEXT
from app.bot.utils.callbacks import safe_callback_answer

_ALERT_CHOOSING_COIN_STATE = AlertCreationStates.choosing_coin.state
_ALERT_CHOOSING_CONDITION_STATE = AlertCreationStates.choosing_condition.state
_ALERT_ENTERING_PRICE_STATE = AlertCreationStates.entering_price.state
_RISK_CHECK_CHOOSING_CHAIN_STATE = RiskCheckStates.choosing_chain.state
_RISK_CHECK_ENTERING_CONTRACT_ADDRESS_STATE = (
    RiskCheckStates.entering_contract_address.state
)
_WHALE_ENTERING_THRESHOLD_STATE = WhaleSettingsStates.entering_threshold.state


def is_callback_allowed_during_locked_fsm(
    *,
    callback_data: str | None,
    current_state: str,
) -> bool:
    """Return True when a callback may run during a locked FSM step."""
    if callback_data is None:
        return False

    if callback_data in {
        CB_NOTIFICATION_DISMISS,
        CB_ALERTS_IGNORE,
        CB_WHALES_IGNORE,
    }:
        return True

    if current_state == _ALERT_CHOOSING_COIN_STATE:
        return callback_data == CB_ALERTS_CANCEL or callback_data.startswith(
            CB_ALERTS_COIN_PREFIX
        )

    if current_state == _ALERT_CHOOSING_CONDITION_STATE:
        return callback_data in {
            CB_ALERTS_CANCEL,
            CB_ALERTS_CONDITION_ABOVE,
            CB_ALERTS_CONDITION_BELOW,
        }

    if current_state == _ALERT_ENTERING_PRICE_STATE:
        return callback_data == CB_ALERTS_CANCEL

    if current_state == _RISK_CHECK_CHOOSING_CHAIN_STATE:
        return callback_data == CB_RISK_CHECK_CANCEL or callback_data.startswith(
            CB_RISK_CHECK_CHAIN_PREFIX
        )

    if current_state == _RISK_CHECK_ENTERING_CONTRACT_ADDRESS_STATE:
        return callback_data == CB_RISK_CHECK_CANCEL

    if current_state == _WHALE_ENTERING_THRESHOLD_STATE:
        return callback_data == CB_WHALES_CANCEL

    return True


async def block_callback_during_locked_fsm(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> bool:
    """Block unrelated callbacks while the user is inside a locked FSM flow.

    Returns True when the callback was answered and the handler should stop.
    """
    current_state = await state.get_state()

    if current_state is None:
        return False

    if is_callback_allowed_during_locked_fsm(
        callback_data=callback.data,
        current_state=current_state,
    ):
        return False

    await safe_callback_answer(
        callback,
        FSM_LOCKED_CALLBACK_TEXT,
        show_alert=True,
    )
    return True
