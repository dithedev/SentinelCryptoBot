"""FSM states for token risk checks."""

from aiogram.fsm.state import State, StatesGroup


class RiskCheckStates(StatesGroup):
    """Steps used while checking token risk."""

    choosing_chain = State()
    entering_contract_address = State()
