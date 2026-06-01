# Audience Intelligence Platform — Global Context

**Project:** ML-powered audience segmentation for digital publishers
**Stack:** FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis, Pandas, NumPy, scikit-learn, MLflow, Airflow, structlog, Pydantic v2
**Primary branch:** main

## Phase Tracker
| Phase | Name | Status |
|-------|------|--------|
| 1 | environment-setup | ✅ |
| 2 | database-schema | ✅ |
| 3 | synthetic-data | 🔄 |
| 4 | etl-ingestion | ⏳ |
| 5 | feature-engineering | ⏳ |
| 6 | ml-training | ⏳ |
| 7 | ml-inference | ⏳ |
| 8 | api-layer | ⏳ |
| 9 | airflow-dags | ⏳ |
| 10 | monitoring | ⏳ |

## Git Conventions
- **Branches:** `feature/phaseN-name`, `fix/name`, `chore/name` (from main)
- **Commits:** `<type>: <description>` (conventional commits per CLAUDE.md)

## Never-Do Rules (Enforced)
1. NEVER hardcode config values — read from configs/base.yaml
2. NEVER commit .env, venv/, secrets, API keys, PII
3. NEVER use SELECT * — always name columns
4. NEVER put business logic in FastAPI endpoints
5. NEVER write DDL without {schema} placeholder
6. NEVER write ORM model without __table_args__ schema param
7. NEVER leave TODOs, placeholders, or pseudo-code in committed files
8. NEVER skip type hints on any function
9. NEVER re-fit a scaler on inference data (fit once, use everywhere)
10. NEVER update a stale status file — edit .claude/CURRENT_STATUS.md instead

## Quick Links
- **Full standards:** See .claude/CLAUDE.md
- **Data schema:** See project_context/01_data_context.md
- **ML config:** See project_context/02_ml_context.md
- **API design:** See project_context/03_api_context.md
- **Infra setup:** See project_context/04_infra_context.md
- **Decisions log:** See project_context/05_decisions.md
- **Session recovery:** See project_context/06_session_recovery.md
