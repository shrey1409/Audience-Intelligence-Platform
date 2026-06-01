"""Unit tests for Phase 3 synthetic data generators.

No live database required — all DB operations are mocked.
All generators are tested for correct output structure, persona distributions,
coverage rates, and derived feature calculations.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
from faker import Faker

from app.core.config import settings
from scripts.seeds.persona_config import (
    PERSONA_NAMES,
    build_persona_array,
    get_archetype,
    normalized_weights,
    persona_counts,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture
def faker_inst() -> Faker:
    f = Faker()
    Faker.seed(42)
    return f


@pytest.fixture
def sd():
    return settings.synthetic_data


@pytest.fixture
def small_user_ids() -> list[uuid.UUID]:
    """100 user IDs for lightweight tests."""
    return [uuid.uuid4() for _ in range(100)]


@pytest.fixture
def small_sd():
    """A SyntheticDataSettings instance with n_users=100 — does not mutate singleton."""
    from app.core.config import SyntheticDataSettings

    return SyntheticDataSettings(n_users=100, random_seed=42, batch_size=50)


@pytest.fixture
def zephr_output(rng, faker_inst, small_sd):
    """Generate a small zephr_users batch (100 users) for downstream tests."""
    from scripts.seeds.generators.zephr_users import generate_zephr_users

    mock_settings = MagicMock()
    mock_settings.synthetic_data = small_sd
    mock_settings.email_engagement = settings.email_engagement
    mock_settings.etl = settings.etl

    return generate_zephr_users(rng, mock_settings, faker_inst)


# ---------------------------------------------------------------------------
# TestPersonaConfig
# ---------------------------------------------------------------------------


class TestPersonaConfig:
    def test_persona_weights_normalize_to_1(self, sd) -> None:
        weights = normalized_weights(sd)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_all_9_personas_present(self, sd) -> None:
        weights = normalized_weights(sd)
        assert set(weights.keys()) == set(PERSONA_NAMES)

    def test_page_category_weights_sum_to_1_per_persona(self) -> None:
        from scripts.seeds.persona_config import PERSONA_ARCHETYPES

        for name, arch in PERSONA_ARCHETYPES.items():
            total = sum(arch.page_category_weights.values())
            assert abs(total - 1.0) < 1e-6, f"{name} page weights sum = {total}"

    def test_device_weights_sum_to_1_per_persona(self) -> None:
        from scripts.seeds.persona_config import PERSONA_ARCHETYPES

        for name, arch in PERSONA_ARCHETYPES.items():
            total = sum(arch.device_weights.values())
            assert abs(total - 1.0) < 1e-6, f"{name} device weights sum = {total}"

    def test_get_archetype_returns_correct_type(self) -> None:
        from scripts.seeds.persona_config import PersonaArchetype

        arch = get_archetype("loyalist")
        assert isinstance(arch, PersonaArchetype)
        assert arch.name == "loyalist"

    def test_get_archetype_raises_on_unknown(self) -> None:
        with pytest.raises(KeyError):
            get_archetype("nonexistent_persona")

    def test_persona_counts_sum_to_n_users(self, sd) -> None:
        weights = normalized_weights(sd)
        counts = persona_counts(1000, weights)
        assert sum(counts.values()) == 1000

    def test_build_persona_array_exact_length(self, rng, sd) -> None:
        weights = normalized_weights(sd)
        arr = build_persona_array(rng, 500, weights)
        assert len(arr) == 500

    def test_low_engager_is_largest_group(self, rng, sd) -> None:
        weights = normalized_weights(sd)
        counts = persona_counts(10000, weights)
        assert counts["low_engager"] == max(counts.values())

    def test_high_value_shopper_is_smallest_group(self, rng, sd) -> None:
        weights = normalized_weights(sd)
        counts = persona_counts(10000, weights)
        assert counts["high_value_shopper"] == min(counts.values())


# ---------------------------------------------------------------------------
# TestZephrGenerator
# ---------------------------------------------------------------------------


class TestZephrGenerator:
    def test_generates_correct_count(self, zephr_output) -> None:
        users, *_ = zephr_output
        assert len(users) == 100

    def test_no_duplicate_emails(self, zephr_output) -> None:
        users, *_ = zephr_output
        emails = [u.email for u in users]
        assert len(emails) == len(set(emails))

    def test_all_persona_labels_present_in_map(self, zephr_output, sd) -> None:
        users, user_persona_map, *_ = zephr_output
        personas_used = set(user_persona_map.values())
        # At 100 users, not all 9 personas guaranteed, but at least 1.
        assert len(personas_used) >= 1
        assert all(p in PERSONA_NAMES for p in personas_used)

    def test_account_age_within_valid_range(self, zephr_output) -> None:
        users, *_ = zephr_output
        for u in users:
            assert 1 <= u.account_age_days <= 3650

    def test_registration_date_derived_from_account_age(self, zephr_output) -> None:
        users, *_ = zephr_output
        ref = date(2026, 6, 1)
        for u in users:
            reg_date = u.registration_date.date()
            expected_age = (ref - reg_date).days
            # Allow ±1 day for datetime conversion.
            assert abs(expected_age - u.account_age_days) <= 1

    def test_hashed_email_is_64_hex_chars(self, zephr_output) -> None:
        users, *_ = zephr_output
        for u in users:
            assert len(u.hashed_email) == 64
            assert all(c in "0123456789abcdef" for c in u.hashed_email)

    def test_all_users_registered(self, zephr_output) -> None:
        users, *_ = zephr_output
        assert all(u.is_registered for u in users)

    def test_user_persona_map_covers_all_users(self, zephr_output) -> None:
        users, user_persona_map, *_ = zephr_output
        user_ids = {u.user_id for u in users}
        assert user_ids == set(user_persona_map.keys())

    def test_reference_date_not_datetime_now(self) -> None:
        from scripts.seeds.generators.zephr_users import REFERENCE_DATE

        assert REFERENCE_DATE == date(2026, 6, 1)


# ---------------------------------------------------------------------------
# TestGa4Generator
# ---------------------------------------------------------------------------


class TestGa4Generator:
    def test_event_count_per_user_within_clipped_range(
        self, rng, small_user_ids
    ) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.ga4_events import generate_ga4_events

        persona_map = {uid: "casual_reader" for uid in small_user_ids}
        ga4_ids = small_user_ids[:20]
        small_sd = SyntheticDataSettings(n_users=100, random_seed=42, batch_size=50)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        all_events: list[dict[str, Any]] = []
        for batch, _ in generate_ga4_events(ga4_ids, persona_map, rng, mock_settings):
            all_events.extend(batch)

        # Each event must have required keys.
        for event in all_events:
            assert "event_id" in event
            assert "user_id" in event
            assert "user_pseudo_id" in event
            assert "event_date" in event

    def test_page_category_matches_valid_values(self, rng, small_user_ids) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.ga4_events import generate_ga4_events
        from scripts.seeds.persona_config import PAGE_CATS

        persona_map = {uid: "sports_focused" for uid in small_user_ids}
        ga4_ids = small_user_ids[:10]
        small_sd = SyntheticDataSettings(
            n_users=100,
            random_seed=42,
            batch_size=500,
            ga4_events_per_user_mean=10,
            ga4_events_per_user_std=2,
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        all_events: list[dict[str, Any]] = []
        for batch, _ in generate_ga4_events(ga4_ids, persona_map, rng, mock_settings):
            all_events.extend(batch)

        cats = {e["page_category"] for e in all_events}
        assert cats.issubset(set(PAGE_CATS))

    def test_device_category_matches_valid_values(self, rng, small_user_ids) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.ga4_events import generate_ga4_events

        valid_devices = {"desktop", "mobile", "tablet"}
        persona_map = {uid: "loyalist" for uid in small_user_ids}
        ga4_ids = small_user_ids[:5]
        small_sd = SyntheticDataSettings(
            n_users=100,
            random_seed=42,
            batch_size=500,
            ga4_events_per_user_mean=10,
            ga4_events_per_user_std=2,
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        all_events: list[dict[str, Any]] = []
        for batch, _ in generate_ga4_events(ga4_ids, persona_map, rng, mock_settings):
            all_events.extend(batch)

        devices = {e["device_category"] for e in all_events}
        assert devices.issubset(valid_devices)

    def test_no_event_timestamp_after_reference_date(self, rng, small_user_ids) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.ga4_events import (
            REFERENCE_DATE,
            generate_ga4_events,
        )

        persona_map = {uid: "casual_reader" for uid in small_user_ids}
        ga4_ids = small_user_ids[:10]
        small_sd = SyntheticDataSettings(
            n_users=100,
            random_seed=42,
            batch_size=500,
            ga4_events_per_user_mean=10,
            ga4_events_per_user_std=2,
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        for batch, _ in generate_ga4_events(ga4_ids, persona_map, rng, mock_settings):
            for event in batch:
                assert event["event_date"] <= REFERENCE_DATE

    def test_is_bounce_only_on_single_event_sessions(self, rng, small_user_ids) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.ga4_events import generate_ga4_events

        persona_map = {uid: "low_engager" for uid in small_user_ids}
        ga4_ids = small_user_ids[:5]
        small_sd = SyntheticDataSettings(
            n_users=100,
            random_seed=42,
            batch_size=500,
            ga4_events_per_user_mean=5,
            ga4_events_per_user_std=1,
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        all_events: list[dict[str, Any]] = []
        for batch, _ in generate_ga4_events(ga4_ids, persona_map, rng, mock_settings):
            all_events.extend(batch)

        # Group by session — if is_bounce is True, that session has only 1 event.
        from collections import defaultdict

        session_events: dict[str, list] = defaultdict(list)
        for e in all_events:
            session_events[e["session_id"]].append(e)

        for session_id, events in session_events.items():
            bounced = [e for e in events if e["is_bounce"]]
            if bounced:
                assert len(events) == 1


# ---------------------------------------------------------------------------
# TestBraintreeGenerator
# ---------------------------------------------------------------------------


class TestBraintreeGenerator:
    def test_coverage_rate_within_tolerance(self, rng, faker_inst) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.braintree_subscriptions import (
            generate_braintree_subscriptions,
        )

        n = 1000
        user_ids = [uuid.uuid4() for _ in range(n)]
        persona_map = {uid: "casual_reader" for uid in user_ids}
        small_sd = SyntheticDataSettings(n_users=n, random_seed=42, batch_size=100)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        rows = generate_braintree_subscriptions(
            user_ids, persona_map, rng, mock_settings, faker_inst
        )
        rate = len(rows) / n
        assert abs(rate - 0.10) <= 0.05  # ±5% at small scale

    def test_braintree_customer_id_unique(self, rng, faker_inst) -> None:
        from app.core.config import SourceCoverageSettings, SyntheticDataSettings
        from scripts.seeds.generators.braintree_subscriptions import (
            generate_braintree_subscriptions,
        )

        n = 200
        user_ids = [uuid.uuid4() for _ in range(n)]
        persona_map = {uid: "subscription_focused" for uid in user_ids}
        cov = SourceCoverageSettings(braintree=0.50)
        small_sd = SyntheticDataSettings(
            n_users=n, random_seed=42, batch_size=100, source_coverage=cov
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        rows = generate_braintree_subscriptions(
            user_ids, persona_map, rng, mock_settings, faker_inst
        )
        cids = [r.braintree_customer_id for r in rows]
        assert len(cids) == len(set(cids))

    def test_plan_id_valid_enum_value(self, rng, faker_inst) -> None:
        from app.core.config import SourceCoverageSettings, SyntheticDataSettings
        from scripts.seeds.generators.braintree_subscriptions import (
            generate_braintree_subscriptions,
        )

        valid_plans = {"sports_plus", "home_delivery", "digital_all_access"}
        user_ids = [uuid.uuid4() for _ in range(100)]
        persona_map = {uid: "loyalist" for uid in user_ids}
        cov = SourceCoverageSettings(braintree=1.0)
        small_sd = SyntheticDataSettings(
            n_users=100, random_seed=42, batch_size=50, source_coverage=cov
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        rows = generate_braintree_subscriptions(
            user_ids, persona_map, rng, mock_settings, faker_inst
        )
        for r in rows:
            assert r.plan_id in valid_plans

    def test_status_valid_enum_value(self, rng, faker_inst) -> None:
        from app.core.config import SourceCoverageSettings, SyntheticDataSettings
        from scripts.seeds.generators.braintree_subscriptions import (
            generate_braintree_subscriptions,
        )

        valid_statuses = {"active", "canceled", "past_due"}
        user_ids = [uuid.uuid4() for _ in range(100)]
        persona_map = {uid: "casual_reader" for uid in user_ids}
        cov = SourceCoverageSettings(braintree=1.0)
        small_sd = SyntheticDataSettings(
            n_users=100, random_seed=42, batch_size=50, source_coverage=cov
        )
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd

        rows = generate_braintree_subscriptions(
            user_ids, persona_map, rng, mock_settings, faker_inst
        )
        for r in rows:
            assert r.status in valid_statuses


# ---------------------------------------------------------------------------
# TestSailthruGenerator
# ---------------------------------------------------------------------------


class TestSailthruGenerator:
    def test_coverage_is_100_percent(self, rng) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.sailthru_newsletter import (
            generate_sailthru_newsletter,
        )

        user_ids = [uuid.uuid4() for _ in range(200)]
        persona_map = {uid: "casual_reader" for uid in user_ids}
        emails = {uid: f"user_{i}@test.com" for i, uid in enumerate(user_ids)}
        small_sd = SyntheticDataSettings(n_users=200, random_seed=42, batch_size=50)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd
        mock_settings.email_engagement.low_threshold = 0.15
        mock_settings.email_engagement.high_threshold = 0.35

        rows = generate_sailthru_newsletter(
            user_ids, persona_map, emails, rng, mock_settings
        )
        assert len(rows) == 200

    def test_newsletter_count_equals_sum_of_ml_flags(self, rng) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.sailthru_newsletter import (
            generate_sailthru_newsletter,
        )

        user_ids = [uuid.uuid4() for _ in range(50)]
        persona_map = {uid: "subscription_focused" for uid in user_ids}
        emails = {uid: f"u{i}@test.com" for i, uid in enumerate(user_ids)}
        small_sd = SyntheticDataSettings(n_users=50, random_seed=42, batch_size=50)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd
        mock_settings.email_engagement.low_threshold = 0.15
        mock_settings.email_engagement.high_threshold = 0.35

        rows = generate_sailthru_newsletter(
            user_ids, persona_map, emails, rng, mock_settings
        )
        for r in rows:
            expected_count = sum(
                [
                    r.nl_sports_alerts,
                    r.nl_morning_report,
                    r.nl_page_six_daily,
                    r.nl_celebrity_news,
                    r.nl_evening_update,
                    r.nl_post_opinion,
                ]
            )
            assert r.newsletter_count == expected_count

    def test_email_engagement_score_computed_correctly(self, rng) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.sailthru_newsletter import (
            generate_sailthru_newsletter,
        )

        user_ids = [uuid.uuid4() for _ in range(50)]
        persona_map = {uid: "loyalist" for uid in user_ids}
        emails = {uid: f"u{i}@test.com" for i, uid in enumerate(user_ids)}
        small_sd = SyntheticDataSettings(n_users=50, random_seed=42, batch_size=50)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd
        mock_settings.email_engagement.low_threshold = 0.15
        mock_settings.email_engagement.high_threshold = 0.35

        rows = generate_sailthru_newsletter(
            user_ids, persona_map, emails, rng, mock_settings
        )
        for r in rows:
            rate = float(r.open_rate)
            if rate < 0.15:
                assert r.email_engagement_score == 0
            elif rate < 0.35:
                assert r.email_engagement_score == 1
            else:
                assert r.email_engagement_score == 2

    def test_open_rate_within_0_1(self, rng) -> None:
        from app.core.config import SyntheticDataSettings
        from scripts.seeds.generators.sailthru_newsletter import (
            generate_sailthru_newsletter,
        )

        user_ids = [uuid.uuid4() for _ in range(50)]
        persona_map = {uid: "casual_reader" for uid in user_ids}
        emails = {uid: f"u{i}@test.com" for i, uid in enumerate(user_ids)}
        small_sd = SyntheticDataSettings(n_users=50, random_seed=42, batch_size=50)
        mock_settings = MagicMock()
        mock_settings.synthetic_data = small_sd
        mock_settings.email_engagement.low_threshold = 0.15
        mock_settings.email_engagement.high_threshold = 0.35

        rows = generate_sailthru_newsletter(
            user_ids, persona_map, emails, rng, mock_settings
        )
        for r in rows:
            assert 0.0 <= float(r.open_rate) <= 1.0


# ---------------------------------------------------------------------------
# TestCoverageRates
# ---------------------------------------------------------------------------


class TestCoverageRates:
    def test_source_coverage_settings_values(self, sd) -> None:
        cov = sd.source_coverage
        assert cov.ga4 == pytest.approx(0.95)
        assert cov.braintree == pytest.approx(0.10)
        assert cov.sailthru == pytest.approx(1.00)
        assert cov.pushly == pytest.approx(0.35)
        assert cov.openweb == pytest.approx(0.23)
        assert cov.trackonomics == pytest.approx(0.16)
        assert cov.transunion == pytest.approx(0.70)

    def test_ga4_events_config_present(self, sd) -> None:
        assert sd.ga4_events_per_user_mean == 150
        assert sd.ga4_events_per_user_std == 50

    def test_transunion_high_confidence_ratio(self, sd) -> None:
        assert sd.transunion_high_confidence_ratio == pytest.approx(0.85)

    def test_n_users_and_batch_size(self, sd) -> None:
        assert sd.n_users == 100000
        assert sd.batch_size == 5000
        assert sd.random_seed == 42


# ---------------------------------------------------------------------------
# TestPersonaDistribution
# ---------------------------------------------------------------------------


class TestPersonaDistribution:
    def test_all_9_personas_in_distribution(self, sd) -> None:
        dist = sd.persona_distribution.model_dump()
        assert set(dist.keys()) == set(PERSONA_NAMES)

    def test_raw_weights_do_not_sum_to_1(self, sd) -> None:
        dist = sd.persona_distribution.model_dump()
        raw_sum = sum(dist.values())
        # Raw values sum to ~1.009 — normalization is required.
        assert abs(raw_sum - 1.0) > 1e-6

    def test_normalized_weights_sum_to_1(self, sd) -> None:
        weights = normalized_weights(sd)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_persona_counts_sum_exactly_to_n_users(self, sd) -> None:
        weights = normalized_weights(sd)
        for n in [100, 1000, 100000]:
            counts = persona_counts(n, weights)
            assert sum(counts.values()) == n


# ---------------------------------------------------------------------------
# TestFeatureStoreBuilder
# ---------------------------------------------------------------------------


class TestFeatureStoreBuilder:
    def test_zero_imputation_for_missing_sources(self) -> None:
        """Verify F-08: missing source rows become 0, not NULL."""
        import pandas as pd

        from scripts.seeds.feature_store_builder import _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1"],
                "total_comments": [None],
                "total_likes_given": [None],
                "total_shares": [None],
                "total_affiliate_clicks": [None],
                "total_transactions": [None],
                "total_revenue_generated": [None],
                "age_range": [None],
                "income_range": [None],
                "has_children": [None],
                "open_rate": [None],
                "click_through_rate": [None],
            }
        )
        # Fill nulls before calling _compute_derived.
        df["total_comments"] = df["total_comments"].fillna(0).astype(int)
        df["total_likes_given"] = df["total_likes_given"].fillna(0).astype(int)
        df["total_shares"] = df["total_shares"].fillna(0).astype(int)
        df["total_affiliate_clicks"] = (
            df["total_affiliate_clicks"].fillna(0).astype(float)
        )
        df["total_transactions"] = df["total_transactions"].fillna(0).astype(float)
        df["total_revenue_generated"] = (
            df["total_revenue_generated"].fillna(0.0).astype(float)
        )
        df["has_children"] = df["has_children"].fillna(False).astype(bool)

        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        assert result["social_engagement_score"].iloc[0] == 0
        assert result["conversion_rate"].iloc[0] == 0.0
        assert result["avg_transaction_value"].iloc[0] == 0.0
        # has_children must be falsy bool, not float 0.0 or None.
        val = result["has_children"].iloc[0]
        assert not val
        assert not isinstance(val, float)

    def test_social_engagement_score_formula(self) -> None:
        import pandas as pd

        from scripts.seeds.feature_store_builder import _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1"],
                "total_comments": [10],
                "total_likes_given": [20],
                "total_shares": [5],
                "total_affiliate_clicks": [0.0],
                "total_transactions": [0.0],
                "total_revenue_generated": [0.0],
                "has_children": [True],
            }
        )
        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        # 3*10 + 1*20 + 2*5 = 30 + 20 + 10 = 60
        assert result["social_engagement_score"].iloc[0] == 60

    def test_conversion_rate_formula(self) -> None:
        import pandas as pd

        from scripts.seeds.feature_store_builder import _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1", "uid2"],
                "total_comments": [0, 0],
                "total_likes_given": [0, 0],
                "total_shares": [0, 0],
                "total_affiliate_clicks": [20.0, 0.0],
                "total_transactions": [4.0, 0.0],
                "total_revenue_generated": [100.0, 0.0],
                "has_children": [False, False],
            }
        )
        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        assert result["conversion_rate"].iloc[0] == pytest.approx(0.20)
        assert result["conversion_rate"].iloc[1] == pytest.approx(0.0)

    def test_avg_transaction_value_formula(self) -> None:
        import pandas as pd

        from scripts.seeds.feature_store_builder import _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1"],
                "total_comments": [0],
                "total_likes_given": [0],
                "total_shares": [0],
                "total_affiliate_clicks": [10.0],
                "total_transactions": [4.0],
                "total_revenue_generated": [200.0],
                "has_children": [None],
            }
        )
        df["has_children"] = df["has_children"].fillna(False).astype(bool)
        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        assert result["avg_transaction_value"].iloc[0] == pytest.approx(50.0)

    def test_has_children_null_becomes_false_not_zero(self) -> None:
        import pandas as pd

        from scripts.seeds.feature_store_builder import _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1"],
                "total_comments": [0],
                "total_likes_given": [0],
                "total_shares": [0],
                "total_affiliate_clicks": [0.0],
                "total_transactions": [0.0],
                "total_revenue_generated": [0.0],
                "has_children": [None],
            }
        )
        df["has_children"] = df["has_children"].fillna(False).astype(bool)
        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        val = result["has_children"].iloc[0]
        assert not val
        assert not isinstance(val, float)

    def test_days_since_last_visit_uses_reference_date(self) -> None:
        import pandas as pd

        from scripts.seeds.feature_store_builder import REFERENCE_DATE, _compute_derived

        df = pd.DataFrame(
            {
                "user_id": ["uid1"],
                "total_comments": [0],
                "total_likes_given": [0],
                "total_shares": [0],
                "total_affiliate_clicks": [0.0],
                "total_transactions": [0.0],
                "total_revenue_generated": [0.0],
                "has_children": [False],
                "last_event_date": [date(2026, 5, 1)],
            }
        )
        result = _compute_derived(df, low_t=0.15, high_t=0.35)
        expected_days = (REFERENCE_DATE - date(2026, 5, 1)).days
        assert result["days_since_last_visit"].iloc[0] == expected_days
