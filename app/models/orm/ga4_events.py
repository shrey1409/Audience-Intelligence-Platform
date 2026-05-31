"""ORM model for ga4_events — raw GA4 page-view and session events."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class Ga4Events(Base):
    """Raw GA4 event rows. user_id nullable — populated by identity stitching."""

    __tablename__ = "ga4_events"
    __table_args__ = {"schema": settings.database.schema}

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # ON DELETE SET NULL: event history is preserved even if the user is deleted
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="SET NULL"
        ),
        nullable=True,
    )
    user_pseudo_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    engagement_time_msec: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_bounce: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
