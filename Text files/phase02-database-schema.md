# Spec: Phase 02 — Database Schema

## Overview

Phase 02 builds the complete PostgreSQL database foundation for the Audience Intelligence Platform. It delivers 10 staging tables (9 source tables + the GA4 identity bridge), all SQLAlchemy 2.0 ORM models, a schema-aware Alembic migration system, Docker Compose infrastructure for local development (postgres + redis), and the full application configuration layer (`app/core/config.py`, `app/core/database.py`, `app/core/logging.py`, `app/core/security.py`). Every subsequent phase writes to, reads from, or depends on at least one artifact produced here. Nothing in phases 03–09 can begin until these tables exist and Alembic can migrate a clean PostgreSQL schema to head.

Phase 02 sits between Phase 01 (environment setup — complete) and Phase 03 (synthetic data generation — pending). Phase 01 delivered the project scaffold, configs, requirements, and pre-commit hooks. Phase 02 consumes `configs/base.yaml` for schema configuration and uses `requirements/base.txt` (with the added `asyncpg==0.29.0`) to implement the dual-engine database layer. Phase 03 will read the ORM models created here to seed 100K synthetic users across all 10 tables with correct referential integrity. The ETL pipeline (Phase 06) writes source-system data into the staging tables defined here. The feature builder (Phase 07) reads those tables via the sync SQLAlchemy engine. The API (Phase 08) writes back via the async engine.

## Phase position

- Previous phase: 01 — Environment Setup — **COMPLETE** (scaffold, configs, requirements, pre-commit)
- This phase: **02 — Database Schema**
- Next phase: 03 — Synthetic Data Generation

## Depends on

- `configs/base.yaml` — must exist; `database.schema`, `database.pool_size`, `redis.ttl_seconds` read at import time
- `configs/clients/example.yaml` — must exist; validated in `test_config.py`
- `requirements/base.txt` — must contain `asyncpg==0.29.0` (blocking pre-implementation task; add before writing any code)
- `requirements/base.txt` — must contain `sqlalchemy==2.0.30`, `alembic==1.13.1`, `psycopg2-binary==2.9.9`, `pydantic-settings==2.2.1`, `pyyaml==6.0.1`, `structlog==24.1.0`, `redis==5.0.4`
- `pyproject.toml` — must exist; black/isort/mypy/pytest config loaded by pre-commit and CI
- Docker must be installed and running (Phase 02 integration tests require `docker compose up -d postgres`)
- No prior phase deliverable files are required beyond what Phase 01 committed

## System context

**Data Platform** — this phase creates the PostgreSQL staging layer that is the first storage tier of the Data Platform. All ETL ingestion (Phase 06) writes to these tables. The feature engineering pipeline (Phase 07) reads from these tables. The ML output is written back to `feature_store` (Phase 09). This phase also creates the core application configuration and database connection infrastructure shared by all three systems (Data Platform, ML Platform, Serving Platform).

## Database changes

**10 new tables** in `{schema}` (default: `public`). All DDL uses `{schema}` placeholder. Build and FK dependency order:

| # | Table | Source | Coverage | Refresh |
|---|-------|--------|----------|---------|
| 1 | `zephr_users` | Zephr | 100% | incremental |
| 2 | `ga4_events` | GA4 | ~60% resolved | incremental |
| 3 | `ga4_identity_bridge` | Derived | ~60% | incremental |
| 4 | `braintree_subscriptions` | Braintree | ~10% | incremental |
| 5 | `sailthru_newsletter` | Sailthru | ~100% | full_refresh |
| 6 | `pushly_subscribers` | Pushly | ~35% | incremental |
| 7 | `openweb_engagement` | OpenWeb | ~23% | incremental |
| 8 | `trackonomics_clicks` | Trackonomics | ~16% | incremental |
| 9 | `transunion_demographics` | Transunion | ~70% | full_refresh |
| 10 | `feature_store` | Computed | 100% | weekly upsert |

All FK constraints reference `{schema}.zephr_users(user_id)`. The `feature_store` table has no FK constraint (denormalised ML output table). See `.claude/specs/database-schema-spec.md` Section 3 for complete column-by-column DDL specification including all CHECK constraints, index definitions, and nullability rules.

`feature_store` has **64 columns**: 1 UUID PK + 3 audit/status + 46 ML features + 4 extra nl_* metadata flags (not in ML matrix) + 10 ML output columns.

## New API endpoints

No new API endpoints in this phase. `app/core/security.py` implements the `APIKeyMiddleware` class used by Phase 08, but no FastAPI app or routes are wired up in Phase 02.

## ML changes

No ML changes in this phase. `feature_store` table is created with all 64 columns ready to receive ML output from Phase 09, but no ML code runs in Phase 02.

## Configuration changes

No new keys in `configs/base.yaml`. All configuration needed by Phase 02 already exists:
- `database.schema` — PostgreSQL schema name (default: `"public"`)
- `database.pool_size` — 10
- `database.max_overflow` — 20
- `database.pool_timeout` — 30
- `database.echo` — false
- `redis.ttl_seconds` — 604800
- `redis.max_connections` — 50

Required environment variables (go in `.env`, never YAML):
- `DATABASE__URL` — `postgresql://aip_user:<password>@localhost:5432/audience_intelligence`
- `REDIS__URL` — `redis://localhost:6379/0`
- `MLFLOW__TRACKING_URI` — `http://localhost:5000` (not used in Phase 02 but required by Settings validation)
- `API__API_KEYS` — `["dev-api-key-001"]`
- `API__ADMIN_API_KEY` — `dev-admin-key-001`
- `POSTGRES_PASSWORD` — any local dev password matching `DATABASE__URL`

## Files to create

| # | Path | Description | Key classes/functions |
|---|------|-------------|----------------------|
| 1 | `requirements/base.txt` | **Modify** — append `asyncpg==0.29.0` | n/a |
| 2 | `docker/postgres/init/01_create_databases.sql` | Creates `mlflow` and `airflow` databases on first postgres start | n/a |
| 3 | `docker-compose.yml` | Phase 02 minimal: postgres + redis services only | n/a |
| 4 | `.env.example` | Template environment file with all required variables and safe placeholder values | n/a |
| 5 | `app/core/config.py` | Pydantic-settings Settings class; YAML deep-merge loader; module-level singleton | `Settings`, `_deep_merge`, `_load_and_merge_yaml`, `settings` |
| 6 | `app/core/database.py` | Async engine (FastAPI) + sync engine (ETL/ML/Alembic); `get_db` dependency | `async_engine`, `AsyncSessionLocal`, `sync_engine`, `SyncSessionLocal`, `get_db` |
| 7 | `app/core/logging.py` | structlog configuration; single `configure_logging()` function | `configure_logging` |
| 8 | `app/core/security.py` | API key middleware; validates `X-API-Key` header on every request | `APIKeyMiddleware` |
| 9 | `app/models/orm/base.py` | SQLAlchemy `DeclarativeBase` subclass | `Base` |
| 10 | `app/models/orm/enums.py` | 14 Python Enum classes for all enumerated column types | `DeviceCategory`, `PageCategory`, `SubscriptionPlan`, `SubscriptionStatus`, `PaymentMethod`, `EmailEngagementTier`, `PushPlatform`, `ProductCategory`, `AgeRange`, `Gender`, `IncomeRange`, `HomeOwnership`, `Education`, `AlgorithmUsed` |
| 11 | `app/models/orm/zephr_users.py` | ORM model for `zephr_users` (PK table) | `ZephrUsers` |
| 12 | `app/models/orm/ga4_events.py` | ORM model for `ga4_events` | `Ga4Events` |
| 13 | `app/models/orm/ga4_identity_bridge.py` | ORM model for `ga4_identity_bridge` | `Ga4IdentityBridge` |
| 14 | `app/models/orm/braintree_subscriptions.py` | ORM model for `braintree_subscriptions` | `BraintreeSubscriptions` |
| 15 | `app/models/orm/sailthru_newsletter.py` | ORM model for `sailthru_newsletter` (22 columns) | `SailthruNewsletter` |
| 16 | `app/models/orm/pushly_subscribers.py` | ORM model for `pushly_subscribers` | `PushlySubscribers` |
| 17 | `app/models/orm/openweb_engagement.py` | ORM model for `openweb_engagement` | `OpenwebEngagement` |
| 18 | `app/models/orm/trackonomics_clicks.py` | ORM model for `trackonomics_clicks` | `TrackonomicsClicks` |
| 19 | `app/models/orm/transunion_demographics.py` | ORM model for `transunion_demographics` | `TransunionDemographics` |
| 20 | `app/models/orm/feature_store.py` | ORM model for `feature_store` — 64 columns, every one explicit | `FeatureStore` |
| 21 | `app/models/orm/__init__.py` | Imports all 10 ORM models to register with `Base.metadata`; exposes `__all__` | n/a |
| 22 | `alembic.ini` | Alembic config; no `sqlalchemy.url` (injected at runtime); file_template with date prefix | n/a |
| 23 | `alembic/env.py` | Schema-aware env.py: `include_schemas=True`, `include_object` filter, `version_table_schema` | `include_object`, `run_migrations_online`, `run_migrations_offline` |
| 24 | `alembic/versions/` | Empty directory (placeholder for migration files) | n/a |
| 25 | `scripts/run_migrations.py` | `CREATE SCHEMA IF NOT EXISTS` + `alembic upgrade head`; callable as `python scripts/run_migrations.py` | `run_migrations` |
| 26 | `sql/ddl/001_create_zephr_users.sql` | Human-readable DDL reference for `zephr_users` with `{schema}` placeholder | n/a |
| 27 | `sql/ddl/002_create_ga4_events.sql` | Human-readable DDL reference for `ga4_events` | n/a |
| 28 | `sql/ddl/003_create_ga4_identity_bridge.sql` | Human-readable DDL reference for `ga4_identity_bridge` | n/a |
| 29 | `sql/ddl/004_create_braintree_subscriptions.sql` | Human-readable DDL reference | n/a |
| 30 | `sql/ddl/005_create_sailthru_newsletter.sql` | Human-readable DDL reference | n/a |
| 31 | `sql/ddl/006_create_pushly_subscribers.sql` | Human-readable DDL reference | n/a |
| 32 | `sql/ddl/007_create_openweb_engagement.sql` | Human-readable DDL reference | n/a |
| 33 | `sql/ddl/008_create_trackonomics_clicks.sql` | Human-readable DDL reference | n/a |
| 34 | `sql/ddl/009_create_transunion_demographics.sql` | Human-readable DDL reference | n/a |
| 35 | `sql/ddl/010_create_feature_store.sql` | Human-readable DDL reference for `feature_store` (64 columns) | n/a |
| 36 | `tests/unit/test_config.py` | 6 unit tests for Settings loading, YAML merge, validation errors, feature count, weight sums | n/a |
| 37 | `tests/unit/test_models.py` | 4 unit tests for ORM model instantiation, UUID generation, schema injection, column count | n/a |
| 38 | `tests/integration/test_migrations.py` | 6 integration tests for migration execution, table creation, FK constraints, downgrade | n/a |

**Total: 38 files** (37 new + 1 modified)

## Files to modify

| Path | What changes | Why |
|------|-------------|-----|
| `requirements/base.txt` | Append `asyncpg==0.29.0` after `psycopg2-binary==2.9.9` line | Required by `create_async_engine` in `app/core/database.py`; without it FastAPI async DB path fails at import |
| `app/models/orm/__init__.py` | Replace empty `__init__.py` with imports of all 10 ORM models | All models must be imported before `Base.metadata` is used by Alembic `env.py` |

## New dependencies

- `asyncpg==0.29.0` — add to `requirements/base.txt` — required for `create_async_engine` with `postgresql+asyncpg://` DSN

No other new packages. All other required packages (`sqlalchemy`, `alembic`, `psycopg2-binary`, `pydantic-settings`, `pyyaml`, `structlog`, `redis`) are already in `requirements/base.txt`.

## Implementation rules

### Universal rules (all phases)
- All parameters read from `configs/base.yaml` via `settings` object — never hardcode any numeric value, threshold, weight, or schema name
- All SQL DDL files must use `{schema}` placeholder — never write `public.table_name` or any literal schema name
- All functions must have type hints on every parameter and return value
- All public functions must have Google-style docstrings with `Args:`, `Returns:`, and `Raises:` sections
- No bare `except:` — always catch specific exceptions (`except ValueError`, `except KeyError`, `except Exception as e:`)
- structlog for all logging — no `print()` in any file
- No real credentials, API keys, or passwords in any committed file

### Database-specific rules
- Every ORM model must have `__table_args__ = {"schema": settings.database.schema}` — no exceptions
- Every DDL file must have a corresponding ORM model file — they must define the same columns in the same order
- UUID primary keys use `default=uuid.uuid4` (Python-side) — never `server_default=text("gen_random_uuid()")`
- DECIMAL/money columns use `Numeric(precision, scale)` — never `Float`
- All ENUM-like columns use `String` + `CHECK` constraint in DDL — never PostgreSQL ENUM types
- `soft_persona_scores` and `cluster_top_features` in `feature_store` use `Text` — never `JSON` or `JSONB`
- The `feature_store` ORM model must explicitly list all 64 `mapped_column()` declarations — no abbreviation or "...same pattern" shortcuts
- `alembic.ini` must NOT contain a `sqlalchemy.url` entry — URL is injected at runtime by `alembic/env.py` from `settings.database.url`
- `scripts/run_migrations.py` must call `CREATE SCHEMA IF NOT EXISTS` before running `alembic upgrade head`
- SQLAlchemy 2.0 API only — `session.execute(select(...))` not `session.query(...)`

### Configuration rules
- `app/core/config.py` uses `_load_and_merge_yaml()` outside `Settings.__init__` — YAML is loaded first, then `Settings(**merged)` is called so environment variables correctly override YAML values
- Load order: `base.yaml` → `{APP_ENV}.yaml` → `configs/clients/{CLIENT_NAME}.yaml` → `.env` → process env vars
- Module-level `settings` singleton — instantiated once at module import, never per-request
- Missing `CLIENT_NAME` client file raises `FileNotFoundError` immediately at startup

### Correctness rules specific to ORM models
- `DateTime` (not `Timestamp`) for all timestamp columns — import from `sqlalchemy`
- `from decimal import Decimal` must be in every model file that uses `Mapped[Decimal]`
- `from datetime import date, datetime` — use `date` directly in type hints, not `datetime.date`
- `server_default=func.now()` for `created_at`; `server_default=func.now(), onupdate=func.now()` for `updated_at`

## Definition of done

```
[ ] asyncpg installed and importable
    Verified by: python3 -c "import asyncpg; print(asyncpg.__version__)"
    Expected: 0.29.0

[ ] asyncpg==0.29.0 in requirements/base.txt
    Verified by: grep asyncpg requirements/base.txt
    Expected: asyncpg==0.29.0

[ ] Docker postgres service starts and reaches healthy state
    Verified by: docker compose up -d postgres && sleep 15 && docker compose ps
    Expected: aip_postgres shows "healthy"

[ ] Docker redis service starts and reaches healthy state
    Verified by: docker compose up -d redis && sleep 5 && docker compose ps
    Expected: aip_redis shows "healthy"

[ ] Settings singleton loads without error
    Verified by: python3 -c "from app.core.config import settings; print(settings.database.schema)"
    Expected: public

[ ] ML features matrix has exactly 46 features
    Verified by: python3 -c "from app.core.config import settings; print(len(settings.ml.features.matrix))"
    Expected: 46

[ ] Propensity weights each sum to 1.0
    Verified by: python3 -c "
    from app.core.config import settings
    s = settings.ml.propensity.subscription.weights
    c = settings.ml.propensity.churn.weights
    co = settings.ml.propensity.commerce.weights
    print(sum(s.model_dump().values()), sum(c.model_dump().values()), sum(co.model_dump().values()))
    "
    Expected: 1.0 1.0 1.0

[ ] All 10 ORM models import without error
    Verified by: python3 -c "from app.models.orm import *; print('OK')"
    Expected: OK

[ ] Async and sync DB engines initialise (requires DATABASE__URL in env)
    Verified by: python3 -c "from app.core.database import async_engine, sync_engine; print('engines OK')"
    Expected: engines OK

[ ] Alembic can read env.py without error
    Verified by: python3 -m alembic current 2>&1 | grep -v "ERROR"
    Expected: exits cleanly or shows "(head)" if already migrated

[ ] Initial migration file exists in alembic/versions/
    Verified by: ls alembic/versions/*.py
    Expected: one .py file with date prefix and "initial_schema" in name

[ ] run_migrations.py creates schema and all 10 tables
    Verified by: python3 scripts/run_migrations.py
    Expected: exits with code 0, no exceptions

[ ] All 10 tables exist in configured schema
    Verified by: docker exec aip_postgres psql -U aip_user -d audience_intelligence \
      -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"
    Expected: 10 rows including ga4_identity_bridge and feature_store

[ ] feature_store has exactly 64 columns
    Verified by: docker exec aip_postgres psql -U aip_user -d audience_intelligence \
      -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='feature_store';"
    Expected: 64

[ ] All 10 DDL files exist in sql/ddl/
    Verified by: ls sql/ddl/*.sql | wc -l
    Expected: 10

[ ] DDL files all contain {schema} placeholder (not hardcoded schema)
    Verified by: grep -rL "{schema}" sql/ddl/*.sql
    Expected: no output (all files contain {schema})

[ ] ORM models have no hardcoded schema names
    Verified by: grep -r '"public"' app/models/orm/ --include="*.py"
    Expected: no output

[ ] No hardcoded numeric config values in app/ code
    Verified by: grep -rn "604800\|pool_size.*=.*10\|max_overflow.*=.*20" app/ --include="*.py" | grep -v "test_\|#"
    Expected: no output

[ ] All new Python files pass syntax check
    Verified by: python3 -m py_compile app/core/config.py app/core/database.py app/core/logging.py app/core/security.py app/models/orm/feature_store.py scripts/run_migrations.py alembic/env.py
    Expected: no output (no syntax errors)

[ ] All new files pass pre-commit
    Verified by: pre-commit run --all-files
    Expected: all hooks Passed

[ ] All unit tests pass (no DB connection needed)
    Verified by: pytest tests/unit/ -v
    Expected: all PASSED; feature count = 46, column count = 64

[ ] All integration tests pass (requires docker compose up -d postgres)
    Verified by: pytest tests/integration/ -v
    Expected: all PASSED; 10 tables created; FK constraint test raises IntegrityError

[ ] /db-check skill passes
    Verified by: run /db-check in Claude Code
    Expected: all 10 tables pass DDL ↔ ORM parity check
```

## Estimated effort

**4 days** (per master-specification.md Phase 4: DATABASE estimate).

Breakdown:
- Day 1: `requirements/base.txt` asyncpg, `docker-compose.yml`, postgres init SQL, `.env.example`, `app/core/config.py`, `app/core/database.py`, `app/core/logging.py`, `app/core/security.py`
- Day 2: `app/models/orm/base.py`, `enums.py`, and ORM models 1–5 (`zephr_users` through `pushly_subscribers`)
- Day 3: ORM models 6–10 (`openweb_engagement` through `feature_store` — 64 columns), `__init__.py`, `alembic.ini`, `alembic/env.py`, initial migration file
- Day 4: All 10 DDL files, `scripts/run_migrations.py`, all 3 test files, DoD validation

## Risk flags

1. **asyncpg missing** — `asyncpg==0.29.0` is not in `requirements/base.txt`. This MUST be the very first action before any code is written. Failure to add it causes `ImportError` in `app/core/database.py` at import time, blocking all subsequent tests.

2. **feature_store 64-column ORM model** — High probability of a missed or misspelled column during implementation. Mitigation: implement directly from `database-schema-spec.md` Section 4.10 which lists every single `mapped_column()` explicitly. Never abbreviate. Test 4 in `test_models.py` asserts `column_count == 64` and will catch any discrepancy.

3. **DateTime vs Timestamp import** — `Timestamp` is not a valid SQLAlchemy type. All timestamp columns must use `from sqlalchemy import DateTime` and `mapped_column(DateTime, ...)`. Using `Timestamp` causes a silent `AttributeError` that is hard to trace. This is correction C1 from `database-schema-spec.md` v1.1.

4. **Alembic env.py schema injection** — `alembic/env.py` must import `settings` from `app.core.config` to get `settings.database.schema`. If `DATABASE__URL` is not set in the environment when `alembic` CLI is invoked, `Settings` raises `ValidationError`. The `alembic.ini` must NOT contain `sqlalchemy.url` — the URL is injected at runtime only.

5. **Docker volume persistence** — If a `postgres_data` volume already exists from a prior run, `docker/postgres/init/01_create_databases.sql` does NOT re-run (init scripts only run on first volume creation). To reset: `docker compose down -v` then `docker compose up -d postgres`. Document this in a comment inside `docker-compose.yml`.

6. **chore/add-master-spec-alias PR not yet merged** — `database-schema-spec.md` and `system_design-spec.md` are on the `chore/add-master-spec-alias` branch, not yet on `main`. The implementer needs these files as reference during Phase 02 implementation. They are available locally. If working from a fresh clone, merge that PR first or cherry-pick the spec files.
