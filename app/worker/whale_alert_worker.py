"""Background worker for whale event alerts."""

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.constants import MAX_WHALE_NOTIFICATION_ATTEMPTS
from app.core.exceptions import AppError, TelegramDeliveryBlockedError
from app.core.log_messages import (
    WHALE_EVENT_CREATED_LOG_TEMPLATE,
    WHALE_EVENT_DUPLICATE_LOG_TEMPLATE,
    WHALE_NOTIFICATION_FAILED_LOG_TEMPLATE,
    WHALE_NOTIFICATION_SENT_LOG_TEMPLATE,
    WHALE_WORKER_CYCLE_FAILED_LOG,
    WHALE_WORKER_CYCLE_FINISHED_LOG,
    WHALE_WORKER_CYCLE_STARTED_LOG,
    WHALE_WORKER_NO_EVENTS_LOG,
)
from app.database.models.whale import (
    WhaleAlertSettings,
    WhaleEvent,
    WhaleNotificationDeliveryStatus,
)
from app.database.session import AsyncSessionFactory
from app.integrations.whales import (
    WhaleEventProvider,
    WhaleProviderEvent,
    build_whale_event_provider,
)
from app.repositories.users import deactivate_user
from app.repositories.whale_notification_deliveries import (
    get_or_create_whale_notification_delivery,
    mark_whale_notification_delivery_failed,
    mark_whale_notification_delivery_sent,
)
from app.services.notifications_service import send_whale_alert_notification
from app.services.whales_service import (
    WhaleEventCreateData,
    create_whale_event_if_new,
    get_matching_whale_settings,
    should_notify_user_about_whale_event,
)
from app.worker.constants import WORKER_SLEEP_ON_ERROR_SECONDS
from app.worker.telegram_rate_limiter import TelegramSendRateLimiter

logger = logging.getLogger(__name__)


class WhaleAlertWorker:
    """Worker that stores whale events and sends matching notifications."""

    def __init__(
        self,
        *,
        bot: Bot,
        session_maker: AsyncSessionFactory,
        settings: Settings,
        provider: WhaleEventProvider | None = None,
        telegram_rate_limiter: TelegramSendRateLimiter | None = None,
    ) -> None:
        self._bot = bot
        self._session_maker = session_maker
        self._settings = settings
        self._provider = provider or build_whale_event_provider(settings)
        self._telegram_rate_limiter = telegram_rate_limiter or TelegramSendRateLimiter()
        self._is_stopping = False

    async def run_forever(self) -> None:
        """Run the worker until stop is requested or task is cancelled."""
        while not self._is_stopping:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except (AppError, SQLAlchemyError):
                logger.exception(WHALE_WORKER_CYCLE_FAILED_LOG)
                await asyncio.sleep(WORKER_SLEEP_ON_ERROR_SECONDS)

            await asyncio.sleep(self._settings.whale_check_interval_seconds)

    def stop(self) -> None:
        """Request graceful worker shutdown."""
        self._is_stopping = True

    async def run_once(self) -> None:
        """Run one whale alert checking cycle."""
        logger.info(WHALE_WORKER_CYCLE_STARTED_LOG)

        provider_events = await self._provider.get_latest_events()

        if not provider_events:
            logger.info(WHALE_WORKER_NO_EVENTS_LOG)
            return

        for provider_event in provider_events:
            async with self._session_maker() as session:
                await self._process_provider_event(
                    session=session,
                    provider_event=provider_event,
                )
                await session.commit()

        logger.info(WHALE_WORKER_CYCLE_FINISHED_LOG)

    async def _process_provider_event(
        self,
        *,
        session: AsyncSession,
        provider_event: WhaleProviderEvent,
    ) -> None:
        """Store one provider event and notify matching users."""
        create_result = await create_whale_event_if_new(
            session,
            data=WhaleEventCreateData(
                coin_id=provider_event.coin_id,
                network=provider_event.network,
                transaction_hash=provider_event.transaction_hash,
                amount=provider_event.amount,
                amount_usd=provider_event.amount_usd,
                event_type=provider_event.event_type,
                from_address=provider_event.from_address,
                to_address=provider_event.to_address,
                detected_at=provider_event.detected_at,
                raw_payload=provider_event.raw_payload,
            ),
        )

        if create_result.was_created:
            logger.info(
                WHALE_EVENT_CREATED_LOG_TEMPLATE.format(
                    event_id=create_result.event.id,
                    symbol=create_result.event.symbol,
                    amount_usd=create_result.event.amount_usd,
                ),
            )
        else:
            logger.info(
                WHALE_EVENT_DUPLICATE_LOG_TEMPLATE.format(
                    transaction_hash=create_result.event.transaction_hash,
                ),
            )

        await self._notify_matching_users(
            session=session,
            event=create_result.event,
        )

    async def _notify_matching_users(
        self,
        *,
        session: AsyncSession,
        event: WhaleEvent,
    ) -> None:
        """Notify all users whose whale settings match the event."""
        matching_settings = await get_matching_whale_settings(
            session,
            event=event,
        )

        for settings in matching_settings:
            await self._notify_one_user(
                session=session,
                settings=settings,
                event=event,
            )

    async def _notify_one_user(
        self,
        *,
        session: AsyncSession,
        settings: WhaleAlertSettings,
        event: WhaleEvent,
    ) -> None:
        """Send one whale notification if delivery is still pending."""
        if not should_notify_user_about_whale_event(
            settings=settings,
            event=event,
        ):
            return

        if settings.user is None:
            return

        delivery = await get_or_create_whale_notification_delivery(
            session,
            whale_event_id=event.id,
            user_id=settings.user_id,
        )

        if delivery.status == WhaleNotificationDeliveryStatus.SENT:
            return

        if delivery.attempts >= MAX_WHALE_NOTIFICATION_ATTEMPTS:
            return

        try:
            await self._telegram_rate_limiter.acquire()
            await send_whale_alert_notification(
                self._bot,
                telegram_id=settings.user.telegram_id,
                event=event,
            )
        except TelegramDeliveryBlockedError:
            await deactivate_user(
                session,
                telegram_id=settings.user.telegram_id,
            )
            await mark_whale_notification_delivery_failed(
                session,
                delivery=delivery,
                error_message="telegram_blocked",
            )
            logger.exception(
                WHALE_NOTIFICATION_FAILED_LOG_TEMPLATE.format(
                    event_id=event.id,
                    user_id=settings.user_id,
                ),
            )
            return
        except TelegramAPIError as exc:
            await mark_whale_notification_delivery_failed(
                session,
                delivery=delivery,
                error_message=str(exc),
            )
            logger.exception(
                WHALE_NOTIFICATION_FAILED_LOG_TEMPLATE.format(
                    event_id=event.id,
                    user_id=settings.user_id,
                ),
            )
            return

        await mark_whale_notification_delivery_sent(
            session,
            delivery=delivery,
        )

        logger.info(
            WHALE_NOTIFICATION_SENT_LOG_TEMPLATE.format(
                event_id=event.id,
                user_id=settings.user_id,
            ),
        )
