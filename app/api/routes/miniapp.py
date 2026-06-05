"""Telegram Mini App API routes.

These endpoints are protected with Telegram WebApp initData validation. The
frontend never sends telegram_id directly. The backend derives the current user
from the signed Telegram payload.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_miniapp_user, get_db_session
from app.api.presenters import (
    to_alert_response,
    to_alert_response_list,
    to_token_risk_check_response,
    to_whale_event_response_list,
    to_whale_settings_response,
)
from app.api.schemas import (
    AlertActionResponse,
    AlertResponse,
    MiniAppAlertCreateRequest,
    MiniAppConfigResponse,
    MiniAppUserResponse,
    PaginatedAlertsResponse,
    PaginatedWhaleEventsResponse,
    SupportedCoinResponse,
    TokenRiskCheckRequest,
    TokenRiskCheckResponse,
    WhaleSettingsResponse,
    WhaleSettingsUpdateRequest,
)
from app.api.texts import ALERT_DISABLED_MESSAGE
from app.core.constants import (
    DEFAULT_ALERT_HISTORY_LIMIT,
    DEFAULT_WHALE_EVENTS_LIMIT,
    MAX_ALERT_HISTORY_LIMIT,
    MAX_WHALE_EVENTS_LIMIT,
    SUPPORTED_CHAINS,
    SUPPORTED_COINS,
)
from app.database.models.alert import AlertCondition
from app.database.models.user import User
from app.services.alerts_service import (
    AlertCreateData,
    create_price_alert,
    disable_user_alert,
    get_active_user_alerts,
    get_user_alert_history,
    get_user_alert_history_page,
)
from app.services.token_risk_service import TokenRiskCheckData, check_token_risk
from app.services.whales_service import (
    WhaleSettingsUpdateData,
    get_latest_whale_events_page,
    get_or_create_user_whale_settings,
    update_user_whale_settings,
)

router = APIRouter(prefix="/miniapp-api", tags=["miniapp"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentMiniAppUser = Annotated[User, Depends(get_current_miniapp_user)]

AlertHistoryLimitQuery = Annotated[
    int,
    Query(ge=1, le=MAX_ALERT_HISTORY_LIMIT),
]
AlertHistoryOffsetQuery = Annotated[int, Query(ge=0)]

WhaleEventsLimitQuery = Annotated[
    int,
    Query(ge=1, le=MAX_WHALE_EVENTS_LIMIT),
]
WhaleEventsOffsetQuery = Annotated[int, Query(ge=0)]


@router.get("/me", response_model=MiniAppUserResponse)
async def get_me(
    user: CurrentMiniAppUser,
) -> MiniAppUserResponse:
    """Return the authenticated Telegram Mini App user."""
    return MiniAppUserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.get("/config", response_model=MiniAppConfigResponse)
async def get_miniapp_config() -> MiniAppConfigResponse:
    """Return static config required by the Mini App UI."""
    return MiniAppConfigResponse(
        supported_coins=[
            SupportedCoinResponse(
                coin_id=coin.coin_id,
                symbol=coin.symbol,
                name=coin.name,
            )
            for coin in SUPPORTED_COINS
        ],
        alert_conditions=[
            AlertCondition.ABOVE,
            AlertCondition.BELOW,
        ],
        supported_chains=sorted(SUPPORTED_CHAINS),
    )


@router.get("/alerts", response_model=list[AlertResponse])
async def list_my_alerts(
    session: DbSession,
    user: CurrentMiniAppUser,
    include_inactive: bool = False,
) -> list[AlertResponse]:
    """Return alerts owned by the authenticated Mini App user.

    include_inactive is kept for backward compatibility. The Mini App frontend
    should use /alerts/history for paginated history.
    """
    if include_inactive:
        alerts = await get_user_alert_history(session, user_id=user.id)
    else:
        alerts = await get_active_user_alerts(session, user_id=user.id)

    return to_alert_response_list(alerts)


@router.get("/alerts/history", response_model=PaginatedAlertsResponse)
async def list_my_alert_history(
    session: DbSession,
    user: CurrentMiniAppUser,
    limit: AlertHistoryLimitQuery = DEFAULT_ALERT_HISTORY_LIMIT,
    offset: AlertHistoryOffsetQuery = 0,
) -> PaginatedAlertsResponse:
    """Return paginated alert history for the authenticated Mini App user."""
    page = await get_user_alert_history_page(
        session,
        user_id=user.id,
        limit=limit,
        offset=offset,
    )

    return PaginatedAlertsResponse(
        items=to_alert_response_list(page.items),
        limit=page.limit,
        offset=page.offset,
        has_more=page.has_more,
    )


@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_alert(
    payload: MiniAppAlertCreateRequest,
    session: DbSession,
    user: CurrentMiniAppUser,
) -> AlertResponse:
    """Create an alert for the authenticated Mini App user."""
    alert = await create_price_alert(
        session,
        data=AlertCreateData(
            user_id=user.id,
            coin_id=payload.coin_id,
            target_price=payload.target_price,
            condition=payload.condition,
        ),
    )

    return to_alert_response(alert)


@router.patch("/alerts/{alert_id}/disable", response_model=AlertActionResponse)
async def disable_my_alert(
    alert_id: int,
    session: DbSession,
    user: CurrentMiniAppUser,
) -> AlertActionResponse:
    """Disable one active alert owned by the authenticated Mini App user.

    Disabled alerts stay in history and are not checked by the worker anymore.
    """
    await disable_user_alert(
        session,
        user_id=user.id,
        alert_id=alert_id,
    )

    return AlertActionResponse(message=ALERT_DISABLED_MESSAGE)


@router.post("/risk-check", response_model=TokenRiskCheckResponse)
async def check_token_risk_from_miniapp(
    payload: TokenRiskCheckRequest,
    session: DbSession,
    user: CurrentMiniAppUser,
) -> TokenRiskCheckResponse:
    """Check token risk for the authenticated Mini App user."""
    token_check = await check_token_risk(
        session,
        data=TokenRiskCheckData(
            user_id=user.id,
            chain=payload.chain,
            contract_address=payload.contract_address,
        ),
    )

    return to_token_risk_check_response(token_check)


@router.get("/whales/settings", response_model=WhaleSettingsResponse)
async def get_my_whale_settings(
    session: DbSession,
    user: CurrentMiniAppUser,
) -> WhaleSettingsResponse:
    """Return whale alert settings for the authenticated Mini App user."""
    settings = await get_or_create_user_whale_settings(
        session,
        user_id=user.id,
    )

    return to_whale_settings_response(settings)


@router.patch("/whales/settings", response_model=WhaleSettingsResponse)
async def update_my_whale_settings(
    payload: WhaleSettingsUpdateRequest,
    session: DbSession,
    user: CurrentMiniAppUser,
) -> WhaleSettingsResponse:
    """Update whale alert settings for the authenticated Mini App user."""
    settings = await update_user_whale_settings(
        session,
        data=WhaleSettingsUpdateData(
            user_id=user.id,
            is_enabled=payload.is_enabled,
            min_usd_value=payload.min_usd_value,
        ),
    )

    return to_whale_settings_response(settings)


@router.get("/whales/events", response_model=PaginatedWhaleEventsResponse)
async def list_whale_events(
    session: DbSession,
    user: CurrentMiniAppUser,
    limit: WhaleEventsLimitQuery = DEFAULT_WHALE_EVENTS_LIMIT,
    offset: WhaleEventsOffsetQuery = 0,
) -> PaginatedWhaleEventsResponse:
    """Return latest whale events for the authenticated Mini App user."""
    _ = user
    page = await get_latest_whale_events_page(
        session,
        limit=limit,
        offset=offset,
    )

    return PaginatedWhaleEventsResponse(
        items=to_whale_event_response_list(page.items),
        limit=page.limit,
        offset=page.offset,
        has_more=page.has_more,
    )
