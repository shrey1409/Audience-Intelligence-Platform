"""Integration tests for Alembic migrations — requires docker compose up -d postgres."""

from __future__ import annotations

import os
import warnings

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")
def migrated_schema(test_schema: str, test_db_url: str) -> str:
    """Run Alembic upgrade head against the isolated test schema."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)

    original_schema = os.environ.get("DATABASE__SCHEMA", "public")
    os.environ["DATABASE__SCHEMA"] = test_schema

    try:
        import importlib

        import app.core.config as cfg_mod

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            importlib.reload(cfg_mod)

        from scripts.run_migrations import run_migrations  # noqa: PLC0415

        run_migrations()
    finally:
        os.environ["DATABASE__SCHEMA"] = original_schema

    return test_schema


def test_run_migrations_creates_schema(test_schema: str, test_db_url: str) -> None:
    """run_migrations.py creates the configured schema if it does not already exist."""
    import importlib
    import os

    os.environ["DATABASE__SCHEMA"] = test_schema
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        import app.core.config as cfg_mod

        importlib.reload(cfg_mod)

    from scripts.run_migrations import run_migrations  # noqa: PLC0415

    run_migrations()

    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = :s"
            ),
            {"s": test_schema},
        )
        row = result.fetchone()

    engine.dispose()
    assert row is not None, f"Schema {test_schema!r} was not created"

    os.environ["DATABASE__SCHEMA"] = "public"


def test_all_10_tables_exist_after_migration(
    migrated_schema: str, test_db_url: str
) -> None:
    """All 10 staging tables exist in the schema after upgrade head."""
    expected_tables = {
        "zephr_users",
        "ga4_events",
        "ga4_identity_bridge",
        "braintree_subscriptions",
        "sailthru_newsletter",
        "pushly_subscribers",
        "openweb_engagement",
        "trackonomics_clicks",
        "transunion_demographics",
        "feature_store",
    }
    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = :s"
            ),
            {"s": migrated_schema},
        )
        actual_tables = {row[0] for row in result}

    engine.dispose()
    missing = expected_tables - actual_tables
    assert not missing, f"Tables missing from schema: {missing}"


def test_feature_store_has_64_columns_in_db(
    migrated_schema: str, test_db_url: str
) -> None:
    """feature_store table in the database has exactly 64 columns."""
    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = 'feature_store'"
            ),
            {"s": migrated_schema},
        )
        count = result.scalar()

    engine.dispose()
    assert count == 64, f"Expected 64 columns in feature_store, got {count}"


def test_fk_constraint_raises_integrity_error(
    migrated_schema: str, test_db_url: str
) -> None:
    """Inserting a row with a non-existent user_id FK raises IntegrityError."""
    import uuid

    engine = create_engine(test_db_url)
    with pytest.raises(IntegrityError):
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"INSERT INTO {migrated_schema}.braintree_subscriptions "
                    "(subscription_id, user_id, braintree_customer_id, plan_id, "
                    "status, amount, started_at) "
                    "VALUES (:sid, :uid, :cid, 'sports_plus', 'active', 9.99, NOW())"
                ),
                {
                    "sid": str(uuid.uuid4()),
                    "uid": str(uuid.uuid4()),  # non-existent user_id
                    "cid": "bt_test_999",
                },
            )
            conn.commit()

    engine.dispose()


def test_alembic_downgrade_drops_all_tables(
    migrated_schema: str, test_db_url: str
) -> None:
    """Alembic downgrade to base removes all application tables from the schema."""
    import importlib
    import os

    os.environ["DATABASE__SCHEMA"] = migrated_schema
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        import app.core.config as cfg_mod

        importlib.reload(cfg_mod)

    from alembic import command  # noqa: PLC0415
    from alembic.config import Config  # noqa: PLC0415

    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")

    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = :s AND table_name != 'alembic_version'"
            ),
            {"s": migrated_schema},
        )
        count = result.scalar()

    engine.dispose()
    assert count == 0, f"Expected 0 tables after downgrade, got {count}"
    os.environ["DATABASE__SCHEMA"] = "public"
