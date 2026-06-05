"""Middleware that blocks unrelated callbacks during locked FSM steps."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, TelegramObject

from app.bot.services.fsm_guards import block_callback_during_locked_fsm


class FsmCallbackGuardMiddleware(BaseMiddleware):
    """Stop unrelated inline button presses during numeric FSM input."""

    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            state: FSMContext | None = data.get("state")

            if state is not None:
                was_blocked = await block_callback_during_locked_fsm(
                    callback=event,
                    state=state,
                )

                if was_blocked:
                    return None

        return await handler(event, data)
