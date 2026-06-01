from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class TrackonomicsClicks(Base):
    """Trackonomics affiliate click and transaction staging table.

    Incremental daily SFTP export.
    """

    __tablename__ = "trackonomics_clicks"
    __table_args__ = {"schema": settings.database.schema}

    click_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    advertiser_id: Mapped[str] = mapped_column(String(100), nullable=False)
    product_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    click_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    converted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
