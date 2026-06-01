# Session Recovery Prompts

Use these prompts at the start of a session to set context without reading large files.

---

## RECOVERY_GLOBAL (any session)

```
Read .claude/project_context/00_global.md and .claude/CURRENT_STATUS.md only.

Current phase: 3 — Synthetic Data Generation
Current branch: feature/phase03-synthetic-data
Status: Spec ready, not yet implemented

Next action: Implement data generators for Phase 3 synthetic data.
```

---

## RECOVERY_DATA (ETL, synthetic data, feature engineering)

```
Read .claude/project_context/00_global.md + 01_data_context.md + .claude/CURRENT_STATUS.md only.

Context:
- 10 database tables: 8 staging + user_profiles + feature_store
- 46 ML features grouped by source (GA4, Transunion, First-party, Behavioral, Lookalike, Survey)
- Seeding order: user_profiles → ga4_identity_bridge → ga4_events → ... → feature_store
- Identity resolution: GA4 pseudo_id → user_id via login events; email as fallback
- Cold-start: Zero-fill demographics, RFM=(0,0,0), mask personas until 30 days GA4 data

Current task: [INSERT YOUR TASK HERE]
```

---

## RECOVERY_ML (training, evaluation, inference, MLflow)

```
Read .claude/project_context/00_global.md + 02_ml_context.md + .claude/CURRENT_STATUS.md only.

Context:
- 9 personas, KMeans (k=5-15, silhouette ≥0.30 quality gate)
- 46 features: GA4 (F-01–F-12), Demographics (F-13–F-20), CRM (F-21–F-30), Behavioral (F-31–F-38), Lookalike (F-39–F-42), Survey (F-43–F-46)
- Cold-start: Defaults + lookalike scoring, confidence × 0.6 for <30 days
- Propensity formulas: Purchase (0.3+0.3+0.4), Churn (0.4+0.3+0.3), Reactivation (0.5+0.3+0.2)
- Log1p transform on F-07 (session_count), F-14 (income), F-32 (frequency)
- StandardScaler fit once in Phase 6, frozen for Phase 7+ inference

Current task: [INSERT YOUR TASK HERE]
```

---

## RECOVERY_API (FastAPI, Redis, serving, rate limiting)

```
Read .claude/project_context/00_global.md + 03_api_context.md + .claude/CURRENT_STATUS.md only.

Context:
- 4 planned endpoints: GET /personas/{user_id}, GET /personas/batch, GET /propensity/{user_id}, POST /inference/trigger
- Redis keys: persona:{user_id} (24h TTL), propensity:{user_id} (1h TTL), inference:lock (5m)
- Auth: X-API-Key header (required, validated against api_keys table)
- Response schemas: PersonaResponse + PropensityResponse + InferenceStatusResponse
- Cold-start responses: confidence=0.40, no activation_strategy, return null persona if no seed match
- Rate limits: 10K req/min per key (at gateway, not in-app)

Current task: [INSERT YOUR TASK HERE]
```

---

## RECOVERY_INFRA (Docker, CI/CD, migrations, Airflow setup)

```
Read .claude/project_context/00_global.md + 04_infra_context.md + .claude/CURRENT_STATUS.md only.

Context:
- Docker services: postgres (5432), redis (6379), api (8000), adminer (8080), minio (9000), jupyter (8888), worker
- Databases: audience_intelligence_dev, audience_intelligence_staging, audience_intelligence_prod
- Schema: Dynamic from settings.database.schema (default "public", override per client)
- Alembic: Never hardcode schema in migrations; use settings override via context.configure()
- Environment: DATABASE_URL, REDIS_URL, MINIO_*, API_KEY_SECRET, LOG_LEVEL, SCHEMA
- CI/CD gates: Black + isort + flake8 + mypy strict + pytest (>85% coverage) + conventional commits
- Debug: docker compose down -v for fresh start; pytest with subprocess isolation for schema tests

Current task: [INSERT YOUR TASK HERE]
```

---

## RECOVERY_DB (database schema, ORM models, migrations, constraints)

```
Read .claude/project_context/00_global.md + 01_data_context.md + .claude/CURRENT_STATUS.md only.

Context:
- 10 tables: 8 staging (ga4_events, transunion_demographics, ...) + user_profiles + feature_store
- feature_store: 64 columns (46 features + 9 persona_scores + user_id + timestamps)
- Primary keys: (user_id) for user_profiles/feature_store; (source_id, user_id) for staging tables
- UNIQUE constraints: user_profiles(user_id), feature_store(user_id) — required for ON CONFLICT upserts
- CASCADE deletes: user_profiles → ga4_events, user_sessions only
- Schema dynamic from settings (never hardcode); all DDL uses {schema} placeholder
- ORM __table_args__: {"schema": settings.database.schema} required on all models
- ON CONFLICT behavior: Alembic auto-detect may miss composite key uniqueness; hand-edit if needed

Current task: [INSERT YOUR TASK HERE]
```

---

## How to Use These Prompts

1. **At session start:** Copy the relevant RECOVERY_* prompt for your task type
2. **Replace [INSERT YOUR TASK HERE]** with your actual task (one sentence)
3. **Paste into chat** — this loads the right context files without reading large specs
4. **Continue with:** "Now [describe what you need to do]"

Example usage:
```
Read .claude/project_context/00_global.md + 01_data_context.md + .claude/CURRENT_STATUS.md only.

Current task: Implement a generator for synthetic GA4 events with realistic session patterns and user pseudo_id → user_id resolution via ga4_identity_bridge.
```
