"""Builds the feature_store table by aggregating all source staging tables.

Reads all source tables via SQL GROUP BY (memory-efficient for 15M GA4 rows),
merges on user_id with left joins, applies zero-imputation (F-08), computes
all derived features, and writes FeatureStore rows in batches.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import Engine, text

from app.core.config import Settings
from app.models.orm.feature_store import FeatureStore
from scripts.seeds.db_writer import DbWriter

logger = structlog.get_logger(__name__)

REFERENCE_DATE: date = date(2026, 6, 1)

_AGE_SCORE_MAP: dict[str, int] = {
    "age_18_24": 1,
    "age_25_34": 2,
    "age_35_44": 3,
    "age_45_54": 4,
    "age_55_64": 5,
    "age_65_plus": 6,
}
_INCOME_SCORE_MAP: dict[str, int] = {
    "lt_30k": 1,
    "range_30_50k": 2,
    "range_50_75k": 3,
    "range_75_100k": 4,
    "range_100_150k": 5,
    "gt_150k": 6,
}


def _aggregate_ga4(engine: Engine, schema: str) -> pd.DataFrame:
    """Run SQL GROUP BY on ga4_events — returns one row per user with GA4 features."""
    sql = text(
        f"""
        SELECT
            e.user_id::text AS user_id,
            COUNT(DISTINCT e.session_id) AS total_sessions,
            COUNT(*) AS total_pageviews,
            COUNT(DISTINCT e.event_date) AS active_days,
            AVG(e.engagement_time_msec) / 1000.0 AS avg_session_duration,
            CASE
                WHEN COUNT(DISTINCT e.session_id) > 0
                THEN COUNT(*)::float / COUNT(DISTINCT e.session_id)
                ELSE 0
            END AS pageviews_per_session,
            CASE
                WHEN COUNT(DISTINCT e.session_id) > 0
                THEN COUNT(DISTINCT e.session_id) FILTER (WHERE e.is_bounce)::float
                     / COUNT(DISTINCT e.session_id)
                ELSE 0
            END AS bounce_rate,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.device_category = 'mobile')
                     ::float / COUNT(*) ELSE 0 END AS mobile_ratio,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.device_category = 'desktop')
                     ::float / COUNT(*) ELSE 0 END AS desktop_ratio,
            MAX(e.event_date) AS last_event_date,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'sports')
                     ::float / COUNT(*) ELSE 0 END AS ratio_sports,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'entertainment')
                     ::float / COUNT(*) ELSE 0 END AS ratio_entertainment,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'celebrity')
                     ::float / COUNT(*) ELSE 0 END AS ratio_celebrity,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'shopping')
                     ::float / COUNT(*) ELSE 0 END AS ratio_shopping,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'opinion')
                     ::float / COUNT(*) ELSE 0 END AS ratio_opinion,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'world_news')
                     ::float / COUNT(*) ELSE 0 END AS ratio_world_news,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'business')
                     ::float / COUNT(*) ELSE 0 END AS ratio_business,
            CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE e.page_category = 'lifestyle')
                     ::float / COUNT(*) ELSE 0 END AS ratio_lifestyle
        FROM {schema}.ga4_events e
        WHERE e.user_id IS NOT NULL
        GROUP BY e.user_id
    """
    )
    logger.info("feature_store.aggregate_ga4.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_ga4.done", rows=len(df))
    return df


def _aggregate_braintree(engine: Engine, schema: str) -> pd.DataFrame:
    """Aggregate braintree_subscriptions — most recent active record per user."""
    sql = text(
        f"""
        SELECT
            user_id::text AS user_id,
            MAX(CASE WHEN status = 'active' THEN 1 ELSE 0 END)
                ::boolean AS has_subscription,
            MAX(CASE WHEN status = 'active' THEN amount ELSE 0 END)
                AS subscription_amount,
            MAX(billing_cycle_count) AS total_billing_cycles,
            MAX(CASE
                WHEN status IN ('active', 'past_due') AND next_billing_date IS NOT NULL
                THEN (next_billing_date - '2026-06-01'::date)
                ELSE 0
            END) AS days_until_renewal
        FROM {schema}.braintree_subscriptions
        GROUP BY user_id
    """
    )
    logger.info("feature_store.aggregate_braintree.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_braintree.done", rows=len(df))
    return df


def _aggregate_sailthru(engine: Engine, schema: str) -> pd.DataFrame:
    """Read sailthru_newsletter — one row per user (already user-level)."""
    sql = text(
        f"""
        SELECT
            user_id::text AS user_id,
            newsletter_count,
            open_rate,
            click_through_rate,
            email_engagement_score,
            nl_sports_alerts,
            nl_morning_report,
            nl_page_six_daily,
            nl_celebrity_news,
            nl_evening_update,
            nl_post_opinion,
            nl_breaking_news,
            nl_real_estate,
            nl_tech_news,
            nl_lifestyle_weekly
        FROM {schema}.sailthru_newsletter
        WHERE user_id IS NOT NULL
    """
    )
    logger.info("feature_store.aggregate_sailthru.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_sailthru.done", rows=len(df))
    return df


def _aggregate_openweb(engine: Engine, schema: str) -> pd.DataFrame:
    """Aggregate openweb_engagement to comment/like/share totals per user."""
    sql = text(
        f"""
        SELECT
            user_id::text AS user_id,
            SUM(CASE WHEN event_type = 'comment' THEN 1 ELSE 0 END) AS total_comments,
            SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) AS total_likes_given,
            SUM(CASE WHEN event_type = 'share' THEN 1 ELSE 0 END) AS total_shares
        FROM {schema}.openweb_engagement
        GROUP BY user_id
    """
    )
    logger.info("feature_store.aggregate_openweb.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_openweb.done", rows=len(df))
    return df


def _aggregate_trackonomics(engine: Engine, schema: str) -> pd.DataFrame:
    """Aggregate trackonomics_clicks to commerce features per user."""
    sql = text(
        f"""
        SELECT
            user_id::text AS user_id,
            COUNT(*) AS total_affiliate_clicks,
            SUM(CASE WHEN converted THEN 1 ELSE 0 END) AS total_transactions,
            COALESCE(SUM(transaction_amount), 0) AS total_revenue_generated,
            COUNT(DISTINCT advertiser_id) AS unique_advertisers_clicked
        FROM {schema}.trackonomics_clicks
        GROUP BY user_id
    """
    )
    logger.info("feature_store.aggregate_trackonomics.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_trackonomics.done", rows=len(df))
    return df


def _aggregate_transunion(engine: Engine, schema: str) -> pd.DataFrame:
    """Read non-excluded transunion records for ML features."""
    sql = text(
        f"""
        SELECT
            user_id::text AS user_id,
            age_range,
            income_range,
            has_children
        FROM {schema}.transunion_demographics
        WHERE excluded = FALSE AND user_id IS NOT NULL
    """
    )
    logger.info("feature_store.aggregate_transunion.start")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    logger.info("feature_store.aggregate_transunion.done", rows=len(df))
    return df


def _aggregate_zephr(engine: Engine, schema: str) -> pd.DataFrame:
    """Read zephr created_at for account_age_days computation."""
    sql = text(
        f"""
        SELECT user_id::text AS user_id, created_at::date AS created_date
        FROM {schema}.zephr_users
    """
    )
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    return df


def _compute_derived(df: pd.DataFrame, low_t: float, high_t: float) -> pd.DataFrame:
    """Compute all derived features in-place on the merged DataFrame.

    Args:
        df: Merged DataFrame with all source columns.
        low_t: email_engagement low threshold from settings.
        high_t: email_engagement high threshold from settings.

    Returns:
        DataFrame with derived features added/corrected.
    """
    # days_since_last_visit: from GA4 last_event_date vs REFERENCE_DATE.
    if "last_event_date" in df.columns:
        df["last_event_date"] = pd.to_datetime(
            df["last_event_date"], errors="coerce"
        ).dt.date
        df["days_since_last_visit"] = df["last_event_date"].apply(
            lambda d: (REFERENCE_DATE - d).days if pd.notna(d) else 365
        )
    else:
        df["days_since_last_visit"] = 365

    # account_age_days: from zephr created_date.
    if "created_date" in df.columns:
        df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce").dt.date
        df["account_age_days"] = df["created_date"].apply(
            lambda d: (REFERENCE_DATE - d).days if pd.notna(d) else 0
        )

    # social_engagement_score: 3×comments + 1×likes + 2×shares.
    df["social_engagement_score"] = (
        3 * df["total_comments"].fillna(0).astype(int)
        + 1 * df["total_likes_given"].fillna(0).astype(int)
        + 2 * df["total_shares"].fillna(0).astype(int)
    )

    # conversion_rate: transactions / affiliate_clicks.
    clicks = df["total_affiliate_clicks"].fillna(0).astype(float)
    txns = df["total_transactions"].fillna(0).astype(float)
    df["conversion_rate"] = np.where(clicks > 0, txns / clicks, 0.0)

    # avg_transaction_value: revenue / transactions.
    revenue = df["total_revenue_generated"].fillna(0).astype(float)
    df["avg_transaction_value"] = np.where(txns > 0, revenue / txns, 0.0)

    # has_children: nullable Boolean → always bool (NULL → False).
    df["has_children"] = df["has_children"].fillna(False).astype(bool)

    # is_new_user: True if no GA4 data (total_sessions == 0 or absent).
    if "total_sessions" in df.columns:
        df["is_new_user"] = df["total_sessions"].fillna(0).astype(int) == 0
    else:
        df["is_new_user"] = True

    # Clip ratio_* features to [0, 1].
    ratio_cols = [c for c in df.columns if c.startswith("ratio_")]
    for col in ratio_cols:
        df[col] = df[col].fillna(0.0).clip(0.0, 1.0)

    # Clip bounce_rate, mobile_ratio, desktop_ratio to [0, 1].
    for col in ["bounce_rate", "mobile_ratio", "desktop_ratio"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0).clip(0.0, 1.0)

    # Clip open_rate, click_through_rate, conversion_rate to [0, 1].
    for col in ["open_rate", "click_through_rate", "conversion_rate"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0).clip(0.0, 1.0)

    # age_score / income_score: map from string range to ordinal; default 0.
    if "age_range" in df.columns:
        df["age_score"] = df["age_range"].map(_AGE_SCORE_MAP).fillna(0).astype(int)
    else:
        df["age_score"] = 0
    if "income_range" in df.columns:
        df["income_score"] = (
            df["income_range"].map(_INCOME_SCORE_MAP).fillna(0).astype(int)
        )
    else:
        df["income_score"] = 0

    return df


def build_feature_store(
    engine: Engine,
    db_writer: DbWriter,
    settings: Settings,
    all_user_ids: list[uuid.UUID],
) -> None:
    """Aggregate all source tables and write the feature_store.

    Strategy:
    1. Run SQL GROUP BY per source → DataFrames (95K rows max each).
    2. Left-join all frames onto the 100K user base DataFrame.
    3. Apply zero-imputation (F-08) via fillna(0) for numeric columns.
    4. Compute derived features.
    5. Write FeatureStore ORM objects in batch_size chunks.

    Args:
        engine: SQLAlchemy sync engine.
        db_writer: DbWriter instance for ORM batch writes.
        settings: Application settings.
        all_user_ids: All 100K user UUIDs (to ensure full outer join basis).
    """
    schema = settings.database.schema
    low_t = settings.email_engagement.low_threshold
    high_t = settings.email_engagement.high_threshold
    batch_size = settings.synthetic_data.batch_size
    logger.info("feature_store.build.start", n_users=len(all_user_ids))

    # Base frame: all users.
    base_df = pd.DataFrame({"user_id": [str(u) for u in all_user_ids]})

    # Aggregate each source.
    ga4_df = _aggregate_ga4(engine, schema)
    braintree_df = _aggregate_braintree(engine, schema)
    sailthru_df = _aggregate_sailthru(engine, schema)
    openweb_df = _aggregate_openweb(engine, schema)
    trackonomics_df = _aggregate_trackonomics(engine, schema)
    transunion_df = _aggregate_transunion(engine, schema)
    zephr_df = _aggregate_zephr(engine, schema)

    # Left-merge all sources onto the base.
    df = base_df.copy()
    df = df.merge(zephr_df, on="user_id", how="left")
    df = df.merge(ga4_df, on="user_id", how="left")
    df = df.merge(braintree_df, on="user_id", how="left")
    df = df.merge(sailthru_df, on="user_id", how="left")
    df = df.merge(openweb_df, on="user_id", how="left")
    df = df.merge(trackonomics_df, on="user_id", how="left")
    df = df.merge(transunion_df, on="user_id", how="left")

    logger.info("feature_store.merge.done", rows=len(df))

    # Zero-imputation (F-08): numeric columns → 0, boolean → False.
    int_cols = [
        "total_sessions",
        "total_pageviews",
        "active_days",
        "days_since_last_visit",
        "account_age_days",
        "total_billing_cycles",
        "days_until_renewal",
        "newsletter_count",
        "email_engagement_score",
        "total_comments",
        "total_likes_given",
        "total_shares",
        "social_engagement_score",
        "total_affiliate_clicks",
        "total_transactions",
        "unique_advertisers_clicked",
        "age_score",
        "income_score",
    ]
    float_cols = [
        "avg_session_duration",
        "avg_pages_per_session",
        "bounce_rate",
        "mobile_ratio",
        "desktop_ratio",
        "pageviews_per_session",
        "ratio_sports",
        "ratio_entertainment",
        "ratio_celebrity",
        "ratio_shopping",
        "ratio_opinion",
        "ratio_world_news",
        "ratio_business",
        "ratio_lifestyle",
        "subscription_amount",
        "open_rate",
        "click_through_rate",
        "total_revenue_generated",
        "conversion_rate",
        "avg_transaction_value",
    ]
    bool_cols = [
        "has_subscription",
        "nl_sports_alerts",
        "nl_morning_report",
        "nl_page_six_daily",
        "nl_celebrity_news",
        "nl_evening_update",
        "nl_post_opinion",
        "nl_breaking_news",
        "nl_real_estate",
        "nl_tech_news",
        "nl_lifestyle_weekly",
        "has_children",
    ]

    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0

    for col in float_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0.0).astype(float)
        else:
            df[col] = 0.0

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
        else:
            df[col] = False

    # Compute derived features.
    df = _compute_derived(df, low_t, high_t)

    logger.info("feature_store.derived.done")

    # Build ORM objects in batches.
    total_written = 0

    for i in range(0, len(df), batch_size):
        chunk = df.iloc[i : i + batch_size]
        objects: list[FeatureStore] = []

        for _, row in chunk.iterrows():
            uid = uuid.UUID(str(row["user_id"]))
            obj = FeatureStore(
                user_id=uid,
                is_new_user=bool(row.get("is_new_user", False)),
                # Web behaviour
                total_sessions=int(row.get("total_sessions", 0)),
                total_pageviews=int(row.get("total_pageviews", 0)),
                active_days=int(row.get("active_days", 0)),
                avg_session_duration=Decimal(
                    str(round(float(row.get("avg_session_duration", 0.0)), 2))
                ),
                avg_pages_per_session=Decimal(
                    str(round(float(row.get("pageviews_per_session", 0.0)), 4))
                ),
                bounce_rate=Decimal(str(round(float(row.get("bounce_rate", 0.0)), 4))),
                mobile_ratio=Decimal(
                    str(round(float(row.get("mobile_ratio", 0.0)), 4))
                ),
                desktop_ratio=Decimal(
                    str(round(float(row.get("desktop_ratio", 0.0)), 4))
                ),
                pageviews_per_session=Decimal(
                    str(round(float(row.get("pageviews_per_session", 0.0)), 4))
                ),
                days_since_last_visit=int(row.get("days_since_last_visit", 365)),
                account_age_days=int(row.get("account_age_days", 0)),
                # Content affinity
                ratio_sports=Decimal(
                    str(round(float(row.get("ratio_sports", 0.0)), 4))
                ),
                ratio_entertainment=Decimal(
                    str(round(float(row.get("ratio_entertainment", 0.0)), 4))
                ),
                ratio_celebrity=Decimal(
                    str(round(float(row.get("ratio_celebrity", 0.0)), 4))
                ),
                ratio_shopping=Decimal(
                    str(round(float(row.get("ratio_shopping", 0.0)), 4))
                ),
                ratio_opinion=Decimal(
                    str(round(float(row.get("ratio_opinion", 0.0)), 4))
                ),
                ratio_world_news=Decimal(
                    str(round(float(row.get("ratio_world_news", 0.0)), 4))
                ),
                ratio_business=Decimal(
                    str(round(float(row.get("ratio_business", 0.0)), 4))
                ),
                ratio_lifestyle=Decimal(
                    str(round(float(row.get("ratio_lifestyle", 0.0)), 4))
                ),
                # Subscription
                has_subscription=bool(row.get("has_subscription", False)),
                subscription_amount=Decimal(
                    str(round(float(row.get("subscription_amount", 0.0)), 2))
                ),
                total_billing_cycles=int(row.get("total_billing_cycles", 0)),
                days_until_renewal=int(row.get("days_until_renewal", 0)),
                # Email
                newsletter_count=int(row.get("newsletter_count", 0)),
                open_rate=Decimal(str(round(float(row.get("open_rate", 0.0)), 4))),
                click_through_rate=Decimal(
                    str(round(float(row.get("click_through_rate", 0.0)), 4))
                ),
                email_engagement_score=int(row.get("email_engagement_score", 0)),
                nl_sports_alerts=bool(row.get("nl_sports_alerts", False)),
                nl_morning_report=bool(row.get("nl_morning_report", False)),
                nl_page_six_daily=bool(row.get("nl_page_six_daily", False)),
                nl_celebrity_news=bool(row.get("nl_celebrity_news", False)),
                nl_evening_update=bool(row.get("nl_evening_update", False)),
                nl_post_opinion=bool(row.get("nl_post_opinion", False)),
                nl_breaking_news=bool(row.get("nl_breaking_news", False)),
                nl_real_estate=bool(row.get("nl_real_estate", False)),
                nl_tech_news=bool(row.get("nl_tech_news", False)),
                nl_lifestyle_weekly=bool(row.get("nl_lifestyle_weekly", False)),
                # Social
                total_comments=int(row.get("total_comments", 0)),
                total_likes_given=int(row.get("total_likes_given", 0)),
                total_shares=int(row.get("total_shares", 0)),
                social_engagement_score=int(row.get("social_engagement_score", 0)),
                # Commerce
                total_affiliate_clicks=int(row.get("total_affiliate_clicks", 0)),
                total_transactions=int(row.get("total_transactions", 0)),
                total_revenue_generated=Decimal(
                    str(round(float(row.get("total_revenue_generated", 0.0)), 2))
                ),
                conversion_rate=Decimal(
                    str(round(float(row.get("conversion_rate", 0.0)), 4))
                ),
                avg_transaction_value=Decimal(
                    str(round(float(row.get("avg_transaction_value", 0.0)), 2))
                ),
                unique_advertisers_clicked=int(
                    row.get("unique_advertisers_clicked", 0)
                ),
                # Demographics
                age_score=int(row.get("age_score", 0)),
                income_score=int(row.get("income_score", 0)),
                has_children=bool(row.get("has_children", False)),
                # ML output columns — NULL until Phase 7 writes them.
                persona_label=None,
                cluster_id=None,
                algorithm_used=None,
                cluster_score=None,
                last_updated=None,
                subscription_propensity_score=None,
                churn_propensity_score=None,
                commerce_propensity_score=None,
                soft_persona_scores=None,
                cluster_top_features=None,
            )
            objects.append(obj)

        db_writer.write_batch(objects, "feature_store")
        total_written += len(objects)
        logger.debug("feature_store.chunk.done", written=total_written, total=len(df))

    logger.info("feature_store.build.done", total_rows=total_written)
