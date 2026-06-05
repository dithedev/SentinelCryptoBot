"""Telegram bot entrypoint."""

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.middlewares import BotUserThrottleMiddleware, DbSessionMiddleware
from app.bot.routers import setup_routers
from app.core.config import get_settings
from app.core.log_messages import (
    BOT_STARTING_LOG,
    BOT_STOP_REQUESTED_LOG,
    BOT_STOPPED_LOG,
)
from app.core.logger import configure_logging
from app.core.rate_limit import MinIntervalRateLimiter
from app.database.session import async_session_maker

logger = logging.getLogger(__name__)


async def main() -> None:
    """Start Telegram bot polling."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(BOT_STARTING_LOG)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()

    bot_user_limiter = MinIntervalRateLimiter(
        min_interval_seconds=settings.bot_user_min_interval_seconds,
    )
    bot_user_throttle = BotUserThrottleMiddleware(limiter=bot_user_limiter)

    root_router = setup_routers()
    root_router.callback_query.outer_middleware(bot_user_throttle)
    root_router.message.outer_middleware(bot_user_throttle)

    dispatcher.update.middleware(DbSessionMiddleware(async_session_maker))
    dispatcher.include_router(root_router)

    try:
        await dispatcher.start_polling(bot)
    except asyncio.CancelledError:
        logger.info(BOT_STOP_REQUESTED_LOG)
    finally:
        await bot.session.close()
        logger.info(BOT_STOPPED_LOG)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
