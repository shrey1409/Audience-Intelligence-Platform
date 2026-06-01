# Spec: Phase 03 — Synthetic Data

## Overview

This phase generates a deterministic, 100,000-user synthetic dataset that populates all 10 PostgreSQL
staging tables built in Phase 2. Each synthetic user is drawn from one of nine persona archetypes
defined in `configs/base.yaml`, and their source-system records are generated with persona-appropriate
feature distributions — ensuring that when the Phase 6 ML pipeline runs K-Means on the feature
matrix, it rediscovers the same nine cluster boundaries. The dataset is the development stand-in
for real publisher data across all ETL, feature engineering, ML training, and API phases.

The synthetic generator respects the real-world coverage rates of each source system: GA4 covers
95% of users, Braintree 10%, Sailthru 65%, Pushly 37%, OpenWeb 26%, Trackonomics 18%, and
Transunion 70% (at 0.70+ match_confidence). Records are written directly to PostgreSQL using
SQLAlchemy ORM bulk inserts, leaving the database in a state that every downstream phase can
immediately use without modification.

## Phase position

- Previous phase: 02 — Database Schema — complete
- This phase: 03 — Synthetic Data
- Next phase: 04 — ETL Ingestion

## Depends on

- Phase 2 complete: all 10 ORM models present and importable from `app/models/orm/`
- Phase 2 complete: `alembic upgrade head` run and all tables present in the PostgreSQL schema
- `configs/base.yaml` present with `ml.features.matrix` (46 features), `personas.labels` (9 labels),
  `cold_start.min_sessions_for_ml` (5), and `etl.transunion_min_confidence` (0.70)
- Docker Compose running: PostgreSQL accessible at the URL in `.env`
- `app/core/config.py` present and importable (Settings singleton, `settings.database.schema`)
- `app/core/database.py` present with sync engine factory for ETL/seed scripts

## System context

Data Platform — this phase lives entirely in the data platform layer. It uses the sync SQLAlchemy
engine (not async) because seed scripts are offline batch operations, not API request handlers.

## Database changes

No new tables or schema changes. All 10 tables are already defined by Phase 2:

| Table | Rows generated |
|-------|----------------|
| `{schema}.zephr_users` | 100,000 |
| `{schema}.ga4_events` | ~15,000,000 (~150 events per user × 95,000 GA4 users) |
| `{schema}.ga4_identity_bridge` | ~95,000 (one row per GA4 user, not one per event — maps user_pseudo_id → user_id) |
| `{schema}.braintree_subscriptions` | ~10,000 |
| `{schema}.sailthru_newsletter` | ~100,000 (~100% coverage) |
| `{schema}.pushly_subscribers` | ~37,000 |
| `{schema}.openweb_engagement` | ~26,000 |
| `{schema}.trackonomics_clicks` | ~500,000 (multiple clicks per commerce user, 16% user coverage) |
| `{schema}.transunion_demographics` | ~70,000 |
| `{schema}.feature_store` | 100,000 |

All SQL uses the `{schema}` placeholder pattern. The actual schema name comes from
`settings.database.schema` at runtime — never hardcoded.

## New API endpoints

No new API endpoints in this phase.

## ML changes

No new ML algorithms or MLflow experiments in this phase. The synthetic feature distributions are
designed to produce clearly separable clusters in Phase 6. Specifically:

- Each persona archetype has one or two dominant features with z-score > 2.0 relative to the
  global mean — this mirrors the `personas.naming_rules` lookup in `configs/base.yaml`.
- log1p-transformed features (`total_sessions`, `total_pageviews`, `total_affiliate_clicks`,
  `total_comments`) use log-normal distributions matching typical publisher analytics skew.
- All 46 features in `ml.features.matrix` are present in `feature_store` before any ML phase runs.

## Configuration changes

Add the following section to `configs/base.yaml` under a new top-level key `synthetic_data`:

```yaml
synthetic_data:
  n_users: 100000
  random_seed: 42
  batch_size: 5000
  persona_distribution:
    low_engager: 0.506
    casual_reader: 0.154
    sports_focused: 0.101
    celebrity_entertainment: 0.097
    social_engager: 0.077
    occasional_buyer: 0.029
    subscription_focused: 0.028
    loyalist: 0.011
    high_value_shopper: 0.006
  source_coverage:
    ga4: 0.95
    braintree: 0.10
    sailthru: 1.00
    pushly: 0.35
    openweb: 0.23
    trackonomics: 0.16
    transunion: 0.70
  transunion_high_confidence_ratio: 0.85
  ga4_events_per_user_mean: 150
  ga4_events_per_user_std: 50
```

No other config files change.

## Files to create

| File | Description | Key functions / classes |
|------|-------------|------------------------|
| `scripts/seeds/__init__.py` | Package marker | — |
| `scripts/seeds/persona_config.py` | Persona archetype definitions — feature mean/std per persona, coverage flags, per-persona source participation rates | `PersonaArchetype`, `PERSONA_ARCHETYPES`, `get_archetype` |
| `scripts/seeds/generators/__init__.py` | Package marker | — |
| `scripts/seeds/generators/zephr_users.py` | Generates 100,000 `ZephrUsers` ORM rows with persona-appropriate `account_age_days`, `email`, `has_subscription` base flag | `generate_zephr_users` |
| `scripts/seeds/generators/ga4_events.py` | Generates ~150 `Ga4Events` rows per user (across ~10–20 sessions distributed over 365 days) for 95% of users, plus one `Ga4IdentityBridge` row per GA4 user; session metrics drawn from persona distributions | `generate_ga4_events`, `generate_ga4_identity_bridge` |
| `scripts/seeds/generators/braintree_subscriptions.py` | Generates `BraintreeSubscriptions` rows for ~10% of users; Loyalist and Subscription-Focused archetypes have 90%+ participation | `generate_braintree_subscriptions` |
| `scripts/seeds/generators/sailthru_newsletter.py` | Generates `SailthruNewsletter` rows for 65% of users; newsletter flags drawn from persona affinity rules in `configs/base.yaml` | `generate_sailthru_newsletter` |
| `scripts/seeds/generators/pushly_subscribers.py` | Generates `PushlySubscribers` rows for 37% of users | `generate_pushly_subscribers` |
| `scripts/seeds/generators/openweb_engagement.py` | Generates `OpenwebEngagement` rows for 26% of users; Social Engager archetype has 85%+ participation with elevated comment counts | `generate_openweb_engagement` |
| `scripts/seeds/generators/trackonomics_clicks.py` | Generates `TrackonomicsClicks` rows for 18% of users; High-Value Shopper and Occasional Buyer archetypes have elevated participation | `generate_trackonomics_clicks` |
| `scripts/seeds/generators/transunion_demographics.py` | Generates `TransunionDemographics` rows for 70% of users; 85% of those have `match_confidence >= 0.70` | `generate_transunion_demographics` |
| `scripts/seeds/feature_store_builder.py` | Aggregates all per-source generated data into the 46-column ML feature matrix and writes `FeatureStore` rows; applies zero-imputation (F-08) for missing source records | `build_feature_store`, `apply_zero_imputation`, `compute_derived_features` |
| `scripts/seeds/db_writer.py` | Handles bulk inserts via SQLAlchemy sync session using `session.bulk_save_objects()` in configurable batch sizes; logs row counts per table | `DbWriter`, `write_batch`, `truncate_table` |
| `scripts/seeds/generate_synthetic_data.py` | CLI entry point; orchestrates full generation pipeline in insertion order; accepts `--truncate` flag to clear tables before seeding | `main`, `run_pipeline` |
| `scripts/validate_features.py` | Standalone validator that queries `feature_store` and asserts exactly 46 ML feature columns are non-null for at least 95% of rows; exits non-zero on failure | `validate_feature_coverage`, `main` |
| `data/synthetic/.gitkeep` | Ensures `data/synthetic/` directory is tracked; optional CSV exports land here | — |
| `tests/unit/test_synthetic_generators.py` | Unit tests for each generator function: correct row count, correct column types, no null user_ids, no hardcoded schema names, coverage rates within ±2% of config targets | `TestZephrGenerator`, `TestGa4Generator`, `TestFeatureStoreBuilder`, etc. |
| `tests/integration/test_synthetic_nulls.py` | Integration test verifying no NULL user_ids in any staging table after full seed run | `test_no_null_user_ids_zephr`, `test_no_null_user_ids_braintree`, `test_no_null_user_ids_all_tables` |

## Files to modify

| File | What changes and why |
|------|----------------------|
| `configs/base.yaml` | Add `synthetic_data` section (persona distribution, coverage rates, batch size, random seed) as specified in Configuration changes |

## New dependencies

Add to `requirements/dev.txt`:
- `Faker==24.9.0` — realistic email, UUID, date generation for synthetic users

`Faker` is a dev/seed dependency only — it is not needed in the production ETL or API. No changes
to `requirements/base.txt`.

## Implementation rules

**Universal rules (all phases):**
- All parameters read from `configs/base.yaml` via the `settings` object — never hardcode
  `n_users`, persona proportions, coverage rates, or thresholds directly in Python
- All SQL (if any raw SQL is used) must use the `{schema}` placeholder — never hardcode schema name
- All functions have type hints on every argument and return type
- No bare `except:` — catch `sqlalchemy.exc.SQLAlchemyError`, `ValueError`, `KeyError` specifically
- Structured logging via `structlog` on every function entry and exit: log user count, table name,
  rows written, elapsed time
- No real credentials, PII, or real email addresses in any generated data

**Synthetic data rules:**
- `random_seed: 42` (from `configs/base.yaml`) passed to `numpy.random.default_rng()` at the start of `generate_synthetic_data.py` — every generator receives this RNG instance, ensuring full reproducibility
- Same config + same seed → byte-identical output across runs on any machine
- Persona assignment is deterministic: assign personas to user indices in a fixed round-robin-weighted order before any random draws, so persona proportions are exact (not approximate)
- Feature distributions must produce silhouette score > 0.30 when K-Means with K=9 is run in Phase 6 — design distributions so dominant features per persona have mean separation ≥ 1.5 standard deviations from the global mean
- Zero-imputation rule (F-08): any user without a source record gets `0.0` (not `NULL`) for all features from that source in `feature_store`
- Coverage rates are exact to within ±1 user (not random sampling) — use `rng.choice` with `replace=False` to select exactly `int(n_users * coverage_rate)` users per source
- No foreign key violations: `zephr_users` inserted first; all other tables insert after
- Insertion order: `zephr_users` → `ga4_events` → `ga4_identity_bridge` → `braintree_subscriptions` → `sailthru_newsletter` → `pushly_subscribers` → `openweb_engagement` → `trackonomics_clicks` → `transunion_demographics` → `feature_store`
- `db_writer.py` uses batched bulk inserts (`batch_size` from config, default 5,000) — never load all 100,000 rows into memory at once

**Derived feature rules (in `feature_store_builder.py`):**
- `email_engagement_score`: ordinal 0/1/2 based on `email_engagement.low_threshold` and `high_threshold` from config (< 0.15 → 0, 0.15–0.35 → 1, > 0.35 → 2)
- `social_engagement_score`: `3 * total_comments + 1 * total_likes_given + 2 * total_shares` — formula from data-sources reference
- `conversion_rate`: `total_transactions / total_affiliate_clicks` when `total_affiliate_clicks > 0`, else `0.0`
- `avg_transaction_value`: `total_revenue_generated / total_transactions` when `total_transactions > 0`, else `0.0`
- `newsletter_count`: count of `True` values across the 6 nl_* binary flags
- `days_since_last_visit`: derived from `ga4_events.last_event_date` vs a fixed "today" reference date (2026-06-01) — always use the config-supplied reference date, never `datetime.now()`
- `account_age_days`: derived from `zephr_users.created_at` vs the same fixed reference date
- `days_until_renewal`: derived from `braintree_subscriptions.next_billing_date` vs reference date; zero-imputed for non-subscribers

## Definition of done

- [ ] All new Python files pass syntax check — verified by: `python3 -m py_compile scripts/seeds/generate_synthetic_data.py scripts/seeds/persona_config.py scripts/seeds/db_writer.py scripts/seeds/feature_store_builder.py scripts/validate_features.py`
- [ ] All generators pass syntax check — verified by: `python3 -m py_compile scripts/seeds/generators/zephr_users.py scripts/seeds/generators/ga4_events.py scripts/seeds/generators/braintree_subscriptions.py scripts/seeds/generators/sailthru_newsletter.py scripts/seeds/generators/pushly_subscribers.py scripts/seeds/generators/openweb_engagement.py scripts/seeds/generators/trackonomics_clicks.py scripts/seeds/generators/transunion_demographics.py`
- [ ] All new Python files pass pre-commit — verified by: `pre-commit run --all-files`
- [ ] All unit tests pass — verified by: `pytest tests/unit/test_synthetic_generators.py -v`
- [ ] No hardcoded values — verified by: `grep -rn "100000\|0\.95\|0\.65\|0\.37\|0\.26\|0\.18\|0\.70\|public\." scripts/seeds/ scripts/validate_features.py` (must return zero matches in implementation code)
- [ ] `configs/base.yaml` validates — verified by: `python3 -c "import yaml; yaml.safe_load(open('configs/base.yaml'))"`
- [ ] Seed script runs without error — verified by: `python3 scripts/seeds/generate_synthetic_data.py --truncate` (exits 0, no exceptions)
- [ ] `zephr_users` has exactly 100,000 rows — verified by: `docker exec -it aip_postgres psql -U aip_user -d audience_intelligence -c "SELECT COUNT(*) FROM public.zephr_users;"`
- [ ] `feature_store` has exactly 100,000 rows — verified by: `docker exec -it aip_postgres psql -U aip_user -d audience_intelligence -c "SELECT COUNT(*) FROM public.feature_store;"`
- [ ] Feature matrix has exactly 46 non-null columns for ≥ 95% of rows — verified by: `python3 scripts/validate_features.py`
- [ ] Coverage rates within ±2% of config targets — verified by: `pytest tests/unit/test_synthetic_generators.py::TestCoverageRates -v`
- [ ] Reproducibility check: two consecutive runs produce identical `feature_store` rows — verified by: `python3 scripts/seeds/generate_synthetic_data.py --truncate && python3 -c "import hashlib, pandas as pd; df=pd.read_sql(...); print(hashlib.md5(df.to_csv().encode()).hexdigest())"` (hashes match)
- [ ] All persona archetypes present in feature_store — verified by: `pytest tests/unit/test_synthetic_generators.py::TestPersonaDistribution -v`
- [ ] No NULL user_ids in any staging table — verified by: `pytest tests/integration/test_synthetic_nulls.py -v`

## Estimated effort

3–4 hours. The logic is repetitive across 8 source generators but each generator has unique feature
distributions. The `feature_store_builder.py` and the derived feature calculations are the
highest-complexity piece. Unit tests for 8 generators add significant but mechanical test volume.

## Risk flags

- **ORM model availability:** Phase 2 left ORM model files as empty `__init__.py` stubs. Before any
  generator imports ORM models, verify that `app/models/orm/zephr_users.py`, `feature_store.py`,
  etc. exist with actual class definitions. If they do not exist, implement them first (Phase 2
  regression) before writing any seed code.
- **Persona separability:** If feature distributions are too similar across archetypes, Phase 6
  K-Means will produce silhouette scores below the 0.30 threshold (`clustering.silhouette_threshold`
  in config) and the ML phase will fail. Validate separability by running a quick K-Means check
  immediately after seeding, before declaring this phase done.
- **Referential integrity ordering:** Inserting any staging table before `zephr_users` will cause
  FK constraint violations. The `run_pipeline` function must enforce insertion order strictly.
- **Memory pressure at 100K users:** Generating all 100,000 rows in-memory before writing will
  exhaust RAM on constrained machines. Use the configurable `batch_size` (5,000 rows) in
  `db_writer.py` to stream inserts. Never accumulate the full dataset in a single list.
- **test isolation — subprocess required:** As noted in CURRENT_STATUS.md, `importlib.reload()`
  does not work for schema override in tests. Integration tests that need a different schema must
  use subprocess isolation. Unit tests in `test_synthetic_generators.py` should mock the DB session
  and settings object directly rather than relying on environment variable overrides.
