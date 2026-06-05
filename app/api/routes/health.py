"""Health check API routes.

Two health checks are exposed:

- GET /health
  Liveness check. It only confirms that the API process is running.

- GET /health/ready
  Readiness check. It confirms that the API can access critical dependencies,
  currently PostgreSQL.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.schemas import HealthResponse, ReadinessResponse
from app.api.texts import (
    HEALTH_COMPONENT_OK,
    HEALTH_COMPONENT_UNAVAILABLE,
    HEALTH_STATUS_NOT_READY,
    HEALTH_STATUS_OK,
    HEALTH_STATUS_READY,
)
from app.database.health import check_database_health

router = APIRouter(prefix="/health", tags=["health"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a simple liveness status."""
    return HealthResponse(status=HEALTH_STATUS_OK)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_200_OK: {"model": ReadinessResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse},
    },
)
async def readiness_check(
    session: DbSession,
    response: Response,
) -> ReadinessResponse:
    """Return application readiness status.

    HTTP 503 is returned when PostgreSQL is unavailable so orchestrators can
    use this endpoint as a real readiness probe.
    """
    database_is_ready = await check_database_health(session)

    if database_is_ready:
        return ReadinessResponse(
            status=HEALTH_STATUS_READY,
            database=HEALTH_COMPONENT_OK,
        )

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status=HEALTH_STATUS_NOT_READY,
        database=HEALTH_COMPONENT_UNAVAILABLE,
    )
