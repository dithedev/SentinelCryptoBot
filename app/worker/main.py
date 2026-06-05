"""Entrypoint for background worker processes."""

import asyncio
import contextlib
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import get_settings
from app.core.log_messages import (
    WORKER_STARTING_LOG,
    WORKER_STOP_REQUESTED_LOG,
    WORKER_STOPPED_LOG,
)
from app.core.logger import configure_logging
from app.database.session import async_session_maker
from app.worker.price_alert_worker import PriceAlertWorker
from app.worker.telegram_rate_limiter import TelegramSendRateLimiter
from app.worker.whale_alert_worker import WhaleAlertWorker

logger = logging.getLogger(__name__)


async def main() -> None:
    """Start all background workers."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(WORKER_STARTING_LOG)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    telegram_rate_limiter = TelegramSendRateLimiter(
        messages_per_second=settings.telegram_send_rate_per_second,
    )

    price_alert_worker = PriceAlertWorker(
        bot=bot,
        session_maker=async_session_maker,
        settings=settings,
        telegram_rate_limiter=telegram_rate_limiter,
    )
    whale_alert_worker = WhaleAlertWorker(
        bot=bot,
        session_maker=async_session_maker,
        settings=settings,
        telegram_rate_limiter=telegram_rate_limiter,
    )

    try:
        await asyncio.gather(
            price_alert_worker.run_forever(),
            whale_alert_worker.run_forever(),
        )
    except asyncio.CancelledError:
        logger.info(WORKER_STOP_REQUESTED_LOG)
        price_alert_worker.stop()
        whale_alert_worker.stop()
    finally:
        await bot.session.close()
        logger.info(WORKER_STOPPED_LOG)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
