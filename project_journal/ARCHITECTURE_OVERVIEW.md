# Architecture Overview — Audience Intelligence Platform

**Document Type:** Technical Architecture Reference
**Created:** 2026-05-31
**Last Updated:** 2026-05-31
**Corresponds to:** system_design-spec.md v1.0

---

## Current Architecture (Phase 2 State)

The platform has three independently deployable systems that share a PostgreSQL database:

```
configs/base.yaml ──► app/core/config.py (Settings singleton)
                              │
              ┌───────────────┼────────────────────────────────┐
              ▼               ▼                                ▼
  app/core/database.py  app/services/cache_service.py  app/core/logging.py
  (engines + sessions)  (Redis async pool)             (structlog init)
              │               │
              ▼               ▼
  app/models/orm/*.py   app/services/persona_service.py
  (10 ORM models)              │
                              ├── app/utils/cold_start.py
                              │
              app/api/v1/endpoints/*.py  ◄── app/core/security.py
                              │
              app/api/v1/router.py
                              │
              app/main.py  (lifespan, middleware, factory)
```

ETL and ML paths share `app/core/config.py` and the sync SQLAlchemy engine but never touch the FastAPI async engine or Redis async client.

---

## Component Registry

| Component | File | Responsibility |
|---|---|---|
| Settings singleton | `app/core/config.py` | YAML + env var config, available everywhere via `from app.core.config import settings` |
| Async engine | `app/core/database.py` | FastAPI endpoints; uses asyncpg driver |
| Sync engine | `app/core/database.py` | ETL/ML pipelines + Alembic; uses psycopg2 driver |
| ORM Base | `app/models/orm/base.py` | SQLAlchemy DeclarativeBase |
| ORM Models (×10) | `app/models/orm/*.py` | One file per table; all use `__table_args__ = {"schema": settings.database.schema}` |
| API Middleware | `app/core/security.py` | X-API-Key validation on every request |
| structlog | `app/core/logging.py` | JSON logging, called once per process via `configure_logging()` |
| Alembic | `alembic/env.py`, `alembic.ini` | Schema-aware migrations; `version_table_schema = settings.database.schema` |

---

## Database Architecture

### The 10 Tables

```
zephr_users  ◄──── all other source tables FK here via user_id
     │
     ├── ga4_events              (user_id FK, nullable — set after identity stitching)
     ├── ga4_identity_bridge     (user_pseudo_id → user_id mapping)
     ├── braintree_subscriptions (user_id FK)
     ├── sailthru_newsletter     (user_id FK, nullable)
     ├── pushly_subscribers      (user_id FK)
     ├── openweb_engagement      (user_id FK)
     ├── trackonomics_clicks     (user_id FK)
     ├── transunion_demographics (user_id FK, nullable UNIQUE)
     └── feature_store           (user_id PK, no FK — denormalised output table)
```

### Why ga4_identity_bridge Exists

GA4 assigns a `user_pseudo_id` to every session. This resolves to a `user_id` only when the user logs in. Without a persistent bridge table, each ETL run would need to re-scan the entire event history to re-derive all mappings. The bridge is populated incrementally by the identity stitcher and has a UNIQUE constraint on `user_pseudo_id` (one mapping per anonymous ID).

### feature_store Design

```
feature_store — 64 columns, one row per registered user
├── Identity (4):     user_id, created_at, updated_at, is_new_user
├── Web behaviour (11): total_sessions through account_age_days
├── Content affinity (8): ratio_sports through ratio_lifestyle
├── Subscription (4):  has_subscription, subscription_amount, total_billing_cycles, days_until_renewal
├── Email ML (10):     newsletter_count, open_rate, CTR, email_engagement_score, 6 nl_* flags
├── Email metadata (4): 4 additional nl_* flags NOT in ML matrix (nl_breaking_news etc.)
├── Social (4):        total_comments, total_likes_given, total_shares, social_engagement_score
├── Commerce (6):      total_affiliate_clicks through unique_advertisers_clicked
├── Demographic (3):   age_score, income_score, has_children
└── ML output (10):    persona_label through cluster_top_features
```

The PK on `user_id` serves as the upsert conflict target: `INSERT ... ON CONFLICT (user_id) DO UPDATE`. No separate UNIQUE constraint needed.

---

## Configuration Architecture

### Loading Order (lowest → highest priority)

```
1. configs/base.yaml              ← all defaults (committed, no secrets)
2. configs/{APP_ENV}.yaml         ← environment overrides (dev/prod)
3. configs/clients/{CLIENT}.yaml  ← per-client overrides (gitignored)
4. _apply_env_overrides()         ← process env vars injected into merged dict
5. Pydantic-settings .env file    ← secrets (DATABASE__URL, API keys)
6. Process environment variables  ← highest priority (deployment secrets)
```

### Why `_apply_env_overrides()` Exists

Pydantic-settings constructor kwargs (the YAML-merged dict) have higher priority than env vars. This is a documented Pydantic-settings behaviour. `_apply_env_overrides()` solves this by injecting env vars into the merged dict before calling `Settings(**merged)`, ensuring env vars always win over YAML.

**Pattern:** `DATABASE__SCHEMA=nypost` sets `merged["database"]["schema"] = "nypost"` before `Settings()` is called.

### Singleton Pattern

`settings: Settings = Settings.from_yaml_and_env()` — evaluated once at module import time. All subsequent imports receive the same object reference. This means:
- Set all required env vars **before** the first `from app.core.config import settings`
- Integration tests that need to change the schema must run in a subprocess (fresh Python process)

---

## Database Connection Architecture

```
FastAPI (async)                    ETL/ML/Alembic (sync)
─────────────────                  ─────────────────────
create_async_engine                create_engine
driver: asyncpg                    driver: psycopg2
DSN: postgresql+asyncpg://         DSN: postgresql://
AsyncSession                       Session
async_sessionmaker                 sessionmaker
get_db() → FastAPI Depends         Direct session context manager
```

**Why two engines?** FastAPI is an async framework. A sync engine would block the event loop on every DB call, killing the p99 < 10ms SLA under 10K req/sec load. ETL and ML use sync because they run in Airflow `PythonOperator` tasks (sync context) — wrapping asyncpg in `asyncio.run()` adds overhead with no benefit.

---

## Multi-Tenancy Architecture

Each client gets:
- A dedicated PostgreSQL **schema** (not database)
- Schema name set via `DATABASE__SCHEMA` env var or `configs/clients/{client}.yaml`
- Zero cross-client query possible (schema isolation at ORM level)
- All ORM models: `__table_args__ = {"schema": settings.database.schema}`
- All Alembic migrations: `schema=_schema` on every `op.create_table()` call
- Redis key namespace: `persona:{schema}:{user_id}`

**Schema switching is process-level**: one process = one schema. Multiple clients run as separate containers or separate parameterised Airflow DAG runs.

---

## ML Pipeline Architecture (Planned — Phases 5–11)

```
feature_store (46 ML features)
       │
       ▼
StandardScaler.fit_transform()  ← saved as MLflow artifact scaler.pkl
       │
       ▼
4-Stage Algorithm Evaluation:
  Stage 1: HDBSCAN discovery (finds natural K)
  Stage 2: BisectingKMeans + GMM evaluation (K=5 to K=15)
  Stage 3: Composite score selection (silhouette × 0.40 + interpretability × 0.40 + stability × 0.20)
  Stage 4: Weekly production run with selected algorithm+K
       │
       ▼
Persona assignment → feature_store.persona_label
Propensity scores → feature_store.*_propensity_score
       │
       ▼
Redis cache refresh (TTL = 604800s = 7 days)
       │
       ▼
FastAPI serves cached persona data
```

### Propensity Score Formulas

All produce outputs in [0.0, 1.0] via sigmoid. Not supervised models — derived formulas using scaled features and centroid distances.

```
subscription_score = sigmoid(
  newsletter_count_scaled × 0.30 +
  open_rate_scaled × 0.25 +
  days_since_last_visit_scaled_inverted × 0.25 +
  dist_to_subscription_focused_inverted × 0.20
)

churn_score = sigmoid(
  days_since_last_visit_scaled × 0.40 +
  bounce_rate_scaled × 0.30 +
  total_billing_cycles_scaled_inverted × 0.30
)

commerce_score = sigmoid(
  ratio_shopping_scaled × 0.35 +
  total_affiliate_clicks_scaled × 0.30 +
  dist_to_high_value_shopper_inverted × 0.35
)
```

All weights loaded from `configs/base.yaml ml.propensity.*` — never hardcoded.

---

## API Architecture (Planned — Phase 7)

```
GET  /api/v1/persona/{user_id}        → single user lookup (Redis cache → cold-start)
GET  /api/v1/personas/batch           → up to 1000 users via Redis pipeline
GET  /api/v1/health                   → liveness probe (Redis + DB status)
POST /api/v1/admin/pipeline/trigger   → trigger Airflow DAG (admin key required)
```

**Cold-start rules** (priority order, loaded from `configs/base.yaml`):
1. `ratio_sports > 0.50` → `sports_cold_start`
2. `(ratio_celebrity + ratio_entertainment) > 0.50` → `celebrity_cold_start`
3. `has_subscription == True` → `subscription_cold_start`
4. `newsletter_count > 0` → `newsletter_cold_start`
5. default → `new_user`

---

## Scaling Architecture

| Tier | Users | Backend | Pipeline Duration |
|---|---|---|---|
| Dev/Synthetic | 100K | pandas | < 2 min |
| Small publisher | < 1M | pandas | < 10 min |
| Mid publisher | 1M–10M | dask | < 30 min |
| Large publisher | 10M–50M | pyspark | < 2 hours |
| NYPost scale | 50M–100M | pyspark | 3–4 hours |

Backend switch via `configs/base.yaml feature_engineering.backend` — zero code changes.

---

## Architectural Principles

1. **Config-driven**: no tunable parameter hardcoded in Python
2. **Schema isolation**: one PostgreSQL schema per client, no cross-client queries possible
3. **Fail loudly**: pipeline aborts on quality gates; never silently corrupts assignments
4. **Reproducible**: `random_state=42`, all artifacts in MLflow, full audit trail
5. **Cache-first serving**: API reads Redis exclusively at request time; never blocks on DB
6. **Cold-start always wins over 404**: valid users always get a response
7. **DDL ↔ ORM parity**: `/db-check` enforced on every schema PR
