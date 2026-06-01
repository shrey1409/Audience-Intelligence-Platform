"""Generator for openweb_engagement staging table.

Generates individual social engagement events (comment/like/share) per user.
Social engager personas are over-sampled (80% participation) with Poisson(40)
events. Other openweb users get Poisson(5) events.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import datetime, timedelta

import numpy as np
import structlog

from app.core.config import Settings
from app.models.orm.openweb_engagement import OpenwebEngagement
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

_REFERENCE_DT = datetime(2026, 6, 1, 0, 0, 0)
_EVENT_TYPES = ["comment", "like", "share"]


def generate_openweb_engagement(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
) -> Generator[list[OpenwebEngagement], None, None]:
    """Generate OpenwebEngagement rows in batches.

    Social engager users: Poisson(40) events at 80% participation.
    All other openweb users: Poisson(5) events.
    Yields batches of batch_size rows to avoid memory pressure.

    Args:
        all_user_ids: All 100K user IDs.
        user_persona_map: Maps user_id → persona name.
        rng: Seeded numpy RNG.
        settings: Application settings.

    Yields:
        Batches of OpenwebEngagement ORM objects.
    """
    sd = settings.synthetic_data
    n_openweb = int(sd.n_users * sd.source_coverage.openweb)
    batch_size = sd.batch_size
    logger.info("openweb.generate.start", target=n_openweb)

    social_ids = [u for u in all_user_ids if user_persona_map[u] == "social_engager"]
    other_ids = [u for u in all_user_ids if user_persona_map[u] != "social_engager"]

    # Social engagers at 80% participation.
    n_social = min(len(social_ids), int(round(len(social_ids) * 0.80)))
    n_other = max(0, n_openweb - n_social)

    selected_social = (
        rng.choice(
            social_ids, size=min(n_social, len(social_ids)), replace=False
        ).tolist()
        if social_ids
        else []
    )
    selected_other = (
        rng.choice(other_ids, size=min(n_other, len(other_ids)), replace=False).tolist()
        if other_ids
        else []
    )

    all_selected = selected_social + selected_other
    total_rows = 0
    batch: list[OpenwebEngagement] = []

    for user_id in all_selected:
        persona = user_persona_map[user_id]
        archetype = get_archetype(persona)

        n_events = int(rng.poisson(archetype.openweb_events_lambda))
        if n_events == 0:
            continue

        page_cat_keys = list(archetype.page_category_weights.keys())
        page_cat_probs = list(archetype.page_category_weights.values())

        comments_f = archetype.comments_fraction
        likes_f = archetype.likes_fraction
        shares_f = max(0.0, 1.0 - comments_f - likes_f)
        event_probs = [comments_f, likes_f, shares_f]

        for _ in range(n_events):
            event_type = str(rng.choice(_EVENT_TYPES, p=event_probs))
            days_ago = int(rng.integers(0, 181))
            hour = int(rng.integers(0, 24))
            engaged_at = _REFERENCE_DT - timedelta(days=days_ago, hours=hour)
            content_cat = str(rng.choice(page_cat_keys, p=page_cat_probs))

            batch.append(
                OpenwebEngagement(
                    engagement_id=uuid.uuid4(),
                    user_id=user_id,
                    event_type=event_type,
                    content_id=f"article_{int(rng.integers(1, 100001))}",
                    content_category=content_cat,
                    engaged_at=engaged_at,
                )
            )
            total_rows += 1

            if len(batch) >= batch_size:
                logger.debug("openweb.chunk.yield", rows=len(batch))
                yield batch
                batch = []

    if batch:
        yield batch

    logger.info(
        "openweb.generate.done", total_rows=total_rows, openweb_users=len(all_selected)
    )
