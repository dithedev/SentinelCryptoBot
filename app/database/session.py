"""Lazy SQLAlchemy session factory.

The module must be safe to import without a configured DATABASE_URL. This is
important for tests, documentation tooling, static analysis, and importing the
FastAPI app object.

The real engine and sessionmaker are created only when code actually opens a
database session.
"""

from collections.abc import AsyncGenerator
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


class AsyncSessionFactory(Protocol):
    """Callable object that creates AsyncSession instances.

    Both SQLAlchemy async_sessionmaker and our lazy proxy match this protocol.
    Using this protocol lets bot middleware and workers accept either the real
    sessionmaker or the lazy proxy without forcing settings at import time.
    """

    def __call__(self, **kwargs: Any) -> AsyncSession:
        """Create a new AsyncSession."""
        ...


def create_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine from runtime settings."""
    settings = get_settings()

    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )


def get_engine() -> AsyncEngine:
    """Return the lazily initialized async SQLAlchemy engine."""
    global _engine

    if _engine is None:
        _engine = create_engine()

    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return the lazily initialized async sessionmaker."""
    global _session_maker

    if _session_maker is None:
        _session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_maker


class LazyAsyncSessionMaker:
    """Small callable proxy around the real async sessionmaker.

    Existing bot, API, and worker code can keep importing async_session_maker
    without forcing database configuration during module import.
    """

    def __call__(self, **kwargs: Any) -> AsyncSession:
        """Create a new AsyncSession using the real sessionmaker."""
        return get_async_session_maker()(**kwargs)


async_session_maker: AsyncSessionFactory = LazyAsyncSessionMaker()


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session.

    The session is rolled back on errors. Commit policy stays in the caller:
    FastAPI dependencies, bot middleware, or worker code.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose the initialized engine.

    This helper is useful for tests and graceful shutdown flows.
    """
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_maker = None
