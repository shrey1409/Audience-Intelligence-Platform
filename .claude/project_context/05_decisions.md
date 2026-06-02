# Architectural Decisions Log

## Phase 1: Environment Setup
- **[P1] Decision:** PostgreSQL 14 as primary database. **Reason:** SQL-first architecture for identity resolution; Alembic migrations well-supported. **Watch-out:** Schema dynamic from config, never hardcode "public".

- **[P1] Decision:** SQLAlchemy 2.0 async (asyncpg). **Reason:** Enables high-throughput ETL pipelines; pool_size=20 for concurrent workers. **Watch-out:** All queries must use `select()` API, not legacy `Query` objects.

- **[P1] Decision:** Redis for caching (not Memcached). **Reason:** TTL support + sorted sets for ranking; 86400s TTL for personas. **Watch-out:** Cache invalidation on schema changes.

## Phase 2: Database Schema
- **[P2] Decision:** 10 tables (8 staging + 2 core + feature_store). **Reason:** Separation of concerns; feature_store is derived/writable, staging tables are read-only. **Watch-out:** ON CONFLICT upserts require UNIQUE constraints; Alembic auto-detect misses composite key uniqueness.

- **[P2] Decision:** Dynamic schema from settings, all DDL uses `{schema}` placeholder. **Reason:** Multi-tenant support (clients can have separate schemas). **Watch-out:** importlib.reload() doesn't work for schema override in tests; use subprocess isolation instead.

- **[P2] Decision:** Pydantic v2 settings with env_file fallback. **Reason:** Constructor kwargs no longer override env vars (v2 behavior change). **Watch-out:** Test config must not rely on kwargs override; use env fixtures instead.

- **[P2] Decision:** VARCHAR + CHECK constraints for enum columns (not PostgreSQL ENUM). **Reason:** Portability across databases; easier DDL changes. **Watch-out:** Check constraints must be enforced in application layer as well.

- **[P2] Decision:** CASCADE deletes on user_profiles only (not persona_assignments). **Reason:** Prevent accidental cascade orphaning; explicit deletion via service layer. **Watch-out:** Order of deletion matters in tests; delete user_profiles last.

## Phase 3: Synthetic Data Generation
- **[P3] Decision:** Faker library for deterministic data generation; `Faker.seed(42)` at pipeline start. **Reason:** Reproducible test data across machines. **Watch-out:** Must use `faker.uuid4()` not `uuid.uuid4()` for any ID that seeds downstream GROUP BY keys.
- **[P3] Decision:** GA4 generator yields 20K-event sub-batches (not one batch per user chunk). **Reason:** Full chunk accumulation caused OOM with 15M events. **Watch-out:** Sub-batch boundary can split a user's events across two writes — verify COUNT(DISTINCT session_id) still correct.
- **[P3] Decision:** feature_store `created_at`/`updated_at` set explicitly to `REFERENCE_DT = datetime(2026,6,1)`. **Reason:** ORM `server_default=func.now()` is wall-clock and breaks reproducibility. **Watch-out:** Phase 4 ETL real data should write actual ingestion timestamps.
- **[P3] Decision:** Test schema env var cleanup moved to `test_schema` fixture teardown in `tests/conftest.py`. **Reason:** `test_migrations.py` sets `os.environ["DATABASE__SCHEMA"]` directly (not monkeypatch) — it leaked into unit tests. **Watch-out:** Any new integration test that sets env vars directly must clean them up.

## Cross-Phase Patterns
- **Identity Resolution:** GA4 pseudo_id → user_id via ga4_identity_bridge (login events). Email is secondary fallback.
- **Feature Completeness:** 46 ML features + 9 persona scores in feature_store (64 cols total).
- **Cold-Start Strategy:** For new users (<30 days), use demographic defaults + lookalike scoring + reduce confidence by 40%.
- **Model Versioning:** MLflow artifacts per phase; alias=production after validation (Phase 6+).
- **Logging:** structlog only (no print statements); all async functions log at DEBUG level minimum.
