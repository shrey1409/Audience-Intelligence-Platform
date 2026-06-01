# Audience Intelligence Platform — Project Context

**ML-powered audience segmentation platform for digital publishers.**
**For detailed specs, see:** `.claude/specs/reference/` or `.claude/CURRENT_STATUS.md`

## Phase Tracker
| Phase | Name                | Status | Branch |
|-------|---------------------|--------|--------|
| 1 | environment-setup | ✅ | merged |
| 2 | database-schema | 🔄 | feature/phase2-database-schema |
| 3 | synthetic-data | ⏳ | — |
| 4 | etl-ingestion | ⏳ | — |
| 5 | feature-engineering | ⏳ | — |
| 6 | ml-training | ⏳ | — |
| 7 | ml-inference | ⏳ | — |
| 8 | api-layer | ⏳ | — |
| 9 | airflow-dags | ⏳ | — |
| 10 | monitoring | ⏳ | — |

## Core Stack
FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, Redis, Pandas, NumPy, scikit-learn, MLflow, Apache Airflow, structlog, Pydantic-settings

## Folder Structure
```
app/ (core, models/orm, schemas, api/v1, services, utils)
etl/ (ingestion, transforms, identity)
ml/ (feature_store, training, inference, pipelines, experiments)
sql/ (ddl, analytics)
dags/ (Airflow)
configs/ (base.yaml, dev.yaml, prod.yaml)
tests/ (unit, integration)
scripts/ (migrations, seeds, pipelines)
requirements/ docker/
```

## Git Conventions
- Branch: `feature/phaseN-name`, `fix/name`, `chore/name` (from main)
- Commit: `<type>: <description>` (conventional commits)

## Coding Standards (Enforce All)
- Python 3.11+, type hints on every function, no `Any` types
- Black + isort + flake8 + mypy (strict)
- SQLAlchemy 2.0: `select()`, `Session.scalars()`, no legacy `Query`
- All ORM models: `__table_args__ = {"schema": settings.database.schema}`
- All SQL DDL: use `{schema}` placeholder (never hardcode schema)
- structlog for logging (no bare `print()`)
- No bare `except:` (catch specific exceptions)
- Pydantic v2 for API validation
- DB ops only in service layer (never in endpoints)

## Never-Do Rules
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
11. NEVER write more than 20 lines per project_journal/ entry — delete and summarize old entries
12. NEVER let LEARNINGS.md exceed 30 entries total — delete oldest when adding new entries
