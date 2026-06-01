# Decision Log — Audience Intelligence Platform

**Document Type:** Architectural Decision Summary
**Created:** 2026-05-31
**Last Updated:** 2026-05-31

Full ADR files are in `decisions/`. This log provides a quick-reference index.

---

## Quick Reference Index

| ADR | Decision | Status | Date |
|---|---|---|---|
| ADR-001 | Ultra Planning Mode for specifications | ACTIVE | 2026-05-30 |
| ADR-002 | Custom slash command development workflow | ACTIVE | 2026-05-30 |
| ADR-003 | Airflow in separate requirements file | ACTIVE | 2026-05-30 |
| ADR-004 | MLflow local filesystem artifacts for dev | ACTIVE | 2026-05-30 |
| ADR-005 | spec-source.md table names as canonical | ACTIVE | 2026-05-30 |
| ADR-006 | 6 newsletter flags in ML matrix; 4 as metadata | ACTIVE | 2026-05-30 |
| ADR-007 | Async + sync dual SQLAlchemy engine | ACTIVE | 2026-05-30 |
| ADR-008 | VARCHAR + CHECK over PostgreSQL ENUM types | ACTIVE | 2026-05-31 |
| ADR-009 | ga4_identity_bridge as 10th table | ACTIVE | 2026-05-31 |
| ADR-010 | No ga4_events table partitioning at Phase 2 | ACTIVE | 2026-05-31 |
| ADR-011 | Python-side UUID generation (not server_default) | ACTIVE | 2026-05-31 |
| ADR-012 | `_apply_env_overrides()` for config priority fix | ACTIVE | 2026-05-31 |
| ADR-013 | Subprocess approach for integration test schema isolation | ACTIVE | 2026-05-31 |
| ADR-014 | Dynamic `_schema` in Alembic initial migration | ACTIVE | 2026-05-31 |
| ADR-015 | Text (not JSON/JSONB) for soft_persona_scores | ACTIVE | 2026-05-31 |
| ADR-016 | No relationship() objects in Phase 2 ORM models | ACTIVE | 2026-05-31 |

---

## Key Decisions Summary

### ADR-007: Async + Sync Dual SQLAlchemy Engine
**Decision:** Use `create_async_engine` (asyncpg) for FastAPI and `create_engine` (psycopg2) for ETL/ML/Alembic in `app/core/database.py`.
**Reason:** FastAPI's async event loop blocks on sync DB calls. At 10,000 req/sec with p99 < 10ms SLA, a sync engine would saturate the loop. ETL and ML run in Airflow PythonOperator (sync context); wrapping async clients adds overhead with no benefit.
**Alternative considered:** Single sync engine for everything. Rejected because it violates FastAPI's async model.

### ADR-008: VARCHAR + CHECK over PostgreSQL ENUM
**Decision:** All 14 enumerated column types use `VARCHAR(N) + CHECK constraint` in DDL and `str, Enum` Python classes for application-layer type safety.
**Reason:** PostgreSQL ENUM types require `ALTER TYPE ... ADD VALUE` to extend — a DDL operation that cannot be rolled back and breaks Alembic autogenerate. The platform will evolve (new subscription plans, new algorithms). VARCHAR + CHECK constraints are trivially modified via standard migrations.
**Alternative considered:** PostgreSQL native ENUM. Rejected due to schema evolution friction.

### ADR-009: ga4_identity_bridge as 10th Table
**Decision:** Add `ga4_identity_bridge` as a persistent table mapping `user_pseudo_id → user_id`.
**Reason:** Without persistence, each incremental ETL run must re-scan the entire GA4 event history to re-derive all mappings. The bridge table grows incrementally (one row per resolved anonymous ID) and makes each ETL run O(new events) rather than O(all events).
**Alternative considered:** Resolve mapping in ETL code without persistence. Rejected because it makes incremental processing O(n) on the full dataset.

### ADR-012: `_apply_env_overrides()` for Config Priority
**Decision:** Add `_apply_env_overrides(merged_dict)` that injects process env vars into the YAML-merged dict before `Settings(**merged)` is called.
**Reason:** Pydantic-settings treats constructor kwargs as having higher priority than env vars. This means `Settings(**yaml_merged_dict)` ignores `DATABASE__SCHEMA=test` even when set in the process environment. The fix injects env vars into the dict at the right level.
**Alternative considered:** Use Pydantic model_validate with env_vars overlay. Rejected as more complex with the same effect. Dropping YAML merge entirely. Rejected — would lose the multi-level override chain.

### ADR-013: Subprocess Approach for Integration Test Schema Isolation
**Decision:** Integration tests run Alembic migrations in a subprocess (fresh Python process) rather than calling `run_migrations()` directly.
**Reason:** The `settings` singleton is loaded once at module import time. After the test process has imported `app.core.config`, setting `os.environ['DATABASE__SCHEMA'] = 'test_schema'` and reloading the module still doesn't work reliably because `_apply_env_overrides()` reads env vars at Settings() call time, but the subprocess has a completely fresh Python interpreter where env vars are in effect before any import.
**Alternative considered:** `importlib.reload()` — tried first, failed due to singleton caching. Direct `alembic upgrade` with schema override — failed because `_schema = settings.database.schema` in `alembic/env.py` is evaluated at module load.

### ADR-014: Dynamic `_schema` in Alembic Initial Migration
**Decision:** Replace hardcoded `schema="public"` in the autogenerated migration with `schema=_schema` referencing `_schema = settings.database.schema` imported at migration load time.
**Reason:** Alembic autogenerate captures the literal value of `settings.database.schema` at generation time (was `"public"`). Any test or client running with a different schema would create tables in `public`, not the configured schema.
**Alternative considered:** Keep public hardcoded; use separate migration per client. Rejected — defeats the purpose of schema-per-tenant isolation.
