"""CLI entry point for synthetic data generation.

Orchestrates the full pipeline in strict insertion order:
  zephr_users → ga4_events → ga4_identity_bridge → braintree_subscriptions
  → sailthru_newsletter → pushly_subscribers → openweb_engagement
  → trackonomics_clicks → transunion_demographics → feature_store

Usage:
    PYTHONPATH=. python3 scripts/seeds/generate_synthetic_data.py [--truncate]
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid

import numpy as np
import structlog
from faker import Faker

from app.core.config import settings
from app.core.database import SyncSessionLocal, sync_engine
from app.models.orm.ga4_events import Ga4Events
from app.models.orm.trackonomics_clicks import TrackonomicsClicks
from scripts.seeds.db_writer import DbWriter
from scripts.seeds.feature_store_builder import build_feature_store
from scripts.seeds.generators.braintree_subscriptions import (
    generate_braintree_subscriptions,
)
from scripts.seeds.generators.ga4_events import (
    generate_ga4_events,
    generate_ga4_identity_bridge,
)
from scripts.seeds.generators.openweb_engagement import generate_openweb_engagement
from scripts.seeds.generators.pushly_subscribers import generate_pushly_subscribers
from scripts.seeds.generators.sailthru_newsletter import generate_sailthru_newsletter
from scripts.seeds.generators.trackonomics_clicks import generate_trackonomics_clicks
from scripts.seeds.generators.transunion_demographics import (
    generate_transunion_demographics,
)
from scripts.seeds.generators.zephr_users import generate_zephr_users

logger = structlog.get_logger(__name__)


def run_pipeline(truncate: bool = False) -> None:
    """Execute the full synthetic data generation pipeline.

    Args:
        truncate: If True, truncate all 10 tables before seeding.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: On any database write failure.
    """
    sd = settings.synthetic_data
    schema = settings.database.schema
    t_start = time.monotonic()

    # One RNG instance, one Faker instance — both seeded deterministically.
    rng = np.random.default_rng(sd.random_seed)
    faker = Faker()
    Faker.seed(sd.random_seed)

    db_writer = DbWriter(SyncSessionLocal, sd.batch_size)

    logger.info(
        "pipeline.start",
        n_users=sd.n_users,
        random_seed=sd.random_seed,
        schema=schema,
        truncate=truncate,
    )

    # --- 0. Optional truncate ---
    if truncate:
        logger.info("pipeline.truncate.start")
        db_writer.truncate_all_tables(schema)
        logger.info("pipeline.truncate.done")

    # --- 1. ZephrUsers ---
    logger.info("pipeline.step", step=1, table="zephr_users")
    (
        zephr_rows,
        user_persona_map,
        user_emails,
        user_hashed_emails,
        user_account_age,
    ) = generate_zephr_users(rng, settings, faker)
    all_user_ids: list[uuid.UUID] = [
        u.user_id for u in zephr_rows  # type: ignore[attr-defined]
    ]
    db_writer.write_batch(zephr_rows, "zephr_users")

    # --- 2. GA4 events (chunked Core insert) ---
    logger.info("pipeline.step", step=2, table="ga4_events")
    n_ga4 = int(sd.n_users * sd.source_coverage.ga4)
    ga4_user_ids = rng.choice(
        all_user_ids,  # type: ignore[arg-type]
        size=min(n_ga4, len(all_user_ids)),
        replace=False,
    ).tolist()

    # user_pseudo_id_map built during event generation.
    user_pseudo_id_map: dict[uuid.UUID, str] = {}
    accumulated_first_last: dict[str, tuple] = {}

    for event_batch, first_last_update in generate_ga4_events(
        ga4_user_ids, user_persona_map, rng, settings
    ):
        db_writer.write_batch_core(Ga4Events, event_batch, "ga4_events")
        accumulated_first_last.update(first_last_update)

    # Build user_pseudo_id_map by re-reading from accumulated data.
    # (ga4_events generator embeds user_pseudo_id in each event row dict)
    # We need a reverse mapping: we can rebuild from the bridge query or
    # store it during generation. Since generate_ga4_events doesn't expose
    # the map directly, query the DB for the distinct mapping.
    from sqlalchemy import text as sa_text

    with sync_engine.connect() as conn:
        result = conn.execute(
            sa_text(
                f"SELECT DISTINCT user_id::text, user_pseudo_id "
                f"FROM {schema}.ga4_events WHERE user_id IS NOT NULL LIMIT {sd.n_users}"
            )
        )
        for row in result:
            uid = uuid.UUID(str(row[0]))
            user_pseudo_id_map[uid] = row[1]

    # --- 3. GA4 identity bridge ---
    logger.info("pipeline.step", step=3, table="ga4_identity_bridge")
    bridge_rows = generate_ga4_identity_bridge(
        ga4_user_ids, user_pseudo_id_map, accumulated_first_last
    )
    db_writer.write_batch(bridge_rows, "ga4_identity_bridge")

    # --- 4. Braintree subscriptions ---
    logger.info("pipeline.step", step=4, table="braintree_subscriptions")
    braintree_rows = generate_braintree_subscriptions(
        all_user_ids, user_persona_map, rng, settings, faker
    )
    db_writer.write_batch(braintree_rows, "braintree_subscriptions")

    # --- 5. Sailthru newsletter ---
    logger.info("pipeline.step", step=5, table="sailthru_newsletter")
    sailthru_rows = generate_sailthru_newsletter(
        all_user_ids, user_persona_map, user_emails, rng, settings
    )
    db_writer.write_batch(sailthru_rows, "sailthru_newsletter")

    # --- 6. Pushly subscribers ---
    logger.info("pipeline.step", step=6, table="pushly_subscribers")
    pushly_rows = generate_pushly_subscribers(
        all_user_ids, user_persona_map, user_account_age, rng, settings
    )
    db_writer.write_batch(pushly_rows, "pushly_subscribers")

    # --- 7. OpenWeb engagement (chunked ORM insert) ---
    logger.info("pipeline.step", step=7, table="openweb_engagement")
    for openweb_batch in generate_openweb_engagement(
        all_user_ids, user_persona_map, rng, settings
    ):
        db_writer.write_batch(openweb_batch, "openweb_engagement")

    # --- 8. Trackonomics clicks (chunked Core insert) ---
    logger.info("pipeline.step", step=8, table="trackonomics_clicks")
    for tc_batch in generate_trackonomics_clicks(
        all_user_ids, user_persona_map, rng, settings, faker
    ):
        db_writer.write_batch_core(TrackonomicsClicks, tc_batch, "trackonomics_clicks")

    # --- 9. Transunion demographics ---
    logger.info("pipeline.step", step=9, table="transunion_demographics")
    transunion_rows = generate_transunion_demographics(
        all_user_ids, user_persona_map, user_hashed_emails, rng, settings, faker
    )
    db_writer.write_batch(transunion_rows, "transunion_demographics")

    # --- 10. Feature store (SQL aggregation → ORM write) ---
    logger.info("pipeline.step", step=10, table="feature_store")
    build_feature_store(sync_engine, db_writer, settings, all_user_ids)

    elapsed = time.monotonic() - t_start
    logger.info("pipeline.done", elapsed_s=round(elapsed, 1))


def main() -> None:
    """Parse CLI arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for the Audience Intelligence Platform."
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate all 10 seed tables before generating new data.",
    )
    args = parser.parse_args()

    try:
        run_pipeline(truncate=args.truncate)
    except Exception as exc:
        logger.error("pipeline.fatal", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
