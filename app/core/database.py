from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = structlog.get_logger(__name__)


def _async_url(url: str) -> str:
    """Convert postgresql:// URL to postgresql+asyncpg:// for async engine."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _sync_url(url: str) -> str:
    """Ensure URL uses psycopg2 (sync) driver scheme."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


# Async engine — used by FastAPI request handlers
async_engine = create_async_engine(
    _async_url(settings.database.url),
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    echo=settings.database.echo,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine — used by ETL scripts, ML pipelines, Alembic migrations
sync_engine = create_engine(
    _sync_url(settings.database.url),
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    echo=settings.database.echo,
)

SyncSessionLocal: sessionmaker[Session] = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async database session.

    Yields:
        AsyncSession scoped to the request.
    """
    logger.debug("db_session.open")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            logger.error("db_session.error", error=str(exc))
            await session.rollback()
            raise
        finally:
            logger.debug("db_session.close")
