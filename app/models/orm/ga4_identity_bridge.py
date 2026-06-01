from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class Ga4IdentityBridge(Base):
    """Persistent mapping from GA4 user_pseudo_id to Zephr user_id.

    Populated incrementally as users log in during GA4-tracked sessions.
    UNIQUE on user_pseudo_id enforces one resolved identity per anonymous GA4 ID.
    """

    __tablename__ = "ga4_identity_bridge"
    __table_args__ = {"schema": settings.database.schema}

    bridge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_pseudo_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
