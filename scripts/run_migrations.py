"""Run Alembic migrations against the configured PostgreSQL schema.

Creates the schema if it does not exist, then runs alembic upgrade head.
Usage: python scripts/run_migrations.py
"""

from __future__ import annotations

import warnings

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    from app.core.config import settings


def run_migrations() -> None:
    """Create schema if absent, then apply all pending Alembic migrations.

    Raises:
        sqlalchemy.exc.OperationalError: If the database is unreachable.
        alembic.util.exc.CommandError: If the migration fails.
    """
    engine = create_engine(settings.database.url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.database.schema}"))
        conn.commit()
    engine.dispose()

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    run_migrations()
