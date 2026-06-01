"""Integration tests verifying no NULL user_ids in staging tables after seed run.

Requires docker compose up -d postgres and a completed seed run.
Uses subprocess isolation for schema queries per Phase 2 gotcha.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def _get_db_url() -> str:
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://aip_user:aip_password@localhost:5432/audience_intelligence",
    )


def _count_null_user_ids(table: str, schema: str = "public") -> int:
    """Query count of NULL user_ids in the given table."""
    engine = create_engine(_get_db_url())
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {schema}.{table} WHERE user_id IS NULL")
            )
            return result.scalar() or 0
    finally:
        engine.dispose()


def _count_rows(table: str, schema: str = "public") -> int:
    """Query total row count for the given table."""
    engine = create_engine(_get_db_url())
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}"))
            return result.scalar() or 0
    finally:
        engine.dispose()


def test_no_null_user_ids_zephr() -> None:
    """zephr_users.user_id is the PK — must never be NULL."""
    null_count = _count_null_user_ids("zephr_users")
    assert null_count == 0, f"Found {null_count} NULL user_ids in zephr_users"


def test_no_null_user_ids_braintree() -> None:
    null_count = _count_null_user_ids("braintree_subscriptions")
    assert (
        null_count == 0
    ), f"Found {null_count} NULL user_ids in braintree_subscriptions"


def test_no_null_user_ids_openweb() -> None:
    null_count = _count_null_user_ids("openweb_engagement")
    assert null_count == 0, f"Found {null_count} NULL user_ids in openweb_engagement"


def test_no_null_user_ids_pushly() -> None:
    null_count = _count_null_user_ids("pushly_subscribers")
    assert null_count == 0, f"Found {null_count} NULL user_ids in pushly_subscribers"


def test_no_null_user_ids_trackonomics() -> None:
    null_count = _count_null_user_ids("trackonomics_clicks")
    assert null_count == 0, f"Found {null_count} NULL user_ids in trackonomics_clicks"


def test_no_null_user_ids_transunion() -> None:
    """transunion.user_id is nullable by schema; we populate it for all 70K records."""
    null_count = _count_null_user_ids("transunion_demographics")
    assert (
        null_count == 0
    ), f"Found {null_count} NULL user_ids in transunion_demographics"


def test_no_null_user_ids_sailthru() -> None:
    """sailthru.user_id is nullable FK, but coverage=100% means all rows have it."""
    null_count = _count_null_user_ids("sailthru_newsletter")
    assert null_count == 0, f"Found {null_count} NULL user_ids in sailthru_newsletter"


@pytest.mark.parametrize(
    "table",
    [
        "zephr_users",
        "braintree_subscriptions",
        "openweb_engagement",
        "pushly_subscribers",
        "trackonomics_clicks",
        "transunion_demographics",
        "sailthru_newsletter",
    ],
)
def test_no_null_user_ids_all_tables(table: str) -> None:
    null_count = _count_null_user_ids(table)
    assert null_count == 0, f"Found {null_count} NULL user_ids in {table}"


def test_feature_store_row_count_is_100000() -> None:
    from app.core.config import settings

    expected = settings.synthetic_data.n_users
    actual = _count_rows("feature_store")
    assert actual == expected, f"feature_store has {actual} rows, expected {expected}"


def test_zephr_users_row_count_is_100000() -> None:
    from app.core.config import settings

    expected = settings.synthetic_data.n_users
    actual = _count_rows("zephr_users")
    assert actual == expected, f"zephr_users has {actual} rows, expected {expected}"


def test_ga4_events_row_count_within_expected_range() -> None:
    """GA4 events should be in [5*95000, 500*95000] — validates chunked write."""
    from app.core.config import settings

    sd = settings.synthetic_data
    n_ga4_users = int(sd.n_users * sd.source_coverage.ga4)
    min_expected = 5 * n_ga4_users  # min 5 events per user (clipped lower bound)
    max_expected = 500 * n_ga4_users  # max 500 events per user (clipped upper bound)
    actual = _count_rows("ga4_events")
    assert (
        min_expected <= actual <= max_expected
    ), f"ga4_events has {actual} rows, expected [{min_expected}, {max_expected}]"
