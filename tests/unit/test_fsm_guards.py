"""Unit tests for FSM callback guards."""

import pytest
from app.bot.constants import (
    CB_ALERTS_CANCEL,
    CB_ALERTS_IGNORE,
    CB_MAIN_MENU,
    CB_NOTIFICATION_DISMISS,
    CB_RISK_CHECK_CANCEL,
    CB_RISK_CHECK_CHAIN_PREFIX,
    CB_RISK_CHECK_START,
    CB_WHALES_MENU,
)
from app.bot.services.fsm_guards import block_callback_during_locked_fsm
from app.bot.states import AlertCreationStates, RiskCheckStates


class FakeState:
    """Minimal FSM state stub."""

    def __init__(self, *, current_state: str | None) -> None:
        self.current_state = current_state
        self.answers: list[tuple[str | None, bool]] = []

    async def get_state(self) -> str | None:
        return self.current_state

    async def set_state(self, _state: object) -> None:
        return None


class FakeCallback:
    """Minimal callback object for FSM guard tests."""

    def __init__(self, *, data: str | None) -> None:
        self.data = data
        self.answers: list[tuple[str | None, bool]] = []

    async def answer(
        self,
        text: str | None = None,
        *,
        show_alert: bool = False,
    ) -> None:
        self.answers.append((text, show_alert))


@pytest.mark.asyncio
async def test_block_callback_allows_cancel_during_alert_price_input() -> None:
    """Cancel should remain available while entering alert price."""
    callback = FakeCallback(data=CB_ALERTS_CANCEL)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False
    assert callback.answers == []


@pytest.mark.asyncio
async def test_block_callback_blocks_unrelated_button_during_alert_price_input() -> (
    None
):
    """Unrelated callbacks should be answered without changing flow."""
    callback = FakeCallback(data=CB_WHALES_MENU)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is True
    assert len(callback.answers) == 1
    assert callback.answers[0][1] is True


@pytest.mark.asyncio
async def test_block_callback_ignores_callbacks_outside_locked_states() -> None:
    """Callbacks outside locked FSM states should pass through."""
    callback = FakeCallback(data=CB_WHALES_MENU)
    state = FakeState(current_state=None)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False


@pytest.mark.asyncio
async def test_block_callback_blocks_main_menu_during_alert_price_input() -> None:
    """Main menu navigation should be blocked while entering alert price."""
    callback = FakeCallback(data=CB_MAIN_MENU)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is True


@pytest.mark.asyncio
async def test_block_callback_blocks_risk_check_during_alert_price_input() -> None:
    """Other feature flows should not start while alert price input is active."""
    callback = FakeCallback(data=CB_RISK_CHECK_START)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is True


@pytest.mark.asyncio
async def test_block_callback_blocks_foreign_cancel_during_alert_price_input() -> None:
    """Cancel buttons from other flows must not cancel the active alert step."""
    callback = FakeCallback(data=CB_RISK_CHECK_CANCEL)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is True


@pytest.mark.asyncio
async def test_block_callback_allows_chain_choice_during_risk_check_chain_step() -> (
    None
):
    """Risk check chain buttons should stay available on the chain step."""
    callback = FakeCallback(data=f"{CB_RISK_CHECK_CHAIN_PREFIX}eth")
    state = FakeState(current_state=RiskCheckStates.choosing_chain.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False


@pytest.mark.asyncio
async def test_block_callback_allows_cancel_during_risk_check_address_input() -> None:
    """Risk check cancel should remain available while entering an address."""
    callback = FakeCallback(data=CB_RISK_CHECK_CANCEL)
    state = FakeState(current_state=RiskCheckStates.entering_contract_address.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False


@pytest.mark.asyncio
async def test_block_callback_blocks_main_menu_during_risk_check_address_input() -> (
    None
):
    """Navigation should not interrupt active risk check address input."""
    callback = FakeCallback(data=CB_MAIN_MENU)
    state = FakeState(current_state=RiskCheckStates.entering_contract_address.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is True


@pytest.mark.asyncio
async def test_block_callback_allows_blank_coin_pad_during_alert_coin_selection() -> (
    None
):
    """Blank grid padding buttons should stay silent during coin selection."""
    callback = FakeCallback(data=CB_ALERTS_IGNORE)
    state = FakeState(current_state=AlertCreationStates.choosing_coin.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False
    assert callback.answers == []


@pytest.mark.asyncio
async def test_block_callback_allows_notification_dismiss_during_locked_state() -> None:
    """Notification cleanup should not interrupt or get blocked by active flows."""
    callback = FakeCallback(data=CB_NOTIFICATION_DISMISS)
    state = FakeState(current_state=AlertCreationStates.entering_price.state)

    was_blocked = await block_callback_during_locked_fsm(
        callback=callback,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
    )

    assert was_blocked is False
