"""Generator for the zephr_users staging table.

Returns all 100,000 ZephrUsers ORM objects plus auxiliary dicts used by
downstream generators. This must run first — all FK tables depend on it.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta

import numpy as np
import structlog
from faker import Faker

from app.core.config import Settings
from app.models.orm.zephr_users import ZephrUsers
from scripts.seeds.persona_config import (
    build_persona_array,
    get_archetype,
    normalized_weights,
)

logger = structlog.get_logger(__name__)

REFERENCE_DATE: date = date(2026, 6, 1)


def generate_zephr_users(
    rng: np.random.Generator,
    settings: Settings,
    faker: Faker,
) -> tuple[
    list[ZephrUsers],
    dict[uuid.UUID, str],
    dict[uuid.UUID, str],
    dict[uuid.UUID, str],
    dict[uuid.UUID, int],
]:
    """Generate all ZephrUsers rows and per-user metadata dicts.

    Args:
        rng: Seeded numpy RNG instance (shared across the pipeline).
        settings: Application settings (reads synthetic_data section).
        faker: Seeded Faker instance for realistic names and emails.

    Returns:
        Tuple of:
        - list[ZephrUsers]: All 100K ORM objects ready for bulk insert.
        - user_persona_map: {user_id → persona_name}
        - user_emails: {user_id → email} — for sailthru identity
        - user_hashed_emails: {user_id → hashed_email} — for transunion identity
        - user_account_age: {user_id → account_age_days} — for pushly opted_in_at
    """
    sd = settings.synthetic_data
    n = sd.n_users
    logger.info("zephr_users.generate.start", n_users=n)

    weights = normalized_weights(sd)
    persona_arr = build_persona_array(rng, n, weights)

    users: list[ZephrUsers] = []
    user_persona_map: dict[uuid.UUID, str] = {}
    user_emails: dict[uuid.UUID, str] = {}
    user_hashed_emails: dict[uuid.UUID, str] = {}
    user_account_age: dict[uuid.UUID, int] = {}

    seen_emails: set[str] = set()

    for i in range(n):
        persona_name = str(persona_arr[i])
        archetype = get_archetype(persona_name)
        uid = uuid.UUID(faker.uuid4())

        # account_age_days drawn from persona distribution, clipped to [1, 3650].
        age_days = int(
            np.clip(
                rng.normal(
                    archetype.account_age_days_mu, archetype.account_age_days_sigma
                ),
                1,
                3650,
            )
        )

        reg_date = REFERENCE_DATE - timedelta(days=age_days)
        registration_dt = datetime(reg_date.year, reg_date.month, reg_date.day, 0, 0, 0)

        # Generate unique email via faker with collision guard.
        email = faker.email().lower()
        attempts = 0
        while email in seen_emails:
            email = faker.email().lower()
            attempts += 1
            if attempts > 10:
                email = f"user_{uid.hex[:12]}@synthetic.aip"
        seen_emails.add(email)

        hashed = hashlib.sha256(email.encode()).hexdigest()

        user = ZephrUsers(
            user_id=uid,
            email=email,
            hashed_email=hashed,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            account_age_days=age_days,
            is_registered=True,
            registration_date=registration_dt,
            created_at=registration_dt,
            updated_at=registration_dt,
        )
        users.append(user)
        user_persona_map[uid] = persona_name
        user_emails[uid] = email
        user_hashed_emails[uid] = hashed
        user_account_age[uid] = age_days

    logger.info("zephr_users.generate.done", n_users=n)
    return users, user_persona_map, user_emails, user_hashed_emails, user_account_age
