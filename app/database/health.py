"""Database health check helpers.

This module contains a tiny database readiness check used by the API. It is
kept outside the route layer so the same helper can be reused later by the bot,
worker, startup checks, Docker health checks, or tests.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_database_health(session: AsyncSession) -> bool:
    """Return True when the database connection is usable.

    The query is intentionally minimal. We only need to verify that the app can
    talk to PostgreSQL, not that any specific business table contains data.
    """
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("database_health_check_failed")
        return False

    return True
