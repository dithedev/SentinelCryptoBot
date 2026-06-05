"""FSM states for price alert creation."""

from aiogram.fsm.state import State, StatesGroup


class AlertCreationStates(StatesGroup):
    """Steps used while creating a price alert."""

    choosing_coin = State()
    choosing_condition = State()
    entering_price = State()
