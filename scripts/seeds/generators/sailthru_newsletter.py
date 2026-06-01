"""Generator for sailthru_newsletter staging table.

Coverage is 100% (settings.synthetic_data.source_coverage.sailthru = 1.00).
Every user gets exactly one SailthruNewsletter row.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import numpy as np
import structlog

from app.core.config import Settings
from app.models.orm.sailthru_newsletter import SailthruNewsletter
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

# 6 ML-matrix newsletter flags in spec order.
_ML_NL_FLAGS: list[str] = [
    "nl_sports_alerts",
    "nl_morning_report",
    "nl_page_six_daily",
    "nl_celebrity_news",
    "nl_evening_update",
    "nl_post_opinion",
]

# 4 metadata-only newsletter flags (not in 46-feature ML matrix).
_META_NL_FLAGS: list[str] = [
    "nl_breaking_news",
    "nl_real_estate",
    "nl_tech_news",
    "nl_lifestyle_weekly",
]


def generate_sailthru_newsletter(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    user_emails: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
) -> list[SailthruNewsletter]:
    """Generate one SailthruNewsletter row per user (100% coverage).

    email_engagement_score is computed from open_rate using config thresholds.
    newsletter_count = count of True values in the 6 ML newsletter flags.

    Args:
        all_user_ids: All 100K user IDs.
        user_persona_map: Maps user_id → persona name.
        user_emails: Maps user_id → email address (from zephr_users).
        rng: Seeded numpy RNG.
        settings: Application settings.

    Returns:
        List of 100K SailthruNewsletter ORM objects.
    """
    low_t = settings.email_engagement.low_threshold
    high_t = settings.email_engagement.high_threshold
    logger.info("sailthru.generate.start", n_users=len(all_user_ids))
    now = datetime(2026, 6, 1, 0, 0, 0)
    rows: list[SailthruNewsletter] = []

    for user_id in all_user_ids:
        persona = user_persona_map[user_id]
        archetype = get_archetype(persona)
        email = user_emails[user_id]

        open_rate = float(
            np.clip(
                rng.normal(archetype.open_rate_mu, archetype.open_rate_sigma), 0.0, 1.0
            )
        )
        ctr = float(
            np.clip(
                rng.normal(
                    archetype.click_through_rate_mu,
                    archetype.click_through_rate_sigma,
                ),
                0.0,
                1.0,
            )
        )

        # email_engagement_score: 0/1/2 ordinal.
        if open_rate < low_t:
            score = 0
            tier = "low"
        elif open_rate < high_t:
            score = 1
            tier = "medium"
        else:
            score = 2
            tier = "high"

        # ML newsletter flags.
        probs = [
            archetype.nl_sports_alerts_prob,
            archetype.nl_morning_report_prob,
            archetype.nl_page_six_daily_prob,
            archetype.nl_celebrity_news_prob,
            archetype.nl_evening_update_prob,
            archetype.nl_post_opinion_prob,
        ]
        ml_flags = [bool(rng.random() < p) for p in probs]
        nl_count = sum(ml_flags)

        # Metadata flags.
        meta_probs = [
            archetype.nl_breaking_news_prob,
            archetype.nl_real_estate_prob,
            archetype.nl_tech_news_prob,
            archetype.nl_lifestyle_weekly_prob,
        ]
        meta_flags = [bool(rng.random() < p) for p in meta_probs]

        subscribed = [
            name
            for name, flag in zip(_ML_NL_FLAGS + _META_NL_FLAGS, ml_flags + meta_flags)
            if flag
        ]

        rows.append(
            SailthruNewsletter(
                record_id=uuid.uuid4(),
                user_id=user_id,
                email=email,
                newsletter_count=nl_count,
                open_rate=Decimal(str(round(open_rate, 4))),
                click_through_rate=Decimal(str(round(ctr, 4))),
                email_engagement_score=score,
                engagement_tier=tier,
                subscribed_newsletters="|".join(subscribed) if subscribed else None,
                nl_sports_alerts=ml_flags[0],
                nl_morning_report=ml_flags[1],
                nl_page_six_daily=ml_flags[2],
                nl_celebrity_news=ml_flags[3],
                nl_evening_update=ml_flags[4],
                nl_post_opinion=ml_flags[5],
                nl_breaking_news=meta_flags[0],
                nl_real_estate=meta_flags[1],
                nl_tech_news=meta_flags[2],
                nl_lifestyle_weekly=meta_flags[3],
                last_synced_at=now,
            )
        )

    logger.info("sailthru.generate.done", rows=len(rows))
    return rows
