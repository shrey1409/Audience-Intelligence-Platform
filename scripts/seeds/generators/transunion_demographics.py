"""Generator for transunion_demographics staging table.

Coverage: 70% of users. 85% of those have match_confidence >= 0.70 (high-confidence).
Low-confidence records get excluded=True; age/income/has_children remain NULL.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import structlog
from faker import Faker

from app.core.config import Settings
from app.models.orm.transunion_demographics import TransunionDemographics
from scripts.seeds.persona_config import get_archetype

logger = structlog.get_logger(__name__)

REFERENCE_DATE: date = date(2026, 6, 1)

_AGE_RANGES = [
    "age_18_24",
    "age_25_34",
    "age_35_44",
    "age_45_54",
    "age_55_64",
    "age_65_plus",
]
_INCOME_RANGES = [
    "lt_30k",
    "range_30_50k",
    "range_50_75k",
    "range_75_100k",
    "range_100_150k",
    "gt_150k",
]
_GENDERS = ["m", "f", "non_binary", "unknown"]
_HOME_OWNERSHIPS = ["owner", "renter", "unknown"]
_EDUCATIONS = ["high_school", "some_college", "bachelors", "graduate"]
_US_STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


def generate_transunion_demographics(
    all_user_ids: list[uuid.UUID],
    user_persona_map: dict[uuid.UUID, str],
    user_hashed_emails: dict[uuid.UUID, str],
    rng: np.random.Generator,
    settings: Settings,
    faker: Faker,
) -> list[TransunionDemographics]:
    """Generate TransunionDemographics rows for 70% of users.

    85% of selected users are high-confidence (match_confidence >= 0.70) and
    have age_range, income_range, has_children populated.
    15% are low-confidence (excluded=True) with those fields set to NULL.

    Args:
        all_user_ids: All 100K user IDs.
        user_persona_map: Maps user_id → persona name.
        user_hashed_emails: Maps user_id → SHA-256 hashed email.
        rng: Seeded numpy RNG.
        settings: Application settings.
        faker: Seeded Faker instance (for address fields).

    Returns:
        List of TransunionDemographics ORM objects.
    """
    sd = settings.synthetic_data
    n_transunion = int(sd.n_users * sd.source_coverage.transunion)
    high_conf_ratio = sd.transunion_high_confidence_ratio
    min_confidence = settings.etl.transunion_min_confidence
    logger.info("transunion.generate.start", target=n_transunion)

    selected = rng.choice(
        all_user_ids,  # type: ignore[arg-type]
        size=min(n_transunion, len(all_user_ids)),
        replace=False,
    ).tolist()

    n_high = int(round(n_transunion * high_conf_ratio))
    high_set = set(str(u) for u in selected[:n_high])

    rows: list[TransunionDemographics] = []
    match_date_base = REFERENCE_DATE

    for user_id in selected:
        persona = user_persona_map[user_id]
        archetype = get_archetype(persona)
        hashed_email = user_hashed_emails[user_id]

        is_high = str(user_id) in high_set

        if is_high:
            raw_conf = float(rng.uniform(min_confidence, 1.0))
        else:
            raw_conf = float(rng.uniform(0.30, min_confidence - 0.001))

        match_confidence = Decimal(str(round(raw_conf, 3)))
        excluded = not is_high

        days_ago = int(rng.integers(0, 91))
        match_date = match_date_base - timedelta(days=days_ago)

        if is_high:
            age_range: str | None = str(
                rng.choice(_AGE_RANGES, p=archetype.age_score_weights)
            )
            income_range: str | None = str(
                rng.choice(_INCOME_RANGES, p=archetype.income_score_weights)
            )
            # has_children: nullable Boolean — NULL means unknown.
            has_children_choice = rng.choice([True, False, None], p=[0.38, 0.50, 0.12])
            has_children: bool | None = (
                None if has_children_choice is None else bool(has_children_choice)
            )
            gender: str | None = str(rng.choice(_GENDERS, p=[0.46, 0.46, 0.04, 0.04]))
            home_ownership: str | None = str(
                rng.choice(_HOME_OWNERSHIPS, p=[0.55, 0.38, 0.07])
            )
            education: str | None = str(
                rng.choice(_EDUCATIONS, p=[0.20, 0.25, 0.38, 0.17])
            )
            address_state: str | None = str(rng.choice(_US_STATES))
            address_zip: str | None = faker.zipcode()
        else:
            age_range = None
            income_range = None
            has_children = None
            gender = None
            home_ownership = None
            education = None
            address_state = None
            address_zip = None

        rows.append(
            TransunionDemographics(
                demo_id=uuid.uuid4(),
                user_id=user_id,
                hashed_email=hashed_email,
                match_confidence=match_confidence,
                excluded=excluded,
                age_range=age_range,
                gender=gender,
                income_range=income_range,
                has_children=has_children,
                home_ownership=home_ownership,
                education=education,
                address_state=address_state,
                address_zip=address_zip,
                match_date=match_date,
            )
        )

    logger.info("transunion.generate.done", rows=len(rows))
    return rows
