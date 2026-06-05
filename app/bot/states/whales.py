"""FSM states for whale alert settings."""

from aiogram.fsm.state import State, StatesGroup


class WhaleSettingsStates(StatesGroup):
    """Steps used while updating whale alert threshold."""

    entering_threshold = State()
