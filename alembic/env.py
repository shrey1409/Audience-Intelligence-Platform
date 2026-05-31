"""Alembic migration environment — schema-aware."""

from __future__ import annotations

import warnings
from typing import Any

from sqlalchemy import engine_from_config, pool

from alembic import context

with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    from app.core.config import settings

# Import all ORM models to populate Base.metadata before autogenerate runs
import app.models.orm.braintree_subscriptions  # noqa: F401
import app.models.orm.feature_store  # noqa: F401
import app.models.orm.ga4_events  # noqa: F401
import app.models.orm.ga4_identity_bridge  # noqa: F401
import app.models.orm.openweb_engagement  # noqa: F401
import app.models.orm.pushly_subscribers  # noqa: F401
import app.models.orm.sailthru_newsletter  # noqa: F401
import app.models.orm.trackonomics_clicks  # noqa: F401
import app.models.orm.transunion_demographics  # noqa: F401
import app.models.orm.zephr_users  # noqa: F401
from app.models.orm.base import Base

target_metadata = Base.metadata
_schema = settings.database.schema


def include_object(
    object: Any,
    name: str,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """Filter autogenerate to only objects in the configured client schema.

    Args:
        object: The SQLAlchemy schema object being considered.
        name: The name of the object.
        type_: The object type string (e.g. "table", "column").
        reflected: Whether the object was reflected from the database.
        compare_to: The object being compared against (for diff operations).

    Returns:
        True if the object belongs to the configured schema and should be included.
    """
    if type_ == "table":
        return object.schema == _schema
    return True


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    config_section = context.config.get_section(context.config.config_ini_section, {})
    config_section["sqlalchemy.url"] = settings.database.url

    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version",
            version_table_schema=_schema,
            include_schemas=True,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in offline (SQL script generation) mode."""
    context.configure(
        url=settings.database.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema=_schema,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
