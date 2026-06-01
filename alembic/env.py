from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.models.orm import *  # noqa: F401,F403
from app.models.orm.base import Base

config = context.config
# Read schema from env at run time so integration tests can override via os.environ.
_schema = os.environ.get("DATABASE__SCHEMA") or settings.database.schema
_db_url = os.environ.get("DATABASE__URL") or settings.database.url

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _include_object(
    obj: object, name: str, type_: str, reflected: bool, compare_to: object
) -> bool:
    """Only autogenerate migrations for objects in our configured schema."""
    if type_ == "table":
        return getattr(obj, "schema", None) == _schema
    return True


def run_migrations_offline() -> None:
    """Run migrations against a URL string (no DB connection needed)."""
    url = _db_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=_include_object,
        version_table_schema=_schema,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live engine connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=_include_object,
            version_table_schema=_schema,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
