"""Standalone validator for the feature_store table.

Queries the live database to verify:
1. feature_store has exactly n_users rows.
2. All 46 ML feature columns are non-null for >= 95% of rows.
3. Coverage rates for all source tables are within ±2% of config targets.

Exits 0 on success, 1 on any failure.

Usage:
    PYTHONPATH=. python3 scripts/validate_features.py
"""

from __future__ import annotations

import sys

import structlog
from sqlalchemy import text

from app.core.config import settings
from app.core.database import sync_engine

logger = structlog.get_logger(__name__)

# 46 ML feature columns as defined in configs/base.yaml ml.features.matrix.
ML_FEATURES: list[str] = [
    "total_sessions",
    "total_pageviews",
    "active_days",
    "avg_session_duration",
    "avg_pages_per_session",
    "bounce_rate",
    "mobile_ratio",
    "desktop_ratio",
    "pageviews_per_session",
    "days_since_last_visit",
    "account_age_days",
    "ratio_sports",
    "ratio_entertainment",
    "ratio_celebrity",
    "ratio_shopping",
    "ratio_opinion",
    "ratio_world_news",
    "ratio_business",
    "ratio_lifestyle",
    "has_subscription",
    "subscription_amount",
    "total_billing_cycles",
    "days_until_renewal",
    "newsletter_count",
    "open_rate",
    "click_through_rate",
    "email_engagement_score",
    "nl_sports_alerts",
    "nl_morning_report",
    "nl_page_six_daily",
    "nl_celebrity_news",
    "nl_evening_update",
    "nl_post_opinion",
    "total_comments",
    "total_likes_given",
    "total_shares",
    "social_engagement_score",
    "total_affiliate_clicks",
    "total_transactions",
    "total_revenue_generated",
    "conversion_rate",
    "avg_transaction_value",
    "unique_advertisers_clicked",
    "age_score",
    "income_score",
    "has_children",
]


def validate_feature_coverage(schema: str, n_users: int) -> bool:
    """Check that all 46 ML features are non-null for >= 95% of rows.

    Args:
        schema: Database schema name.
        n_users: Expected total row count.

    Returns:
        True if all checks pass, False otherwise.
    """
    all_pass = True
    threshold = 0.95

    with sync_engine.connect() as conn:
        total_result = conn.execute(
            text(f"SELECT COUNT(*) FROM {schema}.feature_store")
        )
        actual_count = total_result.scalar() or 0

        if actual_count != n_users:
            logger.error(
                "validate.row_count.fail",
                expected=n_users,
                actual=actual_count,
            )
            all_pass = False
        else:
            logger.info("validate.row_count.pass", count=actual_count)

        for feature in ML_FEATURES:
            null_result = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {schema}.feature_store"
                    f" WHERE {feature} IS NULL"
                )
            )
            null_count = null_result.scalar() or 0
            null_rate = null_count / max(actual_count, 1)
            non_null_rate = 1.0 - null_rate

            if non_null_rate < threshold:
                logger.error(
                    "validate.feature.fail",
                    feature=feature,
                    non_null_rate=round(non_null_rate, 4),
                    threshold=threshold,
                )
                all_pass = False
            else:
                logger.debug(
                    "validate.feature.pass",
                    feature=feature,
                    non_null_rate=round(non_null_rate, 4),
                )

    return all_pass


def validate_coverage_rates(schema: str, n_users: int) -> bool:
    """Check staging table row counts against config coverage targets (±2%).

    Args:
        schema: Database schema name.
        n_users: Total user count (denominator for coverage rate).

    Returns:
        True if all tables within tolerance, False otherwise.
    """
    cov = settings.synthetic_data.source_coverage
    table_targets: dict[str, float] = {
        "zephr_users": 1.0,
        "ga4_identity_bridge": cov.ga4,
        "braintree_subscriptions": cov.braintree,
        "sailthru_newsletter": cov.sailthru,
        "pushly_subscribers": cov.pushly,
        "transunion_demographics": cov.transunion,
        "feature_store": 1.0,
    }
    tolerance = 0.02
    all_pass = True

    with sync_engine.connect() as conn:
        for table, target in table_targets.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}"))
            actual = result.scalar() or 0
            actual_rate = actual / n_users
            diff = abs(actual_rate - target)
            if diff > tolerance:
                logger.error(
                    "validate.coverage.fail",
                    table=table,
                    expected_rate=target,
                    actual_rate=round(actual_rate, 4),
                    diff=round(diff, 4),
                )
                all_pass = False
            else:
                logger.info(
                    "validate.coverage.pass",
                    table=table,
                    rate=round(actual_rate, 4),
                    target=target,
                )

    return all_pass


def main() -> None:
    """Run all validation checks and exit 1 if any fail."""
    sd = settings.synthetic_data
    schema = settings.database.schema
    n_users = sd.n_users
    logger.info("validate.start", schema=schema, n_users=n_users)

    checks = [
        validate_feature_coverage(schema, n_users),
        validate_coverage_rates(schema, n_users),
    ]

    if all(checks):
        logger.info("validate.all_pass")
        sys.exit(0)
    else:
        logger.error("validate.fail", failed_checks=checks.count(False))
        sys.exit(1)


if __name__ == "__main__":
    main()
