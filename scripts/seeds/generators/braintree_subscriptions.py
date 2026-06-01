"""Generator for braintree_subscriptions staging table.

Loyalist and subscription_focused personas are over-sampled to match
their real-world subscription participation rates.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import numpy as np
import structlog
from faker import Faker

from app.core.config import Settings
from app.models.orm.braintree_subscriptions import BraintreeSubscriptions
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

REFERENCE_DATE: date = date(2026, 6, 1)

_PLAN_AMOUNTS: dict[str, float] = {
    "sports_plus": 14.99,
    "home_delivery": 19.99,
    "digital_all_access": 29.99,
}
_PLANS: list[str] = list(_PLAN_AMOUNTS)


def generate_braintree_subscriptions(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
    faker: Faker,
) -> list[BraintreeSubscriptions]:
    """Generate BraintreeSubscriptions rows for ~10% of users.

    Loyalists (97% participation) and subscription_focused (72%) are
    selected first; remaining quota filled from other personas.

    Args:
        all_user_ids: All 100K user IDs (as list, not shuffled by caller).
        user_persona_map: Maps user_id → persona name.
        rng: Seeded numpy RNG.
        settings: Application settings.
        faker: Seeded Faker instance.

    Returns:
        List of BraintreeSubscriptions ORM objects.
    """
    sd = settings.synthetic_data
    target_count = int(sd.n_users * sd.source_coverage.braintree)
    logger.info("braintree.generate.start", target=target_count)

    # Separate users by persona.
    loyalist_ids = [u for u in all_user_ids if user_persona_map[u] == "loyalist"]
    sub_focused_ids = [
        u for u in all_user_ids if user_persona_map[u] == "subscription_focused"
    ]
    other_ids = [
        u
        for u in all_user_ids
        if user_persona_map[u] not in ("loyalist", "subscription_focused")
    ]

    # Over-sample high-signal personas.
    n_loyalist = min(
        len(loyalist_ids),
        int(round(len(loyalist_ids) * 0.97)),
    )
    n_sub = min(
        len(sub_focused_ids),
        int(round(len(sub_focused_ids) * 0.72)),
    )
    n_other = max(0, target_count - n_loyalist - n_sub)

    selected: list[uuid.UUID] = []
    if n_loyalist > 0 and loyalist_ids:
        selected.extend(
            rng.choice(
                loyalist_ids, size=min(n_loyalist, len(loyalist_ids)), replace=False
            ).tolist()
        )
    if n_sub > 0 and sub_focused_ids:
        selected.extend(
            rng.choice(
                sub_focused_ids, size=min(n_sub, len(sub_focused_ids)), replace=False
            ).tolist()
        )
    if n_other > 0 and other_ids:
        selected.extend(
            rng.choice(
                other_ids, size=min(n_other, len(other_ids)), replace=False
            ).tolist()
        )

    # Deduplicate and trim to target.
    seen: set[uuid.UUID] = set()
    deduped: list[uuid.UUID] = []
    for uid in selected:
        if uid not in seen:
            seen.add(uid)
            deduped.append(uid)
    selected_ids = deduped[:target_count]

    rows: list[BraintreeSubscriptions] = []
    used_customer_ids: set[str] = set()

    for user_id in selected_ids:
        persona = user_persona_map[user_id]
        archetype = get_archetype(persona)

        # Unique braintree_customer_id.
        cid = f"bt_{user_id.hex[:16]}"
        while cid in used_customer_ids:
            cid = f"bt_{faker.uuid4().replace('-', '')[:16]}"
        used_customer_ids.add(cid)

        plan = str(rng.choice(_PLANS))
        amount = Decimal(str(_PLAN_AMOUNTS[plan]))

        # Status: loyalists and subscription_focused mostly active.
        if persona in ("loyalist", "subscription_focused"):
            status = str(rng.choice(["active", "past_due"], p=[0.92, 0.08]))
        else:
            status = str(
                rng.choice(["active", "canceled", "past_due"], p=[0.60, 0.30, 0.10])
            )

        billing_cycles = max(
            1,
            int(
                rng.normal(
                    archetype.billing_cycle_count_mu,
                    archetype.billing_cycle_count_sigma,
                )
            ),
        )

        started_at_date = REFERENCE_DATE - timedelta(days=billing_cycles * 30)
        started_at = datetime(
            started_at_date.year, started_at_date.month, started_at_date.day, 0, 0, 0
        )

        if status == "active":
            days_to_renewal = int(rng.integers(1, 31))
            next_billing = REFERENCE_DATE + timedelta(days=days_to_renewal)
            canceled_at = None
        elif status == "past_due":
            days_overdue = int(rng.integers(1, 15))
            next_billing = REFERENCE_DATE - timedelta(days=days_overdue)
            canceled_at = None
        else:
            next_billing = None
            canceled_days = int(rng.integers(1, billing_cycles * 30))
            canceled_dt = REFERENCE_DATE - timedelta(days=canceled_days)
            canceled_at = datetime(
                canceled_dt.year, canceled_dt.month, canceled_dt.day, 0, 0, 0
            )

        payment = str(rng.choice(["credit_card", "paypal"], p=[0.80, 0.20]))

        rows.append(
            BraintreeSubscriptions(
                subscription_id=uuid.uuid4(),
                user_id=user_id,
                braintree_customer_id=cid,
                plan_id=plan,
                status=status,
                amount=amount,
                currency="USD",
                billing_cycle_count=billing_cycles,
                next_billing_date=next_billing,
                started_at=started_at,
                canceled_at=canceled_at,
                payment_method=payment,
            )
        )

    logger.info("braintree.generate.done", rows=len(rows))
    return rows
