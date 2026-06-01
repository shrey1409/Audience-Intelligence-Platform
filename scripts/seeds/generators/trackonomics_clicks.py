"""Generator for trackonomics_clicks staging table.

Uses SQLAlchemy Core bulk insert (yielded as list[dict]) due to ~500K rows.
High-value shoppers at 90% participation with Poisson(50) clicks.
Occasional buyers at 70% participation with Poisson(20) clicks.
Remaining commerce users at Poisson(32) clicks to hit ~500K total.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import structlog
from faker import Faker

from app.core.config import Settings
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

_REFERENCE_DT = datetime(2026, 6, 1, 0, 0, 0)
_PRODUCT_CATEGORIES = [
    "electronics",
    "fashion",
    "home",
    "beauty",
    "sports_gear",
    "books",
    "travel",
]
_COMMERCE_PERSONAS = {"high_value_shopper", "occasional_buyer"}


def _build_advertiser_pool(faker: Faker, size: int = 50) -> list[str]:
    return [
        f"adv_{faker.company()[:20].replace(' ', '_').lower()}" for _ in range(size)
    ]


def generate_trackonomics_clicks(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
    faker: Faker,
) -> Generator[list[dict[str, Any]], None, None]:
    """Generate TrackonomicsClicks rows as Core-insert dicts, chunked by batch_size.

    Args:
        all_user_ids: All 100K user IDs.
        user_persona_map: Maps user_id → persona name.
        rng: Seeded numpy RNG.
        settings: Application settings.
        faker: Seeded Faker instance (for advertiser pool).

    Yields:
        Batches of click row dicts (Core bulk insert format).
    """
    sd = settings.synthetic_data
    n_trackonomics = int(sd.n_users * sd.source_coverage.trackonomics)
    batch_size = sd.batch_size
    logger.info("trackonomics.generate.start", target_users=n_trackonomics)

    advertiser_pool = _build_advertiser_pool(faker)

    hv_ids = [u for u in all_user_ids if user_persona_map[u] == "high_value_shopper"]
    occ_ids = [u for u in all_user_ids if user_persona_map[u] == "occasional_buyer"]
    other_ids = [
        u for u in all_user_ids if user_persona_map[u] not in _COMMERCE_PERSONAS
    ]

    n_hv = min(len(hv_ids), int(round(len(hv_ids) * 0.90)))
    n_occ = min(len(occ_ids), int(round(len(occ_ids) * 0.70)))
    n_other = max(0, n_trackonomics - n_hv - n_occ)

    selected_hv = (
        rng.choice(hv_ids, size=min(n_hv, len(hv_ids)), replace=False).tolist()
        if hv_ids
        else []
    )
    selected_occ = (
        rng.choice(occ_ids, size=min(n_occ, len(occ_ids)), replace=False).tolist()
        if occ_ids
        else []
    )
    selected_other = (
        rng.choice(other_ids, size=min(n_other, len(other_ids)), replace=False).tolist()
        if other_ids
        else []
    )

    all_selected = selected_hv + selected_occ + selected_other
    total_rows = 0
    batch: list[dict[str, Any]] = []

    for user_id in all_selected:
        persona = user_persona_map[user_id]
        archetype = get_archetype(persona)

        n_clicks = int(rng.poisson(archetype.trackonomics_clicks_lambda))
        if n_clicks == 0:
            n_clicks = 1

        for _ in range(n_clicks):
            click_id = uuid.uuid4()
            advertiser = str(rng.choice(advertiser_pool))
            product_cat = str(rng.choice(_PRODUCT_CATEGORIES))
            days_ago = int(rng.integers(0, 366))
            hour = int(rng.integers(0, 24))
            click_ts = _REFERENCE_DT - timedelta(days=days_ago, hours=hour)

            converted = bool(rng.random() < archetype.conversion_prob)
            txn_id: str | None = None
            txn_amount: Decimal | None = None

            if converted:
                txn_id = f"txn_{uuid.uuid4().hex[:12]}"
                raw_amount = float(
                    np.clip(
                        rng.normal(
                            archetype.transaction_amount_mu,
                            archetype.transaction_amount_sigma,
                        ),
                        1.0,
                        500.0,
                    )
                )
                txn_amount = Decimal(str(round(raw_amount, 2)))

            batch.append(
                {
                    "click_id": click_id,
                    "user_id": user_id,
                    "advertiser_id": advertiser,
                    "product_category": product_cat,
                    "click_timestamp": click_ts,
                    "converted": converted,
                    "transaction_id": txn_id,
                    "transaction_amount": txn_amount,
                }
            )
            total_rows += 1

            if len(batch) >= batch_size:
                logger.debug("trackonomics.chunk.yield", rows=len(batch))
                yield batch
                batch = []

    if batch:
        yield batch

    logger.info(
        "trackonomics.generate.done",
        total_rows=total_rows,
        commerce_users=len(all_selected),
    )
