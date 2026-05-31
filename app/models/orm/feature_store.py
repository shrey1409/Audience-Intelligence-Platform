"""ORM model for feature_store — one row per registered user, 64 columns."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class FeatureStore(Base):
    """64 total: 46 ML features, 4 metadata flags, 10 ML output, 4 audit columns.

    Written by the Airflow pipeline via upsert ON CONFLICT(user_id) DO UPDATE.
    The user_id PRIMARY KEY provides the unique constraint required for upsert.
    No FK constraint — denormalised output table for maximum read performance.
    """

    __tablename__ = "feature_store"
    __table_args__ = {"schema": settings.database.schema}

    # ── Identity (4) ──────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    is_new_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Web behaviour features (11) — ML features #1–#11 ─────────────────────
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pageviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_session_duration: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    avg_pages_per_session: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("0")
    )
    bounce_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    mobile_ratio: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    desktop_ratio: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    pageviews_per_session: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("0")
    )
    days_since_last_visit: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    account_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Content affinity features (8) — ML features #12–#19 ──────────────────
    ratio_sports: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_entertainment: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_celebrity: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_shopping: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_opinion: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_world_news: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_business: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    ratio_lifestyle: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )

    # ── Subscription features (4) — ML features #20–#23 ──────────────────────
    has_subscription: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    subscription_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    total_billing_cycles: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    days_until_renewal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Email ML features (10) — ML features #24–#33 ─────────────────────────
    newsletter_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )
    open_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    click_through_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    email_engagement_score: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )
    nl_sports_alerts: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_morning_report: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_page_six_daily: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_celebrity_news: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_evening_update: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_post_opinion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # ── Email metadata flags (4) — NOT in ML matrix (see spec Section 15 Q7) ─
    nl_breaking_news: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_real_estate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nl_tech_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nl_lifestyle_weekly: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # ── Social features (4) — ML features #34–#37 ────────────────────────────
    total_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_likes_given: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    social_engagement_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Commerce features (6) — ML features #38–#43 ──────────────────────────
    total_affiliate_clicks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_revenue_generated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    conversion_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0")
    )
    avg_transaction_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    unique_advertisers_clicked: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── Demographic features (3) — ML features #44–#46 ───────────────────────
    age_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    income_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    has_children: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── ML output columns (10) — written by Step 8 (pipeline write-back) ─────
    persona_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    algorithm_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cluster_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subscription_propensity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    churn_propensity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    commerce_propensity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    # JSON string — null for non-GMM algorithms
    soft_persona_scores: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string — [[feature_name, importance_score], ...] top-5 per cluster
    cluster_top_features: Mapped[str | None] = mapped_column(Text, nullable=True)
