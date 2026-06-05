"""Bot-level whale alert use cases.

Telegram-specific flow logic lives here. Domain rules stay in
app.services.whales_service.
"""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks.whales import parse_whale_events_page_payload
from app.bot.constants import CB_WHALES_EVENTS_PAGE_PREFIX
from app.bot.keyboards import (
    build_main_menu_keyboard,
    build_whale_threshold_input_keyboard,
    build_whales_menu_keyboard,
)
from app.bot.screens.whales import (
    WhaleEventsPageRequest,
    build_whale_events_page_screen,
)
from app.bot.states import WhaleSettingsStates
from app.bot.text_builders.whales import build_whales_menu_text
from app.bot.texts import (
    GENERIC_ERROR_TEXT,
    VALIDATION_ERROR_TEMPLATE,
    WHALES_ALERTS_DISABLED_TEXT,
    WHALES_ALERTS_ENABLED_TEXT,
    WHALES_ENTER_THRESHOLD_TEXT,
    WHALES_SETTINGS_CANCELLED_TEXT,
    WHALES_THRESHOLD_LOADING_TEXT,
    WHALES_THRESHOLD_UPDATED_TEXT,
)
from app.bot.utils import edit_callback_message, safe_callback_answer
from app.bot.utils.fsm_screens import (
    delete_user_message,
    edit_fsm_screen_or_answer,
    remember_fsm_screen,
)
from app.core.exceptions import UserNotFoundError, ValidationError
from app.services.whales_service import (
    UserWhaleSettings,
    get_or_create_user_whale_settings_by_telegram_id,
    update_loaded_user_whale_settings,
)
from app.utils.money import parse_whale_min_usd_value

WHALE_THRESHOLD_SCREEN_CHAT_ID_KEY = "whale_threshold_screen_chat_id"
WHALE_THRESHOLD_SCREEN_MESSAGE_ID_KEY = "whale_threshold_screen_message_id"


async def show_whales_menu_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Show whale alert settings for the current user."""
    try:
        user_settings = await _get_current_user_whale_settings(
            event=callback,
            session=session,
        )
    except UserNotFoundError:
        await edit_callback_message(
            callback,
            text=GENERIC_ERROR_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await edit_callback_message(
        callback,
        text=build_whales_menu_text(user_settings.settings),
        reply_markup=build_whales_menu_keyboard(user_settings.settings),
    )


async def toggle_whale_alerts_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Enable or disable whale alerts for the current user."""
    try:
        user_settings = await _get_current_user_whale_settings(
            event=callback,
            session=session,
        )
    except UserNotFoundError:
        await edit_callback_message(
            callback,
            text=GENERIC_ERROR_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
        return

    updated_settings = await update_loaded_user_whale_settings(
        session,
        settings=user_settings.settings,
        is_enabled=not user_settings.settings.is_enabled,
    )

    status_message = (
        WHALES_ALERTS_ENABLED_TEXT
        if updated_settings.is_enabled
        else WHALES_ALERTS_DISABLED_TEXT
    )

    await safe_callback_answer(callback, status_message, show_alert=True)

    await edit_callback_message(
        callback,
        text=build_whales_menu_text(updated_settings),
        reply_markup=build_whales_menu_keyboard(updated_settings),
        answer_callback=False,
    )


async def start_whale_threshold_change_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start threshold update flow."""
    await state.set_state(WhaleSettingsStates.entering_threshold)

    await edit_callback_message(
        callback,
        text=WHALES_ENTER_THRESHOLD_TEXT,
        reply_markup=build_whale_threshold_input_keyboard(),
    )
    await remember_fsm_screen(
        callback=callback,
        state=state,
        chat_id_key=WHALE_THRESHOLD_SCREEN_CHAT_ID_KEY,
        message_id_key=WHALE_THRESHOLD_SCREEN_MESSAGE_ID_KEY,
    )


async def handle_whale_threshold_input_flow(
    *,
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update whale threshold from user message."""
    if message.text is None:
        return

    data = await state.get_data()
    screen_chat_id = data.get(WHALE_THRESHOLD_SCREEN_CHAT_ID_KEY)
    screen_message_id = data.get(WHALE_THRESHOLD_SCREEN_MESSAGE_ID_KEY)

    await delete_user_message(message)

    try:
        min_usd_value = parse_whale_min_usd_value(message.text)
    except ValidationError as exc:
        await edit_fsm_screen_or_answer(
            message=message,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=VALIDATION_ERROR_TEMPLATE.format(message=str(exc)),
            reply_markup=build_whale_threshold_input_keyboard(),
        )
        return

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=WHALES_THRESHOLD_LOADING_TEXT,
        reply_markup=None,
    )

    try:
        user_settings = await _get_current_user_whale_settings(
            event=message,
            session=session,
        )
        settings = await update_loaded_user_whale_settings(
            session,
            settings=user_settings.settings,
            min_usd_value=min_usd_value,
        )
    except UserNotFoundError:
        await state.clear()
        await edit_fsm_screen_or_answer(
            message=message,
            chat_id=screen_chat_id,
            message_id=screen_message_id,
            text=GENERIC_ERROR_TEXT,
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await state.clear()

    await edit_fsm_screen_or_answer(
        message=message,
        chat_id=screen_chat_id,
        message_id=screen_message_id,
        text=f"{WHALES_THRESHOLD_UPDATED_TEXT}\n\n{build_whales_menu_text(settings)}",
        reply_markup=build_whales_menu_keyboard(settings),
    )


async def _get_current_user_whale_settings(
    *,
    event: CallbackQuery | Message,
    session: AsyncSession,
) -> UserWhaleSettings:
    """Return the current Telegram user's whale settings."""
    from_user = event.from_user

    if from_user is None:
        raise UserNotFoundError

    return await get_or_create_user_whale_settings_by_telegram_id(
        session,
        telegram_id=from_user.id,
    )


async def cancel_whale_settings_flow(
    *,
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Cancel whale settings update and return to whale menu."""
    await state.clear()
    await safe_callback_answer(
        callback,
        WHALES_SETTINGS_CANCELLED_TEXT,
        show_alert=True,
    )
    await show_whales_menu_flow(
        callback=callback,
        session=session,
    )


async def show_whale_events_page_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
    page_number: int = 0,
) -> None:
    """Show one paginated page of whale events."""
    screen = await build_whale_events_page_screen(
        session=session,
        request=WhaleEventsPageRequest(page_number=page_number),
    )

    await edit_callback_message(
        callback,
        text=screen.text,
        reply_markup=screen.reply_markup,
    )


async def show_whale_events_from_callback_flow(
    *,
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Open whale events page from callback payload."""
    if callback.data is None:
        await safe_callback_answer(callback)
        return

    payload = parse_whale_events_page_payload(
        callback.data.removeprefix(CB_WHALES_EVENTS_PAGE_PREFIX),
    )

    await show_whale_events_page_flow(
        callback=callback,
        session=session,
        page_number=payload.page_number,
    )


async def ignore_whales_callback_flow(
    *,
    callback: CallbackQuery,
) -> None:
    """Answer disabled or no-op whale callbacks."""
    await safe_callback_answer(callback)
