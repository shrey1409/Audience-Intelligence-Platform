"""Generator for ga4_events and ga4_identity_bridge staging tables.

GA4 events are generated in chunks of batch_size users but yielded in
sub-batches of GA4_SUBBATCH_SIZE events (20K) regardless of user chunk
boundaries. This prevents large memory spikes when users have many events.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import structlog

from app.core.config import Settings
from app.models.orm.ga4_identity_bridge import Ga4IdentityBridge
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

REFERENCE_DATE: date = date(2026, 6, 1)
_REFERENCE_DT = datetime(2026, 6, 1, 23, 59, 59)

EVENT_NAMES: list[str] = ["page_view", "session_start", "scroll", "user_engagement"]
EVENT_NAME_WEIGHTS: list[float] = [0.70, 0.15, 0.10, 0.05]

GA4_SUBBATCH_SIZE: int = 20_000


def _chunked(lst: list[Any], size: int) -> Generator[list[Any], None, None]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def generate_ga4_events(
    ga4_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
) -> Generator[
    tuple[list[dict[str, Any]], dict[str, tuple[datetime, datetime]]], None, None
]:
    """Yield chunks of ga4_events rows as Core-insert dicts.

    Each yield is a tuple of:
    - list[dict]: Batch of event row dicts (ready for Core bulk insert).
    - dict: Updated first_last_seen accumulator (user_pseudo_id → (first_dt, last_dt)).

    The first_last_seen dict is cumulative across all chunks — caller should
    pass the same dict through each iteration and use the final state for
    bridge generation.

    Args:
        ga4_user_ids: Exactly the subset of user_ids selected for GA4.
        user_persona_map: Maps all user_ids to persona names.
        rng: Seeded numpy RNG.
        settings: Application settings.

    Yields:
        (event_rows, first_last_seen) tuples, one per chunk of batch_size users.
    """
    sd = settings.synthetic_data
    chunk_size = sd.batch_size
    mean_events = sd.ga4_events_per_user_mean
    std_events = sd.ga4_events_per_user_std
    total_users = len(ga4_user_ids)

    logger.info(
        "ga4_events.generate.start",
        ga4_users=total_users,
        mean_events_per_user=mean_events,
    )

    first_last_seen: dict[str, tuple[datetime, datetime]] = {}
    total_events = 0
    # Accumulator shared across all user chunks; flushed in 20K sub-batches.
    batch: list[dict[str, Any]] = []

    for chunk in _chunked(ga4_user_ids, chunk_size):
        for user_id in chunk:
            persona_name = user_persona_map[user_id]
            archetype = get_archetype(persona_name)

            # One stable user_pseudo_id per user.
            user_pseudo_id = uuid.uuid4().hex[:20]

            page_cat_keys = list(archetype.page_category_weights.keys())
            page_cat_probs = list(archetype.page_category_weights.values())
            device_keys = list(archetype.device_weights.keys())
            device_probs = list(archetype.device_weights.values())

            # n_events drawn from Normal, clipped to [5, 500].
            n_events = int(np.clip(rng.normal(mean_events, std_events), 5, 500))

            # Sessions: 1 event per ~12 events on average (10–20 sessions).
            n_sessions = max(1, int(rng.normal(n_events / 12, 2)))
            session_sizes = rng.multinomial(n_events, [1.0 / n_sessions] * n_sessions)

            # Event dates spread over last 365 days, weighted by recency.
            days_ago_options = np.arange(0, 365)
            # Persona's days_since_last_visit controls recency bias.
            recency_mu = archetype.days_since_last_visit_mu
            weights_raw = np.exp(-days_ago_options / max(recency_mu * 2, 30))
            day_weights = weights_raw / weights_raw.sum()

            # Draw one base date per session.
            session_base_days = rng.choice(
                days_ago_options, size=n_sessions, p=day_weights
            )

            user_first_dt: datetime | None = None
            user_last_dt: datetime | None = None

            for s_idx, (s_size, base_days) in enumerate(
                zip(session_sizes, session_base_days)
            ):
                if s_size == 0:
                    continue
                session_id = uuid.uuid4().hex[:16]
                device = str(rng.choice(device_keys, p=device_probs))
                event_date = REFERENCE_DATE - timedelta(days=int(base_days))
                is_single_event_session = s_size == 1

                for e_idx in range(s_size):
                    event_id = uuid.uuid4()
                    event_name = str(rng.choice(EVENT_NAMES, p=EVENT_NAME_WEIGHTS))
                    page_cat = str(rng.choice(page_cat_keys, p=page_cat_probs))
                    # Timestamp: random hour/minute within the event date.
                    hour = int(rng.integers(0, 24))
                    minute = int(rng.integers(0, 60))
                    second = int(rng.integers(0, 60))
                    event_ts = datetime(
                        event_date.year,
                        event_date.month,
                        event_date.day,
                        hour,
                        minute,
                        second,
                    )
                    # engagement_time_msec: draw in seconds, convert to ms.
                    dur_s = max(
                        0,
                        rng.normal(
                            archetype.avg_session_duration_mu,
                            archetype.avg_session_duration_sigma,
                        ),
                    )
                    engagement_ms = int(dur_s * 1000)

                    # is_bounce: True only on single-event sessions.
                    is_bounce = is_single_event_session and e_idx == 0

                    batch.append(
                        {
                            "event_id": event_id,
                            "user_id": user_id,
                            "user_pseudo_id": user_pseudo_id,
                            "event_name": event_name,
                            "event_date": event_date,
                            "event_timestamp": event_ts,
                            "session_id": session_id,
                            "device_category": device,
                            "page_category": page_cat,
                            "page_path": f"/{page_cat}/article",
                            "engagement_time_msec": engagement_ms,
                            "is_bounce": is_bounce,
                        }
                    )

                    if user_first_dt is None or event_ts < user_first_dt:
                        user_first_dt = event_ts
                    if user_last_dt is None or event_ts > user_last_dt:
                        user_last_dt = event_ts

            if user_first_dt is not None and user_last_dt is not None:
                first_last_seen[user_pseudo_id] = (user_first_dt, user_last_dt)

            # Flush completed 20K sub-batches immediately after each user,
            # never accumulating more than GA4_SUBBATCH_SIZE rows in memory.
            while len(batch) >= GA4_SUBBATCH_SIZE:
                sub = batch[:GA4_SUBBATCH_SIZE]
                batch = batch[GA4_SUBBATCH_SIZE:]
                total_events += len(sub)
                logger.debug(
                    "ga4_events.subbatch.done",
                    subbatch_events=len(sub),
                    total_events=total_events,
                )
                yield sub, first_last_seen

    # Yield any remaining events that did not fill a full sub-batch.
    if batch:
        total_events += len(batch)
        logger.debug(
            "ga4_events.subbatch.done",
            subbatch_events=len(batch),
            total_events=total_events,
        )
        yield batch, first_last_seen

    logger.info(
        "ga4_events.generate.done",
        total_events=total_events,
        total_users=total_users,
    )


def generate_ga4_identity_bridge(
    ga4_user_ids: list[uuid.UUID],
    user_pseudo_id_map: dict[uuid.UUID, str],
    first_last_seen: dict[str, tuple[datetime, datetime]],
) -> list[Ga4IdentityBridge]:
    """Generate one Ga4IdentityBridge row per GA4 user.

    Args:
        ga4_user_ids: Subset of user_ids with GA4 records.
        user_pseudo_id_map: Maps user_id → user_pseudo_id.
        first_last_seen: Maps user_pseudo_id → (first_event_ts, last_event_ts).

    Returns:
        List of Ga4IdentityBridge ORM objects.
    """
    logger.info("ga4_bridge.generate.start", count=len(ga4_user_ids))
    bridges: list[Ga4IdentityBridge] = []
    now = datetime(2026, 6, 1, 0, 0, 0)

    for user_id in ga4_user_ids:
        pseudo_id = user_pseudo_id_map[user_id]
        first_dt, last_dt = first_last_seen.get(pseudo_id, (now, now))
        bridges.append(
            Ga4IdentityBridge(
                bridge_id=uuid.uuid4(),
                user_pseudo_id=pseudo_id,
                user_id=user_id,
                first_seen_at=first_dt,
                last_seen_at=last_dt,
                created_at=now,
                updated_at=now,
            )
        )

    logger.info("ga4_bridge.generate.done", count=len(bridges))
    return bridges
