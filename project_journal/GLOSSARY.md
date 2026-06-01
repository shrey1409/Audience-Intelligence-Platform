# Glossary — Audience Intelligence Platform

**Document Type:** Terminology Reference
**Created:** 2026-05-31

---

## Platform-Specific Terms

**Audience Intelligence Platform (AIP)**
The ML-powered audience segmentation system being built. Ingests data from 8 sources, builds a 46-feature matrix per user, assigns persona labels, exposes via FastAPI.

**Cold Start**
When a `user_id` is not found in Redis cache. Instead of returning a 404, the cold-start engine applies rule-based persona assignment using available feature data. Always returns `is_cold_start: true` in the API response. Five rules in priority order, loaded from `configs/base.yaml`.

**feature_store**
The central output table of the pipeline. One row per registered user. 64 columns: 46 ML features + 4 metadata flags + 10 ML output columns + 4 identity/audit columns. Written weekly via upsert (`INSERT ... ON CONFLICT (user_id) DO UPDATE`).

**ML Feature Matrix**
The 46 numeric columns fed to the clustering algorithms. Canonical list defined in `configs/base.yaml ml.features.matrix`. Any code that references these columns must read from `settings.ml.features.matrix` — never hardcode the list.

**Persona Label**
One of 9 human-readable strings assigned to each registered user by the clustering pipeline: `loyalist`, `subscription_focused`, `high_value_shopper`, `sports_focused`, `social_engager`, `occasional_buyer`, `celebrity_entertainment`, `casual_reader`, `low_engager`.

**Propensity Score**
A [0.0, 1.0] float computed for each user representing their likelihood of a specific conversion event. Three types: `subscription_propensity_score`, `churn_propensity_score`, `commerce_propensity_score`. NOT supervised models — derived formulas using scaled features and centroid distances.

**Schema-per-tenant**
The multi-tenancy isolation strategy. Each client gets a dedicated PostgreSQL schema (e.g., `nypost`, `dailymail`). All ORM models use `__table_args__ = {"schema": settings.database.schema}`. No cross-client queries are possible.

**Silhouette Score**
The clustering quality metric. Range: [-1, 1]; higher is better. Production target: > 0.35. Safety gate aborts write-back if < 0.30. Computed via `sklearn.metrics.silhouette_score` with `sample_size=50000` for performance.

**Upsert**
`INSERT ... ON CONFLICT (user_id) DO UPDATE SET ...` pattern used to write feature_store. Ensures atomic write-back — either all columns update or none do. The PK `user_id` is the conflict target.

---

## Technical Terms

**ADR (Architecture Decision Record)**
A document recording a significant architectural decision: what was decided, why, what alternatives were considered, and the tradeoffs. Stored in `project_journal/decisions/`.

**asyncpg**
Python async PostgreSQL driver used by `create_async_engine` for the FastAPI path. Required for non-blocking DB calls in the async event loop.

**Alembic**
SQLAlchemy's database migration tool. The `alembic/versions/` directory contains timestamped migration scripts. `alembic upgrade head` applies all pending migrations.

**DeclarativeBase**
The SQLAlchemy base class that all ORM models inherit from (via `app/models/orm/base.py`). All models are registered with `Base.metadata` by importing them. This is how Alembic knows which tables to create.

**env_nested_delimiter**
Pydantic-settings feature. `env_nested_delimiter="__"` means `DATABASE__URL` maps to `settings.database.url`. Allows flat environment variables to configure nested Pydantic models.

**ForeignKey()**
SQLAlchemy construct that must be placed INSIDE `mapped_column()` for FK columns. Without it, SQLAlchemy does not enforce referential integrity at the ORM level and Alembic autogenerate ignores FK relationships. Pattern: `ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE")`.

**ga4_identity_bridge**
The 10th database table. Maps `ga4.user_pseudo_id → zephr.user_id`. Populated incrementally by the identity stitcher. Enables efficient incremental ETL without re-scanning the full event history.

**include_schemas**
Alembic configuration option (`include_schemas=True`) that tells autogenerate to look at tables in non-default schemas. Required for schema-per-tenant migrations.

**HDBSCAN**
Hierarchical Density-Based Spatial Clustering of Applications with Noise. Used in Stage 1 of the algorithm evaluation framework to discover the natural number of clusters K before running parametric algorithms.

**MLflow**
Experiment tracking and model registry. Every pipeline run logs: algorithm, K, silhouette score, persona distribution, feature importance, and the scaler artefact. Enables rollback by loading prior run's `scaler.pkl`.

**psycopg2**
Synchronous PostgreSQL driver used by `create_engine` for the ETL/ML/Alembic path. Stable, well-tested, compatible with Alembic.

**server_default**
SQLAlchemy column option that sets the default value at the PostgreSQL server level (e.g., `server_default=func.now()`). Not available in Python until after INSERT. Used for `created_at` and `updated_at`.

**structlog**
Structured logging library that outputs JSON. All pipeline steps use structlog — never `print()`. The `configure_logging()` function must be called exactly once per process (in the FastAPI lifespan or at the top of each Airflow PythonOperator callable).

**TTL (Time To Live)**
The Redis key expiry duration. Set to `604800` seconds (7 days) in `configs/base.yaml redis.ttl_seconds`. Set ON WRITE only, not on read. Ensures persona data remains available for 7 days without a pipeline run.

**version_table_schema**
Alembic configuration option that places the `alembic_version` table in the configured schema (not `public`). Required for schema-per-tenant to track migration state per client.

---

## Source System Abbreviations

| Abbreviation | Full Name | Purpose |
|---|---|---|
| GA4 | Google Analytics 4 | Web behaviour tracking |
| BigQuery | Google BigQuery | GA4 data export destination |
| Braintree | Braintree Payments | Subscription payment events |
| Sailthru | Sailthru Email Platform | Newsletter engagement |
| Pushly | Pushly Push Notifications | Push opt-in and opens |
| OpenWeb | OpenWeb Community Platform | Social comments/reactions |
| Trackonomics | Trackonomics Affiliate | Affiliate click/conversion |
| Transunion | Transunion TruAudience | Demographic enrichment |
| Zephr | Zephr Subscription Engine | User identity and registration |

---

## File Naming Conventions

| Pattern | Example | Meaning |
|---|---|---|
| `configs/clients/{name}.yaml` | `configs/clients/nypost.yaml` | Per-client config override (gitignored) |
| `sql/ddl/NNN_create_{table}.sql` | `sql/ddl/001_create_zephr_users.sql` | DDL reference file (not directly executed) |
| `alembic/versions/YYYYMMDD_{rev}_{slug}.py` | `20260531_d65666c751dc_initial_schema.py` | Alembic migration file |
| `feature/phaseNN-{name}` | `feature/phase02-database-schema` | Phase feature branch |
| `tests/unit/test_{module}.py` | `tests/unit/test_config.py` | Unit test (no DB required) |
| `tests/integration/test_{feature}.py` | `tests/integration/test_migrations.py` | Integration test (DB required) |
