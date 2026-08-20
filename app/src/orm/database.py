"""Async engine and session factory for the conversation store."""

from config import settings
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from .models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def get_engine() -> AsyncEngine:
    """Return the process-wide engine, creating it on first use."""
    global _engine, _session_factory

    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    return _engine


def get_session_factory() -> async_sessionmaker:
    """Return the session factory bound to the engine."""
    get_engine()
    return _session_factory


async def init_models() -> None:
    """Create any missing tables.

    A no-op once the tables exist, which is what makes it safe on every startup.
    Nothing here ever drops anything.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Close the connection pool."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
