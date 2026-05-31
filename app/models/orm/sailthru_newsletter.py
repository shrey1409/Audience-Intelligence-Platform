"""ORM model for sailthru_newsletter — newsletter subscription aggregates."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
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


class SailthruNewsletter(Base):
    """One aggregate row per registered user email. Full-refresh weekly."""

    __tablename__ = "sailthru_newsletter"
    __table_args__ = {"schema": settings.database.schema}

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(String(254), nullable=False)
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
    engagement_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subscribed_newsletters: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ML matrix features (#28–#33)
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
    # Metadata flags — NOT in ML matrix (see database-schema-spec.md Section 15 Q7)
    nl_breaking_news: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    nl_real_estate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nl_tech_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nl_lifestyle_weekly: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
