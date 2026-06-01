from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class OpenwebEngagement(Base):
    """OpenWeb social engagement event staging table — incremental daily sync.

    Stores individual events (comment / like / share), not pre-aggregated totals.
    Feature builder groups by user_id to produce the 4 ML social features.
    """

    __tablename__ = "openweb_engagement"
    __table_args__ = {"schema": settings.database.schema}

    engagement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    engaged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
