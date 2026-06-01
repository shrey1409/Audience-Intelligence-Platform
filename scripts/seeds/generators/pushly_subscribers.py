"""Generator for pushly_subscribers staging table.

Coverage: 35% of users (settings.synthetic_data.source_coverage.pushly).
external_id = str(user_id) — the spec states external_id = user_id at push opt-in.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import numpy as np
import structlog

from app.core.config import Settings
from app.models.orm.pushly_subscribers import PushlySubscribers

logger = structlog.get_logger(__name__)

_REFERENCE_DT = datetime(2026, 6, 1, 0, 0, 0)
_PLATFORMS = ["web_desktop", "web_mobile", "ios", "android"]


def generate_pushly_subscribers(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    user_account_age: dict[uuid.UUID, int],
    rng: np.random.Generator,
    settings: Settings,
) -> list[PushlySubscribers]:
    """Generate PushlySubscribers rows for 35% of users.

    Args:
        all_user_ids: All 100K user IDs.
        user_persona_map: Maps user_id → persona name.
        user_account_age: Maps user_id → account_age_days (for opted_in_at).
        rng: Seeded numpy RNG.
        settings: Application settings.

    Returns:
        List of PushlySubscribers ORM objects.
    """
    sd = settings.synthetic_data
    n_pushly = int(sd.n_users * sd.source_coverage.pushly)
    logger.info("pushly.generate.start", target=n_pushly)

    selected = rng.choice(
        all_user_ids,  # type: ignore[arg-type]
        size=min(n_pushly, len(all_user_ids)),
        replace=False,
    ).tolist()

    rows: list[PushlySubscribers] = []

    for user_id in selected:
        persona = user_persona_map[user_id]
        age_days = user_account_age[user_id]

        # Platform: skewed by persona.
        if persona in ("loyalist", "sports_focused"):
            platform_probs = [0.35, 0.25, 0.30, 0.10]
        elif persona in ("social_engager", "celebrity_entertainment"):
            platform_probs = [0.20, 0.45, 0.20, 0.15]
        else:
            platform_probs = [0.30, 0.35, 0.20, 0.15]
        platform = str(rng.choice(_PLATFORMS, p=platform_probs))

        # 85% active, 15% unsubscribed.
        is_active = bool(rng.random() < 0.85)

        # opted_in_at: sometime in [1, account_age_days] days before reference.
        opt_days_ago = int(rng.integers(1, max(2, age_days)))
        opted_in_at = _REFERENCE_DT - timedelta(days=opt_days_ago)

        opted_out_at: datetime | None = None
        if not is_active:
            opt_out_days = int(rng.integers(1, max(2, opt_days_ago)))
            opted_out_at = _REFERENCE_DT - timedelta(days=opt_out_days)

        last_push_days = int(rng.integers(0, 31))
        last_push_sent_at = _REFERENCE_DT - timedelta(days=last_push_days)

        # push_open_count: higher for engaged personas.
        if persona in ("loyalist", "subscription_focused"):
            open_count = max(0, int(rng.normal(25, 8)))
        elif persona == "low_engager":
            open_count = max(0, int(rng.normal(3, 2)))
        else:
            open_count = max(0, int(rng.normal(12, 6)))

        rows.append(
            PushlySubscribers(
                subscriber_id=uuid.uuid4(),
                user_id=user_id,
                external_id=str(user_id),
                platform=platform,
                push_opted_in=True,
                push_is_active=is_active,
                opted_in_at=opted_in_at,
                opted_out_at=opted_out_at,
                last_push_sent_at=last_push_sent_at,
                push_open_count=open_count,
            )
        )

    logger.info("pushly.generate.done", rows=len(rows))
    return rows
