"""SQLAlchemy engines and session factories — async (FastAPI) + sync (ETL/ML)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _async_dsn(sync_dsn: str) -> str:
    """Convert a postgresql:// DSN to postgresql+asyncpg:// for use with asyncpg driver.

    Args:
        sync_dsn: Standard PostgreSQL DSN (psycopg2 style).

    Returns:
        asyncpg-compatible DSN string.
    """
    return sync_dsn.replace("postgresql://", "postgresql+asyncpg://", 1)


# ── Async engine — FastAPI endpoints via get_db dependency ───────────────────

async_engine: AsyncEngine = create_async_engine(
    _async_dsn(settings.database.url),
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    echo=settings.database.echo,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Sync engine — ETL/ML pipelines and Alembic migrations ────────────────────

sync_engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    echo=settings.database.echo,
)

SyncSessionLocal: sessionmaker[Session] = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession and handles commit/rollback.

    Yields:
        An active AsyncSession scoped to the current request.
    """
    async with AsyncSessionLocal() as session:
        yield session
