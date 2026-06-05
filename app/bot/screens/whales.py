"""Screen builders for whale events browser."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.whales import build_whale_events_page_keyboard
from app.bot.screens.common import BotScreen
from app.bot.text_builders.whales import build_whale_events_page_text
from app.core.constants import (
    BOT_WHALE_EVENTS_PAGE_SIZE,
    MAX_BOT_WHALE_EVENTS_VISIBLE_PAGES,
)
from app.services.whales_service import get_latest_whale_events_page


@dataclass(frozen=True)
class WhaleEventsPageRequest:
    """Input data required to build the whale events screen."""

    page_number: int


async def build_whale_events_page_screen(
    *,
    session: AsyncSession,
    request: WhaleEventsPageRequest,
) -> BotScreen:
    """Build a paginated whale events screen."""
    safe_page_number = min(
        max(request.page_number, 0),
        MAX_BOT_WHALE_EVENTS_VISIBLE_PAGES - 1,
    )
    offset = safe_page_number * BOT_WHALE_EVENTS_PAGE_SIZE

    page = await get_latest_whale_events_page(
        session,
        limit=BOT_WHALE_EVENTS_PAGE_SIZE,
        offset=offset,
    )

    if not page.items and safe_page_number > 0:
        return await build_whale_events_page_screen(
            session=session,
            request=WhaleEventsPageRequest(
                page_number=min(
                    max(page.total_pages - 1, 0),
                    MAX_BOT_WHALE_EVENTS_VISIBLE_PAGES - 1,
                ),
            ),
        )

    visible_total_pages = min(page.total_pages, MAX_BOT_WHALE_EVENTS_VISIBLE_PAGES)
    visible_has_more = page.has_more and safe_page_number < visible_total_pages - 1

    return BotScreen(
        text=build_whale_events_page_text(page.items),
        reply_markup=build_whale_events_page_keyboard(
            page_number=safe_page_number,
            total_pages=visible_total_pages,
            has_more=visible_has_more,
        ),
    )
