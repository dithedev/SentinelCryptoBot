"""Background worker for price alert checking."""

import asyncio
import logging
from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, TelegramDeliveryBlockedError
from app.core.log_messages import (
    ALERT_NOTIFICATION_FAILED_LOG_TEMPLATE,
    ALERT_TRIGGERED_LOG_TEMPLATE,
    WORKER_CYCLE_FAILED_LOG,
    WORKER_CYCLE_FINISHED_LOG,
    WORKER_CYCLE_STARTED_LOG,
    WORKER_NO_ACTIVE_ALERTS_LOG,
    WORKER_NO_PRICES_LOG,
)
from app.database.models.alert import Alert
from app.database.session import AsyncSessionFactory
from app.integrations.coingecko import CoinGeckoClient
from app.repositories.alerts import try_claim_alert_trigger
from app.repositories.users import deactivate_user
from app.services.alerts_service import (
    get_all_active_alerts,
    should_trigger_alert,
)
from app.services.notifications_service import send_price_alert_notification
from app.services.prices_service import get_price_map_for_alerts
from app.worker.constants import WORKER_SLEEP_ON_ERROR_SECONDS
from app.worker.market_price_cache import MarketPriceCache
from app.worker.telegram_rate_limiter import TelegramSendRateLimiter

logger = logging.getLogger(__name__)


class PriceAlertWorker:
    """Worker that checks active alerts and sends Telegram notifications."""

    def __init__(
        self,
        *,
        bot: Bot,
        session_maker: AsyncSessionFactory,
        settings: Settings,
        price_provider: CoinGeckoClient | None = None,
        price_cache: MarketPriceCache | None = None,
        telegram_rate_limiter: TelegramSendRateLimiter | None = None,
    ) -> None:
        self._bot = bot
        self._session_maker = session_maker
        self._settings = settings
        self._price_provider = price_provider or CoinGeckoClient()
        self._price_cache = price_cache or MarketPriceCache()
        self._telegram_rate_limiter = telegram_rate_limiter or TelegramSendRateLimiter()
        self._is_stopping = False

    async def run_forever(self) -> None:
        """Run the worker until stop is requested or task is cancelled.

        Only expected operational errors are swallowed here. Unexpected bugs
        should still crash the worker during development instead of being hidden.
        """
        while not self._is_stopping:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except (AppError, SQLAlchemyError):
                logger.exception(WORKER_CYCLE_FAILED_LOG)
                await asyncio.sleep(WORKER_SLEEP_ON_ERROR_SECONDS)

            await asyncio.sleep(self._settings.price_check_interval_seconds)

    def stop(self) -> None:
        """Request graceful worker shutdown."""
        self._is_stopping = True

    async def run_once(self) -> None:
        """Run one alert-checking cycle."""
        logger.info(WORKER_CYCLE_STARTED_LOG)

        async with self._session_maker() as session:
            alerts = await get_all_active_alerts(session)

            if not alerts:
                logger.info(WORKER_NO_ACTIVE_ALERTS_LOG)
                return

            coin_ids = {alert.coin_id for alert in alerts}
            prices = await self._get_prices(coin_ids)

            if not prices:
                logger.warning(WORKER_NO_PRICES_LOG)
                return

            await self._process_alerts(
                session=session,
                alerts=alerts,
                prices=prices,
            )

            await session.commit()

        logger.info(WORKER_CYCLE_FINISHED_LOG)

    async def _get_prices(
        self,
        coin_ids: set[str],
    ) -> dict[str, Decimal]:
        """Return prices from cache or provider."""
        cached_prices = self._price_cache.get_many(coin_ids)

        if cached_prices is not None:
            return cached_prices

        prices = await get_price_map_for_alerts(
            self._price_provider,
            coin_ids=coin_ids,
        )

        self._price_cache.set_many(prices)

        return prices

    async def _process_alerts(
        self,
        *,
        session: AsyncSession,
        alerts: list[Alert],
        prices: dict[str, Decimal],
    ) -> None:
        """Check all loaded alerts against the current price map."""
        for alert in alerts:
            current_price = prices.get(alert.coin_id)

            if current_price is None:
                continue

            if not should_trigger_alert(
                alert=alert,
                current_price=current_price,
            ):
                continue

            await self._claim_and_notify(
                session=session,
                alert=alert,
                current_price=current_price,
            )

    async def _claim_and_notify(
        self,
        *,
        session: AsyncSession,
        alert: Alert,
        current_price: Decimal,
    ) -> None:
        """Atomically claim one alert and send its notification."""
        claimed_alert = await try_claim_alert_trigger(
            session,
            alert_id=alert.id,
        )

        if claimed_alert is None:
            return

        if alert.user is None:
            return

        try:
            await self._telegram_rate_limiter.acquire()
            await send_price_alert_notification(
                self._bot,
                telegram_id=alert.user.telegram_id,
                symbol=alert.symbol,
                condition=alert.condition,
                target_price=alert.target_price,
                current_price=current_price,
            )
        except TelegramDeliveryBlockedError:
            await deactivate_user(
                session,
                telegram_id=alert.user.telegram_id,
            )
            logger.exception(
                ALERT_NOTIFICATION_FAILED_LOG_TEMPLATE.format(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                ),
            )
            return
        except TelegramAPIError:
            logger.exception(
                ALERT_NOTIFICATION_FAILED_LOG_TEMPLATE.format(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                ),
            )
            return

        logger.info(
            ALERT_TRIGGERED_LOG_TEMPLATE.format(
                alert_id=alert.id,
                user_id=alert.user_id,
                symbol=alert.symbol,
            ),
        )
