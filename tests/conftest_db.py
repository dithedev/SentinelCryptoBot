"""Database fixtures for real PostgreSQL integration tests."""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_test_database_url() -> str | None:
    """Return the PostgreSQL URL used for integration tests."""
    return os.getenv("DATABASE_URL_TEST") or os.getenv("DATABASE_URL")


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Create one async engine per database test.

    Function scope keeps asyncpg bound to the same pytest-asyncio event loop.
    Session-scoped engines break on CI with "attached to a different loop".
    """
    database_url = get_test_database_url()

    if database_url is None:
        pytest.skip("DATABASE_URL_TEST or DATABASE_URL is not configured")

    engine = create_async_engine(database_url)

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL is not available for integration tests: {exc}")

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Yield a database session wrapped in a rollback transaction."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
    )
    session = session_factory()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
