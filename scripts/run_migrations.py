"""Run Alembic migrations: creates schema if absent, then upgrades to head."""

from __future__ import annotations

import sys

import structlog
from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from app.core.config import settings

logger = structlog.get_logger(__name__)


def run_migrations() -> None:
    """Create schema if absent and apply all pending Alembic migrations.

    Raises:
        sqlalchemy.exc.OperationalError: If the database is unreachable.
    """
    schema = settings.database.schema
    db_url = settings.database.url

    logger.info("migrations.start", schema=schema, url=db_url.split("@")[-1])

    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        logger.info("migrations.schema_ready", schema=schema)
    finally:
        engine.dispose()

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("migrations.complete", schema=schema)


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as exc:
        logger.error("migrations.failed", error=str(exc))
        sys.exit(1)
