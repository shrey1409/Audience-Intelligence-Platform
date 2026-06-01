from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base


class BraintreeSubscriptions(Base):
    """Braintree subscription and payment event staging table.

    One user can have multiple rows representing subscription history.
    Feature builder takes the most recent active subscription per user.
    """

    __tablename__ = "braintree_subscriptions"
    __table_args__ = {"schema": settings.database.schema}

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"
        ),
        nullable=False,
    )
    braintree_customer_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    plan_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    billing_cycle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
