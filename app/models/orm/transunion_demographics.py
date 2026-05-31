"""ORM model for transunion_demographics — monthly demographic enrichment."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class TransunionDemographics(Base):
    """One row per user. Excluded if match_confidence < transunion_min_confidence."""

    __tablename__ = "transunion_demographics"
    __table_args__ = {"schema": settings.database.schema}

    demo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        unique=True,
        nullable=True,
    )
    hashed_email: Mapped[str] = mapped_column(String(64), nullable=False)
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    age_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    income_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    has_children: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    home_ownership: Mapped[str | None] = mapped_column(String(10), nullable=True)
    education: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    address_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
