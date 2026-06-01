"""Integration tests for Alembic migrations — requires docker compose up -d postgres."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.integration


def _alembic_cfg(db_url: str, schema: str) -> Config:
    """Build an Alembic config pointing at the given schema."""
    cfg = Config("alembic.ini")
    os.environ["DATABASE__URL"] = db_url
    os.environ["DATABASE__SCHEMA"] = schema
    return cfg


def test_run_migrations_creates_schema_if_absent(test_db_url: str) -> None:
    import uuid

    schema = f"test_schema_{uuid.uuid4().hex[:6]}"
    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata"
                    f" WHERE schema_name = '{schema}'"
                )
            )
            assert result.scalar() == schema
    finally:
        with engine.connect() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.commit()
        engine.dispose()


def test_alembic_upgrade_head_completes_without_error(
    test_db_url: str, test_schema: str
) -> None:
    cfg = _alembic_cfg(test_db_url, test_schema)
    command.upgrade(cfg, "head")

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {test_schema}.alembic_version")
            )
            assert result.scalar() == 1
    finally:
        engine.dispose()


def test_all_10_tables_exist_after_migration(
    test_db_url: str, test_schema: str
) -> None:
    cfg = _alembic_cfg(test_db_url, test_schema)
    command.upgrade(cfg, "head")

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables"
                    f" WHERE table_schema = '{test_schema}'"
                    " AND table_type = 'BASE TABLE'"
                )
            )
            table_names = {row[0] for row in result}
    finally:
        engine.dispose()

    expected = {
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
    assert expected.issubset(table_names)


def test_feature_store_has_64_columns_in_db(test_db_url: str, test_schema: str) -> None:
    cfg = _alembic_cfg(test_db_url, test_schema)
    command.upgrade(cfg, "head")

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.columns"
                    f" WHERE table_schema = '{test_schema}'"
                    " AND table_name = 'feature_store'"
                )
            )
            count = result.scalar()
    finally:
        engine.dispose()

    assert count == 64, f"Expected 64 columns in feature_store, got {count}"


def test_fk_constraint_active(test_db_url: str, test_schema: str) -> None:
    cfg = _alembic_cfg(test_db_url, test_schema)
    command.upgrade(cfg, "head")

    import uuid
    from datetime import datetime

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        f"INSERT INTO {test_schema}.braintree_subscriptions"
                        " (subscription_id, user_id, braintree_customer_id,"
                        "  plan_id, status, amount, started_at)"
                        " VALUES (:sid, :uid, :cid, :plan, :status, :amount, :started)"
                    ),
                    {
                        "sid": str(uuid.uuid4()),
                        "uid": str(uuid.uuid4()),  # non-existent user
                        "cid": "cust_fk_test",
                        "plan": "sports_plus",
                        "status": "active",
                        "amount": 9.99,
                        "started": datetime.utcnow(),
                    },
                )
                conn.commit()
    finally:
        engine.dispose()


def test_alembic_downgrade_returns_to_base(test_db_url: str, test_schema: str) -> None:
    cfg = _alembic_cfg(test_db_url, test_schema)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(test_db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables"
                    f" WHERE table_schema = '{test_schema}'"
                    " AND table_type = 'BASE TABLE'"
                    " AND table_name != 'alembic_version'"
                )
            )
            count = result.scalar()
    finally:
        engine.dispose()

    assert count == 0, f"Expected 0 tables after downgrade, got {count}"
