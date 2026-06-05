"""Screen builders for the price alert browser.

This module owns presentation-level logic for the My alerts screen:
pagination, filter normalization, selected alert lookup, text building and
keyboard building.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import build_alerts_page_keyboard
from app.bot.screens.common import BotScreen
from app.bot.text_builders import (
    build_alerts_page_text,
    get_alert_status_filter,
    normalize_alert_filter,
)
from app.core.constants import BOT_ALERTS_PAGE_SIZE, MAX_BOT_ALERTS_VISIBLE_PAGES
from app.database.models.alert import Alert
from app.services.alerts_service import AlertHistoryPage, get_user_alerts_page


@dataclass(frozen=True)
class AlertPageRequest:
    """Input data required to build the My alerts screen."""

    filter_value: str
    page_number: int
    selected_alert_id: int | None = None
    fallback_to_previous_page: bool = False


async def build_alerts_page_screen(
    *,
    session: AsyncSession,
    user_id: int,
    request: AlertPageRequest,
) -> BotScreen:
    """Build a complete paginated My alerts screen."""
    safe_filter = normalize_alert_filter(request.filter_value)
    safe_page_number = min(
        max(request.page_number, 0),
        MAX_BOT_ALERTS_VISIBLE_PAGES - 1,
    )

    page = await _load_alerts_page(
        session=session,
        user_id=user_id,
        filter_value=safe_filter,
        page_number=safe_page_number,
    )

    if not page.items and request.fallback_to_previous_page and safe_page_number > 0:
        return await build_alerts_page_screen(
            session=session,
            user_id=user_id,
            request=AlertPageRequest(
                filter_value=safe_filter,
                page_number=safe_page_number - 1,
            ),
        )

    if not page.items and safe_page_number > 0:
        return await build_alerts_page_screen(
            session=session,
            user_id=user_id,
            request=AlertPageRequest(
                filter_value=safe_filter,
                page_number=min(
                    max(page.total_pages - 1, 0),
                    MAX_BOT_ALERTS_VISIBLE_PAGES - 1,
                ),
            ),
        )

    visible_total_pages = min(page.total_pages, MAX_BOT_ALERTS_VISIBLE_PAGES)
    visible_has_more = page.has_more and safe_page_number < visible_total_pages - 1

    selected_alert = _find_selected_alert(
        alerts=page.items,
        selected_alert_id=request.selected_alert_id,
    )

    return BotScreen(
        text=build_alerts_page_text(
            alerts=page.items,
            selected_alert=selected_alert,
        ),
        reply_markup=build_alerts_page_keyboard(
            alerts=page.items,
            filter_value=safe_filter,
            page_number=safe_page_number,
            total_pages=visible_total_pages,
            has_more=visible_has_more,
            selected_alert_id=selected_alert.id if selected_alert else None,
        ),
    )


async def _load_alerts_page(
    *,
    session: AsyncSession,
    user_id: int,
    filter_value: str,
    page_number: int,
) -> AlertHistoryPage:
    """Load one alert page from the domain service."""
    offset = page_number * BOT_ALERTS_PAGE_SIZE

    return await get_user_alerts_page(
        session,
        user_id=user_id,
        status_filter=get_alert_status_filter(filter_value),
        limit=BOT_ALERTS_PAGE_SIZE,
        offset=offset,
    )


def _find_selected_alert(
    *,
    alerts: list[Alert],
    selected_alert_id: int | None,
) -> Alert | None:
    """Return selected alert only when it exists on the current page."""
    if selected_alert_id is None:
        return None

    for alert in alerts:
        if alert.id == selected_alert_id:
            return alert

    return None
