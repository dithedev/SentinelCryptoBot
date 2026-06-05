"""Inline keyboard builders for price alerts."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.callbacks.alerts import (
    build_alert_delete_callback,
    build_alert_page_callback,
    build_alert_view_callback,
)
from app.bot.constants import (
    CB_ALERTS_BACK_TO_MENU,
    CB_ALERTS_CANCEL,
    CB_ALERTS_COIN_PREFIX,
    CB_ALERTS_CONDITION_ABOVE,
    CB_ALERTS_CONDITION_BELOW,
    CB_ALERTS_CREATE,
    CB_ALERTS_DELETE_PREFIX,
    CB_ALERTS_IGNORE,
    CB_ALERTS_LIST,
    CB_MAIN_MENU,
)
from app.bot.text_builders import (
    ALERT_FILTER_ACTIVE,
    ALERT_FILTER_ALL,
    build_alert_button_title,
)
from app.bot.texts.buttons import (
    ALERTS_ABOVE_BUTTON,
    ALERTS_BELOW_BUTTON,
    ALERTS_CREATE_BUTTON,
    ALERTS_DELETE_BUTTON,
    ALERTS_FILTER_ACTIVE_BUTTON,
    ALERTS_FILTER_HISTORY_BUTTON,
    ALERTS_FILTER_SELECTED_EMOJI,
    ALERTS_LIST_BUTTON,
    ALERTS_NEXT_PAGE_BUTTON,
    ALERTS_PAGE_BUTTON_TEMPLATE,
    ALERTS_PREVIOUS_PAGE_BUTTON,
    BACK_TO_ALERTS_BUTTON,
    BACK_TO_MAIN_MENU_BUTTON,
    CANCEL_BUTTON,
)
from app.core.constants import (
    SUPPORTED_COINS,
)
from app.database.models.alert import Alert, AlertStatus

ALERT_COIN_COLUMNS = 3


def build_alerts_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the top-level alerts menu.

    Creation and list browsing are intentionally separate actions:
    - Create alert starts the FSM creation flow.
    - My alerts opens the paginated alert browser with History selected by default.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ALERTS_CREATE_BUTTON,
                    callback_data=CB_ALERTS_CREATE,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ALERTS_LIST_BUTTON,
                    callback_data=CB_ALERTS_LIST,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BACK_TO_MAIN_MENU_BUTTON,
                    callback_data=CB_MAIN_MENU,
                ),
            ],
        ],
    )


def build_alert_coin_keyboard() -> InlineKeyboardMarkup:
    """Build a compact coin picker keyboard.

    Coin buttons are rendered in rows of three. If the last row is incomplete,
    it is padded with a blank no-op button so the visual grid stays aligned.
    """
    coin_buttons = [
        InlineKeyboardButton(
            text=coin.symbol,
            callback_data=f"{CB_ALERTS_COIN_PREFIX}{coin.coin_id}",
        )
        for coin in SUPPORTED_COINS
    ]

    rows = _chunk_buttons_with_blank_padding(
        buttons=coin_buttons,
        columns=ALERT_COIN_COLUMNS,
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=CANCEL_BUTTON,
                callback_data=CB_ALERTS_CANCEL,
            ),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_alert_condition_keyboard() -> InlineKeyboardMarkup:
    """Build a keyboard for alert condition selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ALERTS_ABOVE_BUTTON,
                    callback_data=CB_ALERTS_CONDITION_ABOVE,
                ),
                InlineKeyboardButton(
                    text=ALERTS_BELOW_BUTTON,
                    callback_data=CB_ALERTS_CONDITION_BELOW,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=CANCEL_BUTTON,
                    callback_data=CB_ALERTS_CANCEL,
                ),
            ],
        ],
    )


def build_alert_price_input_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard shown while waiting for target price input."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=CANCEL_BUTTON,
                    callback_data=CB_ALERTS_CANCEL,
                ),
            ],
        ],
    )


def build_alerts_page_keyboard(
    *,
    alerts: list[Alert],
    filter_value: str,
    page_number: int,
    total_pages: int,
    has_more: bool,
    selected_alert_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Build the paginated My alerts keyboard.

    Layout:
    1. Status filters.
    2. Up to 10 alert rows.
    3. Pagination row.
    4. Back button to the top-level alerts menu.

    Only active selected alerts receive a Delete button. Triggered or disabled
    selected alerts only show details in the message text, and the next click
    hides those details.
    """
    safe_total_pages = max(total_pages, 1)
    safe_page_number = min(max(page_number, 0), safe_total_pages - 1)

    rows: list[list[InlineKeyboardButton]] = [
        _build_filters_row(current_filter=filter_value),
    ]

    for alert in alerts:
        rows.append(
            _build_alert_row(
                alert=alert,
                filter_value=filter_value,
                page_number=safe_page_number,
                selected_alert_id=selected_alert_id,
            ),
        )

    rows.append(
        _build_pagination_row(
            filter_value=filter_value,
            page_number=safe_page_number,
            total_pages=safe_total_pages,
            has_more=has_more,
        ),
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=BACK_TO_ALERTS_BUTTON,
                callback_data=CB_ALERTS_BACK_TO_MENU,
            ),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_alert_details_keyboard(
    *,
    alert: Alert,
    filter_value: str,
    page_number: int,
) -> InlineKeyboardMarkup:
    """Build a legacy detailed alert keyboard.

    New My alerts flow shows details inline on the list screen. This function is
    kept for import compatibility and older callback payloads.
    """
    rows: list[list[InlineKeyboardButton]] = []

    if alert.status == AlertStatus.ACTIVE:
        rows.append(
            [
                InlineKeyboardButton(
                    text=ALERTS_DELETE_BUTTON,
                    callback_data=build_alert_delete_callback(
                        alert_id=alert.id,
                        filter_value=filter_value,
                        page_number=page_number,
                    ),
                ),
            ],
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=BACK_TO_ALERTS_BUTTON,
                callback_data=build_alert_page_callback(
                    filter_value=filter_value,
                    page_number=page_number,
                ),
            ),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_user_alerts_keyboard(
    alerts: list[Alert],
) -> InlineKeyboardMarkup:
    """Build a legacy keyboard with user alerts.

    Kept for import compatibility. New bot flow uses build_alerts_page_keyboard.
    """
    return build_alerts_page_keyboard(
        alerts=alerts,
        filter_value=ALERT_FILTER_ALL,
        page_number=0,
        total_pages=1,
        has_more=False,
    )


def build_alert_delete_confirmation_keyboard(
    alert: Alert,
) -> InlineKeyboardMarkup:
    """Build a legacy keyboard used to delete one alert."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ALERTS_DELETE_BUTTON,
                    callback_data=f"{CB_ALERTS_DELETE_PREFIX}{alert.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=BACK_TO_ALERTS_BUTTON,
                    callback_data=CB_ALERTS_BACK_TO_MENU,
                ),
            ],
        ],
    )


def _chunk_buttons_with_blank_padding(
    *,
    buttons: list[InlineKeyboardButton],
    columns: int,
) -> list[list[InlineKeyboardButton]]:
    """Split buttons into fixed-width rows and pad the last row.

    Telegram buttons cannot have an empty text value, so the blank button uses a
    single space and a no-op callback.
    """
    rows: list[list[InlineKeyboardButton]] = []

    for index in range(0, len(buttons), columns):
        row = buttons[index : index + columns]

        while len(row) < columns:
            row.append(
                InlineKeyboardButton(
                    text=" ",
                    callback_data=CB_ALERTS_IGNORE,
                ),
            )

        rows.append(row)

    return rows


def _build_filters_row(
    *,
    current_filter: str,
) -> list[InlineKeyboardButton]:
    """Build the fixed filter row shown above the alert list.

    Required order:
    - Active
    - History
    """
    return [
        _build_filter_button(
            text=ALERTS_FILTER_ACTIVE_BUTTON,
            value=ALERT_FILTER_ACTIVE,
            current_filter=current_filter,
        ),
        _build_filter_button(
            text=ALERTS_FILTER_HISTORY_BUTTON,
            value=ALERT_FILTER_ALL,
            current_filter=current_filter,
        ),
    ]


def _build_alert_row(
    *,
    alert: Alert,
    filter_value: str,
    page_number: int,
    selected_alert_id: int | None,
) -> list[InlineKeyboardButton]:
    """Build one alert row.

    Active selected alerts receive a second Delete button. Non-active selected
    alerts stay as a single button and only affect the message details area.
    """
    alert_button = InlineKeyboardButton(
        text=build_alert_button_title(
            alert,
            show_status_emoji=True,
        ),
        callback_data=build_alert_view_callback(
            alert_id=alert.id,
            filter_value=filter_value,
            page_number=page_number,
            selected_alert_id=selected_alert_id,
        ),
    )

    if alert.id != selected_alert_id:
        return [alert_button]

    if alert.status != AlertStatus.ACTIVE:
        return [alert_button]

    return [
        alert_button,
        InlineKeyboardButton(
            text=ALERTS_DELETE_BUTTON,
            callback_data=build_alert_delete_callback(
                alert_id=alert.id,
                filter_value=filter_value,
                page_number=page_number,
                selected_alert_id=selected_alert_id,
            ),
        ),
    ]


def _build_pagination_row(
    *,
    filter_value: str,
    page_number: int,
    total_pages: int,
    has_more: bool,
) -> list[InlineKeyboardButton]:
    """Build the fixed 3-button pagination row.

    Page navigation clears any selected alert because the selected alert may
    not exist on the next or previous page.
    """
    previous_callback = CB_ALERTS_IGNORE

    if page_number > 0:
        previous_callback = build_alert_page_callback(
            filter_value=filter_value,
            page_number=page_number - 1,
        )

    next_callback = CB_ALERTS_IGNORE

    if has_more and page_number < total_pages - 1:
        next_callback = build_alert_page_callback(
            filter_value=filter_value,
            page_number=page_number + 1,
        )

    return [
        InlineKeyboardButton(
            text=ALERTS_PREVIOUS_PAGE_BUTTON,
            callback_data=previous_callback,
        ),
        InlineKeyboardButton(
            text=ALERTS_PAGE_BUTTON_TEMPLATE.format(
                page=page_number + 1,
                total_pages=total_pages,
            ),
            callback_data=CB_ALERTS_IGNORE,
        ),
        InlineKeyboardButton(
            text=ALERTS_NEXT_PAGE_BUTTON,
            callback_data=next_callback,
        ),
    ]


def _build_filter_button(
    *,
    text: str,
    value: str,
    current_filter: str,
) -> InlineKeyboardButton:
    """Build one filter button.

    The active filter is a no-op button to avoid unnecessary message edits.
    Inactive filters open page 0 of their own filtered list.
    """
    is_current_filter = value == current_filter
    button_text = (
        f"{ALERTS_FILTER_SELECTED_EMOJI} {text}" if is_current_filter else text
    )

    callback_data = CB_ALERTS_IGNORE

    if not is_current_filter:
        callback_data = build_alert_page_callback(
            filter_value=value,
            page_number=0,
        )

    return InlineKeyboardButton(
        text=button_text,
        callback_data=callback_data,
    )
