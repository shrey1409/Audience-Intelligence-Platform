from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class PushlySubscribers(Base):
    """Pushly push notification opt-in staging table — incremental daily sync."""

    __tablename__ = "pushly_subscribers"
    __table_args__ = {"schema": settings.database.schema}

    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    push_opted_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    opted_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_push_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    push_open_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
