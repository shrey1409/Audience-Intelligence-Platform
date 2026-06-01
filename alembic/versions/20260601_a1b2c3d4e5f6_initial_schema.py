"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-01 00:00:00.000000

"""

from __future__ import annotations

import os
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op
from app.core.config import settings

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_schema = os.environ.get("DATABASE__SCHEMA") or settings.database.schema


def upgrade() -> None:
    # 1. zephr_users — PK table; all FKs reference this
    op.create_table(
        "zephr_users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_email", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("account_age_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_registered", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("registration_date", sa.DateTime, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.zephr_users"
            f" ADD CONSTRAINT uq_zephr_users_email UNIQUE (email)"
        )
    )
    op.execute(
        text(f"CREATE INDEX idx_zephr_users_email ON {_schema}.zephr_users(email)")
    )
    op.execute(
        text(
            f"CREATE INDEX idx_zephr_users_hashed_email"
            f" ON {_schema}.zephr_users(hashed_email)"
            f" WHERE hashed_email IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_zephr_users_registration_date"
            f" ON {_schema}.zephr_users(registration_date)"
        )
    )

    # 2. ga4_events — nullable user_id FK (resolved by identity stitching)
    op.create_table(
        "ga4_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_pseudo_id", sa.String(64), nullable=False),
        sa.Column("event_name", sa.String(100), nullable=False),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("event_timestamp", sa.DateTime, nullable=False),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("device_category", sa.String(50), nullable=True),
        sa.Column("page_category", sa.String(50), nullable=True),
        sa.Column("page_path", sa.Text, nullable=True),
        sa.Column(
            "engagement_time_msec", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("is_bounce", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.ga4_events"
            f" ADD CONSTRAINT fk_ga4_events_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE SET NULL"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.ga4_events"
            f" ADD CONSTRAINT chk_ga4_events_device_category"
            f" CHECK (device_category IN ('desktop','mobile','tablet'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.ga4_events"
            f" ADD CONSTRAINT chk_ga4_events_page_category"
            f" CHECK (page_category IN"
            f" ('sports','entertainment','celebrity','business',"
            f"'lifestyle','world_news','opinion','shopping','us_news','page_six'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_ga4_events_user_id ON {_schema}.ga4_events(user_id)"
            f" WHERE user_id IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_ga4_events_user_pseudo_id"
            f" ON {_schema}.ga4_events(user_pseudo_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_ga4_events_event_date"
            f" ON {_schema}.ga4_events(event_date)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_ga4_events_pseudo_id_date"
            f" ON {_schema}.ga4_events(user_pseudo_id, event_date)"
        )
    )

    # 3. ga4_identity_bridge
    op.create_table(
        "ga4_identity_bridge",
        sa.Column("bridge_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_pseudo_id", sa.String(64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_seen_at", sa.DateTime, nullable=False),
        sa.Column("last_seen_at", sa.DateTime, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.ga4_identity_bridge"
            f" ADD CONSTRAINT uq_ga4_bridge_user_pseudo_id UNIQUE (user_pseudo_id)"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.ga4_identity_bridge"
            f" ADD CONSTRAINT fk_ga4_bridge_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"CREATE UNIQUE INDEX idx_ga4_bridge_user_pseudo_id"
            f" ON {_schema}.ga4_identity_bridge(user_pseudo_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_ga4_bridge_user_id"
            f" ON {_schema}.ga4_identity_bridge(user_id)"
        )
    )

    # 4. braintree_subscriptions
    op.create_table(
        "braintree_subscriptions",
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("braintree_customer_id", sa.String(50), nullable=False),
        sa.Column("plan_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "billing_cycle_count", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("next_billing_date", sa.Date, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("canceled_at", sa.DateTime, nullable=True),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.braintree_subscriptions"
            f" ADD CONSTRAINT uq_braintree_customer_id UNIQUE (braintree_customer_id)"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.braintree_subscriptions"
            f" ADD CONSTRAINT fk_braintree_subscriptions_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.braintree_subscriptions"
            f" ADD CONSTRAINT chk_braintree_plan_id"
            f" CHECK (plan_id IN ('sports_plus','home_delivery','digital_all_access'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.braintree_subscriptions"
            f" ADD CONSTRAINT chk_braintree_status"
            f" CHECK (status IN ('active','canceled','past_due'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.braintree_subscriptions"
            f" ADD CONSTRAINT chk_braintree_payment_method"
            f" CHECK (payment_method IN ('credit_card','paypal'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_braintree_user_id"
            f" ON {_schema}.braintree_subscriptions(user_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_braintree_status"
            f" ON {_schema}.braintree_subscriptions(status)"
        )
    )

    # 5. sailthru_newsletter
    op.create_table(
        "sailthru_newsletter",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column(
            "newsletter_count", sa.SmallInteger, nullable=False, server_default="0"
        ),
        sa.Column("open_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "click_through_rate", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "email_engagement_score",
            sa.SmallInteger,
            nullable=False,
            server_default="0",
        ),
        sa.Column("engagement_tier", sa.String(10), nullable=True),
        sa.Column("subscribed_newsletters", sa.Text, nullable=True),
        sa.Column(
            "nl_sports_alerts", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_morning_report", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_page_six_daily", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_celebrity_news", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_evening_update", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_post_opinion", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_breaking_news", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column("nl_real_estate", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("nl_tech_news", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "nl_lifestyle_weekly", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.sailthru_newsletter"
            f" ADD CONSTRAINT fk_sailthru_newsletter_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE SET NULL"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.sailthru_newsletter"
            f" ADD CONSTRAINT chk_sailthru_engagement_tier"
            f" CHECK (engagement_tier IN ('low','medium','high'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_sailthru_user_id"
            f" ON {_schema}.sailthru_newsletter(user_id)"
            f" WHERE user_id IS NOT NULL"
        )
    )
    op.execute(
        text(f"CREATE INDEX idx_sailthru_email ON {_schema}.sailthru_newsletter(email)")
    )

    # 6. pushly_subscribers
    op.create_table(
        "pushly_subscribers",
        sa.Column("subscriber_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("push_opted_in", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("push_is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("opted_in_at", sa.DateTime, nullable=False),
        sa.Column("opted_out_at", sa.DateTime, nullable=True),
        sa.Column("last_push_sent_at", sa.DateTime, nullable=True),
        sa.Column("push_open_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.pushly_subscribers"
            f" ADD CONSTRAINT uq_pushly_external_id UNIQUE (external_id)"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.pushly_subscribers"
            f" ADD CONSTRAINT fk_pushly_subscribers_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.pushly_subscribers"
            f" ADD CONSTRAINT chk_pushly_platform"
            f" CHECK (platform IN ('web_desktop','web_mobile','ios','android'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_pushly_user_id ON {_schema}.pushly_subscribers(user_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_pushly_platform"
            f" ON {_schema}.pushly_subscribers(platform)"
        )
    )

    # 7. openweb_engagement
    op.create_table(
        "openweb_engagement",
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("content_id", sa.String(100), nullable=True),
        sa.Column("content_category", sa.String(50), nullable=True),
        sa.Column("engaged_at", sa.DateTime, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.openweb_engagement"
            f" ADD CONSTRAINT fk_openweb_engagement_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.openweb_engagement"
            f" ADD CONSTRAINT chk_openweb_event_type"
            f" CHECK (event_type IN ('comment','like','share'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_openweb_user_id ON {_schema}.openweb_engagement(user_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_openweb_user_event_type"
            f" ON {_schema}.openweb_engagement(user_id, event_type)"
        )
    )

    # 8. trackonomics_clicks
    op.create_table(
        "trackonomics_clicks",
        sa.Column("click_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("advertiser_id", sa.String(100), nullable=False),
        sa.Column("product_category", sa.String(30), nullable=True),
        sa.Column("click_timestamp", sa.DateTime, nullable=False),
        sa.Column("converted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("transaction_id", sa.String(100), nullable=True),
        sa.Column("transaction_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.trackonomics_clicks"
            f" ADD CONSTRAINT fk_trackonomics_clicks_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.trackonomics_clicks"
            f" ADD CONSTRAINT chk_trackonomics_product_category"
            f" CHECK (product_category IN"
            f" ('electronics','fashion','home','beauty',"
            f"'sports_gear','books','travel'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_trackonomics_user_id"
            f" ON {_schema}.trackonomics_clicks(user_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_trackonomics_user_converted"
            f" ON {_schema}.trackonomics_clicks(user_id, converted)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_trackonomics_advertiser_id"
            f" ON {_schema}.trackonomics_clicks(advertiser_id)"
        )
    )

    # 9. transunion_demographics
    op.create_table(
        "transunion_demographics",
        sa.Column("demo_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hashed_email", sa.String(64), nullable=False),
        sa.Column("match_confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("excluded", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("age_range", sa.String(20), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("income_range", sa.String(20), nullable=True),
        sa.Column("has_children", sa.Boolean, nullable=True),
        sa.Column("home_ownership", sa.String(10), nullable=True),
        sa.Column("education", sa.String(20), nullable=True),
        sa.Column("address_state", sa.String(2), nullable=True),
        sa.Column("address_zip", sa.String(10), nullable=True),
        sa.Column("match_date", sa.Date, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT uq_transunion_user_id UNIQUE (user_id)"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT fk_transunion_demographics_user_id"
            f" FOREIGN KEY (user_id) REFERENCES {_schema}.zephr_users(user_id)"
            f" ON DELETE CASCADE"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT chk_transunion_age_range"
            f" CHECK (age_range IN"
            f" ('age_18_24','age_25_34','age_35_44',"
            f"'age_45_54','age_55_64','age_65_plus'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT chk_transunion_gender"
            f" CHECK (gender IN ('m','f','non_binary','unknown'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT chk_transunion_income_range"
            f" CHECK (income_range IN"
            f" ('lt_30k','range_30_50k','range_50_75k',"
            f"'range_75_100k','range_100_150k','gt_150k'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT chk_transunion_home_ownership"
            f" CHECK (home_ownership IN ('owner','renter','unknown'))"
        )
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.transunion_demographics"
            f" ADD CONSTRAINT chk_transunion_education"
            f" CHECK (education IN"
            f" ('high_school','some_college','bachelors','graduate'))"
        )
    )
    op.execute(
        text(
            f"CREATE UNIQUE INDEX idx_transunion_user_id"
            f" ON {_schema}.transunion_demographics(user_id)"
            f" WHERE user_id IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_transunion_hashed_email"
            f" ON {_schema}.transunion_demographics(hashed_email)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_transunion_match_confidence"
            f" ON {_schema}.transunion_demographics(match_confidence)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_transunion_excluded"
            f" ON {_schema}.transunion_demographics(excluded)"
            f" WHERE excluded = FALSE"
        )
    )

    # 10. feature_store — created last; PK = user_id; no FK (denormalised output table)
    op.create_table(
        "feature_store",
        # --- Identity (4) ---
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("is_new_user", sa.Boolean, nullable=False, server_default="false"),
        # --- Web behaviour (11) ---
        sa.Column("total_sessions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_pageviews", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "avg_session_duration",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "avg_pages_per_session",
            sa.Numeric(8, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("bounce_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("mobile_ratio", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "desktop_ratio", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "pageviews_per_session",
            sa.Numeric(8, 4),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "days_since_last_visit", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("account_age_days", sa.Integer, nullable=False, server_default="0"),
        # --- Content affinity (8) ---
        sa.Column("ratio_sports", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "ratio_entertainment", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_celebrity", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_shopping", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_opinion", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_world_news", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_business", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "ratio_lifestyle", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        # --- Subscription (4) ---
        sa.Column(
            "has_subscription", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "subscription_amount", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "total_billing_cycles", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("days_until_renewal", sa.Integer, nullable=False, server_default="0"),
        # --- Email ML features (10) ---
        sa.Column(
            "newsletter_count", sa.SmallInteger, nullable=False, server_default="0"
        ),
        sa.Column("open_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column(
            "click_through_rate", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "email_engagement_score",
            sa.SmallInteger,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "nl_sports_alerts", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_morning_report", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_page_six_daily", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_celebrity_news", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_evening_update", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "nl_post_opinion", sa.Boolean, nullable=False, server_default="false"
        ),
        # --- Email metadata (4 — NOT in ML matrix) ---
        sa.Column(
            "nl_breaking_news", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column("nl_real_estate", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("nl_tech_news", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "nl_lifestyle_weekly", sa.Boolean, nullable=False, server_default="false"
        ),
        # --- Social (4) ---
        sa.Column("total_comments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_likes_given", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_shares", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "social_engagement_score", sa.Integer, nullable=False, server_default="0"
        ),
        # --- Commerce (6) ---
        sa.Column(
            "total_affiliate_clicks", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("total_transactions", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "total_revenue_generated",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "conversion_rate", sa.Numeric(5, 4), nullable=False, server_default="0"
        ),
        sa.Column(
            "avg_transaction_value",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "unique_advertisers_clicked", sa.Integer, nullable=False, server_default="0"
        ),
        # --- Demographic (3) ---
        sa.Column("age_score", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("income_score", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("has_children", sa.Boolean, nullable=False, server_default="false"),
        # --- ML output (10) ---
        sa.Column("persona_label", sa.String(50), nullable=True),
        sa.Column("cluster_id", sa.SmallInteger, nullable=True),
        sa.Column("algorithm_used", sa.String(50), nullable=True),
        sa.Column("cluster_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("last_updated", sa.DateTime, nullable=True),
        sa.Column("subscription_propensity_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("churn_propensity_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("commerce_propensity_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("soft_persona_scores", sa.Text, nullable=True),
        sa.Column("cluster_top_features", sa.Text, nullable=True),
        schema=_schema,
    )
    op.execute(
        text(
            f"ALTER TABLE {_schema}.feature_store"
            f" ADD CONSTRAINT chk_feature_store_algorithm_used"
            f" CHECK (algorithm_used IN"
            f" ('kmeans','bisecting_kmeans','gmm','hdbscan','ensemble'))"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_feature_store_persona_label"
            f" ON {_schema}.feature_store(persona_label)"
            f" WHERE persona_label IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_feature_store_cluster_id"
            f" ON {_schema}.feature_store(cluster_id)"
            f" WHERE cluster_id IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_feature_store_persona_cluster"
            f" ON {_schema}.feature_store(persona_label, cluster_id)"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_feature_store_last_updated"
            f" ON {_schema}.feature_store(last_updated)"
            f" WHERE last_updated IS NOT NULL"
        )
    )
    op.execute(
        text(
            f"CREATE INDEX idx_feature_store_is_new_user"
            f" ON {_schema}.feature_store(is_new_user)"
            f" WHERE is_new_user = TRUE"
        )
    )


def downgrade() -> None:
    op.drop_table("feature_store", schema=_schema)
    op.drop_table("transunion_demographics", schema=_schema)
    op.drop_table("trackonomics_clicks", schema=_schema)
    op.drop_table("openweb_engagement", schema=_schema)
    op.drop_table("pushly_subscribers", schema=_schema)
    op.drop_table("sailthru_newsletter", schema=_schema)
    op.drop_table("braintree_subscriptions", schema=_schema)
    op.drop_table("ga4_identity_bridge", schema=_schema)
    op.drop_table("ga4_events", schema=_schema)
    op.drop_table("zephr_users", schema=_schema)
