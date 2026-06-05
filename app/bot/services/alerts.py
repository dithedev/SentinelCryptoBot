"""Bot-level price alert use cases.

This module keeps Telegram-specific alert flow logic out of routers.
"""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.alerts import (
    AlertActionPayload,
    parse_alert_action_payload,
    parse_alert_page_payload,
)
from app.bot.constants import (
    CB_ALERTS_COIN_PREFIX,
    CB_ALERTS_CONDITION_ABOVE,
    CB_ALERTS_PAGE_PREFIX,
)
from app.bot.keyboards import (
    build_alert_coin_keyboard,
    build_alert_condition_keyboard,
    build_alert_price_input_keyboard,
    build_alerts_menu_keyboard,
    build_main_menu_keyboard,
)
from app.bot.screens import AlertPageRequest, BotScreen, build_alerts_page_screen
from app.bot.services.users import get_current_user_id
from app.bot.states import AlertCreationStates
from app.bot.text_builders import ALERT_FILTER_ALL, build_alert_created_text
from app.bot.texts import (
    ALERT_CREATION_LOADING_TEXT,
    ALERT_DELETED_TEXT,
    ALERT_NOT_FOUND_TEXT,
    ALERTS_MENU_TEXT,
    CHOOSE_ALERT_COIN_TEXT,
    CHOOSE_ALERT_CONDITION_TEXT,
    ENTER_ALERT_PRICE_TEXT,
    GENERIC_ERROR_TEXT,
    MAIN_MENU_TEXT,
    VALIDATION_ERROR_TEMPLATE,
)
from app.bot.utils import edit_callback_message, safe_callback_answer
from app.bot.utils.fsm_screens import (
    delete_user_message,
    edit_fsm_screen_or_answer,
    remember_fsm_screen,
)
from app.core.exceptions import AlertNotFoundError, UserNotFoundError, ValidationError
from app.database.models.alert import Alert, AlertCondition
from app.services.alerts_service import (
    AlertCreateData,
    create_price_alert,
    disable_user_alert,
)
from app.utils.money import parse_alert_price

ALERT_CREATION_SCREEN_CHAT_ID_KEY = "alert_creation_screen_chat_id"
ALERT_CREATION_SCREEN_MESSAGE_ID_KEY = "alert_creation_screen_message_id"


async def start_alert_creation_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start price alert creation and show coin picker."""
    await state.clear()
    await state.set_state(AlertCreationStates.choosing_coin)

    await edit_callback_message(
        callback,
        text=CHOOSE_ALERT_COIN_TEXT,
        reply_markup=build_alert_coin_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=ALERT_CREATION_SCREEN_CHAT_ID_KEY,
        message_id_key=ALERT_CREATION_SCREEN_MESSAGE_ID_KEY,
    )


async def choose_alert_coin_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Store selected coin and show condition picker."""
    if callback.data is None:
        await safe_callback_answer(callback)
        return

    coin_id = callback.data.removeprefix(CB_ALERTS_COIN_PREFIX)

    await state.update_data(coin_id=coin_id)
    await state.set_state(AlertCreationStates.choosing_condition)

    await edit_callback_message(
        callback,
        text=CHOOSE_ALERT_CONDITION_TEXT,
        reply_markup=build_alert_condition_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=ALERT_CREATION_SCREEN_CHAT_ID_KEY,
        message_id_key=ALERT_CREATION_SCREEN_MESSAGE_ID_KEY,
    )


async def choose_alert_condition_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Store selected condition and ask for target price."""
    condition = _resolve_alert_condition(callback.data)

    await state.update_data(condition=condition.value)
    await state.set_state(AlertCreationStates.entering_price)

    await edit_callback_message(
        callback,
        text=ENTER_ALERT_PRICE_TEXT,
        reply_markup=build_alert_price_input_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=ALERT_CREATION_SCREEN_CHAT_ID_KEY,
        message_id_key=ALERT_CREATION_SCREEN_MESSAGE_ID_KEY,
    )


async def handle_alert_price_input_flow(
    *,
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Create an alert from FSM data and incoming price message."""
    if message.text is None:
        return

    data = await state.get_data()
    screen_chat_id = data.get(ALERT_CREATION_SCREEN_CHAT_ID_KEY)
    screen_message_id = data.get(ALERT_CREATION_SCREEN_MESSAGE_ID_KEY)

    await delete_user_message(message)

    try:
        parse_alert_price(message.text)
    except ValidationError as exc:
        await edit_fsm_screen_or_answer(
            message=message,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=VALIDATION_ERROR_TEMPLATE.format(message=str(exc)),
            reply_markup=build_alert_price_input_keyboard(),
        )
        return

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=ALERT_CREATION_LOADING_TEXT,
        reply_markup=None,
    )

    try:
        alert = await _create_alert_from_state(
            message=message,
            state=state,
            session=session,
        )
    except ValidationError as exc:
        await edit_fsm_screen_or_answer(
            message=message,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=VALIDATION_ERROR_TEMPLATE.format(message=str(exc)),
            reply_markup=build_alert_price_input_keyboard(),
        )
        return
    except (KeyError, ValueError, UserNotFoundError):
        await _clear_state_and_show_generic_error(
            message=message,
            state=state,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
        )
        return

    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=build_alert_created_text(alert),
        reply_markup=build_alerts_menu_keyboard(),
    )


async def show_alerts_menu_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Show the top-level alerts menu."""
    await edit_callback_message(
        callback,
        text=ALERTS_MENU_TEXT,
        reply_markup=build_alerts_menu_keyboard(),
    )


async def show_default_alerts_page_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show the first page of all user alerts."""
    await show_alerts_page_flow(
        callback=callback,
        session=session,
        request=AlertPageRequest(
            filter_value=ALERT_FILTER_ALL,
            page_number=0,
        ),
    )


async def show_alerts_page_from_callback_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Parse page callback and show the requested alert page."""
    if callback.data is None:
        await safe_callback_answer(callback)
        return

    payload = parse_alert_page_payload(
        callback.data.removeprefix(CB_ALERTS_PAGE_PREFIX),
    )

    await show_alerts_page_flow(
        callback=callback,
        session=session,
        request=AlertPageRequest(
            filter_value=payload.filter_value,
            page_number=payload.page_number,
        ),
    )


async def toggle_alert_details_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
    callback_prefix: str,
) -> None:
    """Toggle inline alert details on the My alerts screen."""
    payload = _parse_alert_action_from_callback(
        callback=callback,
        callback_prefix=callback_prefix,
    )

    if payload is None or payload.alert_id is None:
        await safe_callback_answer(callback)
        return

    await show_alerts_page_flow(
        callback=callback,
        session=session,
        request=AlertPageRequest(
            filter_value=payload.filter_value,
            page_number=payload.page_number,
            selected_alert_id=_resolve_selected_alert_id(payload),
        ),
    )


async def delete_alert_from_callback_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
    callback_prefix: str,
) -> None:
    """Disable an alert and refresh the current My alerts page.

    The function name is kept for import compatibility with the existing router.
    """
    payload = _parse_alert_action_from_callback(
        callback=callback,
        callback_prefix=callback_prefix,
    )

    if payload is None or payload.alert_id is None:
        await safe_callback_answer(callback)
        return

    try:
        user_id = await get_current_user_id(
            event=callback,
            session=session,
        )
        await disable_user_alert(
            session,
            user_id=user_id,
            alert_id=payload.alert_id,
        )
    except (ValueError, AlertNotFoundError):
        await edit_callback_message(
            callback,
            text=ALERT_NOT_FOUND_TEXT,
            reply_markup=build_alerts_menu_keyboard(),
        )
        return
    except UserNotFoundError:
        await edit_callback_message(
            callback,
            text=GENERIC_ERROR_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await safe_callback_answer(
        callback,
        ALERT_DELETED_TEXT,
        show_alert=True,
    )

    await show_alerts_page_flow(
        callback=callback,
        session=session,
        request=AlertPageRequest(
            filter_value=payload.filter_value,
            page_number=payload.page_number,
            selected_alert_id=payload.alert_id,
        ),
        answer_callback=False,
    )


async def cancel_alert_creation_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel alert creation and return to the main menu."""
    await state.clear()

    await edit_callback_message(
        callback,
        text=MAIN_MENU_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


async def ignore_alerts_callback_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Answer disabled or no-op alert callbacks."""
    await safe_callback_answer(callback)


async def show_alerts_page_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
    request: AlertPageRequest,
    answer_callback: bool = True,
) -> None:
    """Build and render the My alerts screen."""
    try:
        user_id = await get_current_user_id(
            event=callback,
            session=session,
        )
    except UserNotFoundError:
        await edit_callback_message(
            callback,
            text=GENERIC_ERROR_TEXT,
            reply_markup=build_main_menu_keyboard(),
            answer_callback=answer_callback,
        )
        return

    screen = await build_alerts_page_screen(
        session=session,
        user_id=user_id,
        request=request,
    )

    await _render_screen(
        callback=callback,
        screen=screen,
        answer_callback=answer_callback,
    )


def _resolve_alert_condition(callback_data: str | None) -> AlertCondition:
    """Convert condition callback data into an AlertCondition enum."""
    if callback_data == CB_ALERTS_CONDITION_ABOVE:
        return AlertCondition.ABOVE

    return AlertCondition.BELOW


def _resolve_selected_alert_id(payload: AlertActionPayload) -> int | None:
    """Return the next selected alert id for inline details toggle."""
    if payload.alert_id is None:
        return None

    if payload.selected_alert_id == payload.alert_id:
        return None

    return payload.alert_id


def _parse_alert_action_from_callback(
    *,
    callback: CallbackQuery,
    callback_prefix: str,
) -> AlertActionPayload | None:
    """Parse alert action payload from callback data."""
    if callback.data is None:
        return None

    return parse_alert_action_payload(
        callback.data.removeprefix(callback_prefix),
    )


async def _create_alert_from_state(
    *,
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> Alert:
    """Create a price alert using FSM data and the incoming message text."""
    if message.text is None:
        raise ValidationError

    target_price = parse_alert_price(message.text)
    data = await state.get_data()

    user_id = await get_current_user_id(
        event=message,
        session=session,
    )

    return await create_price_alert(
        session,
        data=AlertCreateData(
            user_id=user_id,
            coin_id=str(data["coin_id"]),
            target_price=target_price,
            condition=AlertCondition(str(data["condition"])),
        ),
    )


async def _clear_state_and_show_generic_error(
    *,
    message: Message,
    state: FSMContext,
    chat_id: object | None = None,
    message_id: object | None = None,
) -> None:
    """Clear FSM state and show a safe generic error."""
    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=chat_id,
        message_id=message_id,
        text=GENERIC_ERROR_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


async def _render_screen(
    *,
    callback: CallbackQuery,
    screen: BotScreen,
    answer_callback: bool = True,
) -> None:
    """Render a prepared bot screen into the callback message."""
    await edit_callback_message(
        callback,
        text=screen.text,
        reply_markup=screen.reply_markup,
        answer_callback=answer_callback,
    )
