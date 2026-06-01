# Project History — Audience Intelligence Platform

**Document Type:** Chronological History
**Created:** 2026-05-31
**Last Updated:** 2026-05-31

---

## How to Read This Document

Each entry covers: **what was done**, **why it was done**, and **what was produced**. Entries are in chronological order. This is the authoritative record of how the project evolved.

---

## Event 1 — Project Initialisation

**Date:** 2026-05-30 (morning)
**Branch:** `main` (initial commits)

### What Was Done
The project repository was created from scratch on a local Mac. The initial commits established:
- `.gitignore` covering `venv/`, `.venv/`, `.env`, client config files, data directories, and compiled artefacts
- `pyproject.toml` with Black (88-char), isort (profile=black), mypy (strict), and pytest configuration
- `requirements/base.txt` pinning all production dependencies
- `requirements/dev.txt` adding pytest, coverage, Faker, black, isort, mypy, flake8, pre-commit
- `configs/base.yaml` — the canonical configuration file covering all 46 ML features, clustering parameters, propensity weights, cold-start rules, ETL source modes, and monitoring thresholds
- The complete folder scaffold: `app/`, `etl/`, `ml/`, `sql/`, `dags/`, `configs/`, `tests/`, `scripts/`, `docker/`, `requirements/`
- All `__init__.py` files creating Python package structure
- Pre-commit hooks: trailing whitespace, end-of-file, YAML/JSON validation, large file guard, merge conflict check, private key detection, no-commit-to-main, black, isort, flake8

### Why It Was Done
A complete scaffold before writing any implementation code ensures:
1. Every file created from day one passes linting without retrofitting
2. The folder structure matches the final architecture from the start (no reorganisation later)
3. `configs/base.yaml` as the first real file establishes the config-first principle before any code can hardcode values

### What Was Produced
- PR #1 merged: `feature/phase1-environment-setup` → `main`
- Commit `ec780f9`: Phase 1 environment setup complete

---

## Event 2 — Claude Code Workflow Design

**Date:** 2026-05-30 (mid-morning)
**Branch:** `main` / `feature/phase2-database-schema` (pre-spec work)

### What Was Done
A custom slash command strategy was designed and implemented in `.claude/commands/`. The commands created:

| Command | Purpose |
|---|---|
| `/phase-start` | Pull main, create feature branch, generate phase spec |
| `/phase-ship` | Validate, commit, push, create PR, merge, clean up |
| `/phase-commit` | Commit and push without merging (mid-phase checkpoint) |
| `/validate-phase` | Run all DoD checks for a phase |
| `/create-spec` | Generate detailed spec for a specific phase |
| `/build-file` | Build a single project file completely |
| `/db-check` | Verify DDL ↔ ORM parity |
| `/ml-check` | Validate ML config integrity |
| `/test-gen` | Generate pytest tests for a module |
| `/debug` | Load full project context from CLAUDE.md |

### Why It Was Done
Without a structured workflow, Claude Code sessions tend to:
- Make inconsistent architectural decisions across sessions
- Leave partially-complete files
- Forget to run pre-commit before committing
- Skip PR creation and merge directly to main
- Lose context between sessions

The slash command strategy enforces: spec-first → branch → implement → validate → PR → merge → cleanup. This is the same discipline used in professional engineering teams, applied to AI-assisted development.

### What Was Produced
- 10 `.claude/commands/*.md` files, each containing a detailed prompt
- `.claude/CLAUDE.md` — master project context document loaded by every session

---

## Event 3 — Master Specification Creation

**Date:** 2026-05-30 (afternoon)
**Branch:** `feature/phase2-database-schema` (first iteration)
**Artifact:** `.claude/specs/masterspecification.md` (later aliased to `master-specification.md`)

### What Was Done
The Master Specification Document was created — a 2,094-line document covering all 15 engineering phases of the platform. Key sections:

- **Section 5**: All functional requirements (F-01 through F-33)
- **Section 7**: ML system requirements — 46 features with source, transformation, and null handling
- **Section 8**: Data requirements — 9 table schema, identity resolution, feature store design
- **Section 9**: Platform requirements — Docker Compose, 7 services, NFRs
- **Section 15**: Resolved Decisions — 7 binding architectural decisions
- **Section 16**: Engineering Standards — Python, SQL, API, Git, Config, Testing, Logging

Critical decisions locked in Section 15:
- Q2: feature_store has 64 columns (46 ML + 4 metadata nl_* + 10 ML output + 4 audit)
- Q3: CLAUDE.md updated with canonical table names
- Q4: Airflow goes in `requirements/airflow.txt` (not base.txt — dependency conflict)
- Q5: MLflow artifacts use local filesystem for dev (not MinIO)
- Q6: Table naming follows spec-source.md (e.g. `zephr_users` not `user_profiles`)
- Q7: 6 newsletter flags in ML matrix; 4 extra as metadata only

### Why It Was Done
A complete specification before any implementation prevents the most expensive class of mistakes: building the wrong thing. The specification answers "what does the system do?" before any line of production code exists.

The specification was generated using **Ultra Planning Mode** — a multi-agent cloud planning session that:
1. Read all source documents
2. Cross-referenced conflicting requirements
3. Resolved ambiguities with binding decisions
4. Produced an implementation-ready spec with no TBDs

### What Was Produced
- `.claude/specs/masterspecification.md` (2,094 lines)
- PR #3 merged: planning artifacts → `main`

---

## Event 4 — System Design Specification

**Date:** 2026-05-30 (evening)
**Branch:** `chore/add-master-spec-alias`
**Artifact:** `.claude/specs/system_design-spec.md`

### What Was Done
The System Design Specification was created via Ultra Planning Mode. This document answers one question the Master Specification does not: **"HOW do the components connect, initialise, and interact at the code level?"**

Key sections:
- **Section 2**: Complete `app/core/config.py` design — 13 nested Pydantic models, YAML loading sequence, env var priority
- **Section 3**: Database connection architecture — dual engine pattern (asyncpg + psycopg2), session factory, Alembic env.py design
- **Section 4**: Redis connection lifecycle — async pool, cache key schema `persona:{schema}:{user_id}`, TTL strategy
- **Section 5**: FastAPI application factory — lifespan pattern, middleware order, dependency injection chain
- **Section 7**: Docker Compose — 8 services with health checks
- **Section 8**: Alembic migration design — schema-aware `env.py`, `version_table_schema`
- **Section 9**: ORM base class design — schema injection via `settings.database.schema`
- **Section 13**: 6 architectural risks with decisions
- **Section 14**: Definition of done — 10 verifiable items

### Why It Was Done
Specification documents answer "what" — system design documents answer "how." Without a system design spec, implementation would require making dozens of micro-decisions in real-time (async vs sync? singleton vs per-request? yaml before or after env vars?) that compound into inconsistent architecture.

### What Was Produced
- `.claude/specs/system_design-spec.md` (1,880 lines)

---

## Event 5 — Database Schema Specification

**Date:** 2026-05-31 (morning)
**Branch:** `chore/add-master-spec-alias`
**Artifact:** `.claude/specs/database-schema-spec.md`

### What Was Done
The Database Schema Specification was created — the primary implementation input for Phase 2. This 1,933-line document covers:

- **Section 3**: Complete DDL for all 10 tables with exact column types, constraints, and indexes
- **Section 4**: Complete ORM model specification — every `mapped_column()` call explicit
- **Section 5**: 14 Python Enum classes (decision: VARCHAR + CHECK, not PostgreSQL ENUM types)
- **Section 6**: 29 indexes across all tables with rationale
- **Section 7**: DDL file coexistence with Alembic (DDL = reference docs; Alembic = authoritative)
- **Section 13**: 7 binding decisions (Q1–Q7) including ga4_identity_bridge as 10th table

Version 1.1 corrections applied (critical bugs caught before implementation):
- C1: `DateTime` not `Timestamp` in SQLAlchemy
- C3: `from decimal import Decimal` required
- C4: `from datetime import date` required
- C5: `ForeignKey()` inside `mapped_column()` required
- C6: `alembic/versions/.gitkeep` required

### Why It Was Done
Phase 2 builds 10 database tables with 126 total columns and 14 enum types. Without a complete specification, column count errors (especially in the 64-column feature_store) are near-certain. The spec was written in planning mode specifically to prevent having to debug ORM ↔ DDL mismatches after writing 2,000+ lines of boilerplate.

### What Was Produced
- `.claude/specs/database-schema-spec.md` v1.1 (1,933 lines)

---

## Event 6 — Phase 2 Implementation

**Date:** 2026-05-31 (afternoon–evening)
**Branch:** `feature/phase02-database-schema`

### What Was Done
38 files were created implementing the complete Phase 2 deliverables:

**Core application layer:**
- `app/core/config.py` — 13 nested Pydantic models, YAML deep-merge loader, `_apply_env_overrides()`, module-level singleton
- `app/core/database.py` — dual engine (asyncpg async + psycopg2 sync), `get_db()` dependency
- `app/core/logging.py` — structlog JSON configuration
- `app/core/security.py` — `APIKeyMiddleware` (Starlette `BaseHTTPMiddleware`)

**ORM models (10 tables):**
- `app/models/orm/base.py` — `DeclarativeBase`
- `app/models/orm/enums.py` — 14 `str, Enum` classes
- 10 model files: `zephr_users`, `ga4_events`, `ga4_identity_bridge`, `braintree_subscriptions`, `sailthru_newsletter`, `pushly_subscribers`, `openweb_engagement`, `trackonomics_clicks`, `transunion_demographics`, `feature_store` (64 columns)

**Alembic infrastructure:**
- `alembic.ini` — no hardcoded `sqlalchemy.url`
- `alembic/env.py` — schema-aware with `include_schemas=True`, `version_table_schema=_schema`
- `alembic/script.py.mako` — migration template
- `alembic/versions/20260531_d65666c751dc_initial_schema.py` — initial migration (autogenerated, then fixed to use dynamic `_schema`)

**Infrastructure:**
- `docker-compose.yml` — postgres:15 + redis:7-alpine with health checks
- `docker/postgres/init/01_create_databases.sql` — creates mlflow and airflow databases

**SQL DDL reference files:**
- `sql/ddl/001–010_create_*.sql` — 10 human-readable DDL files with `{schema}` placeholder

**Tests:**
- `tests/conftest.py` — shared fixtures with `test_schema` (creates/drops isolated schema)
- `tests/unit/test_config.py` — 6 unit tests
- `tests/unit/test_models.py` — 4 unit tests
- `tests/integration/test_migrations.py` — 6 integration tests (subprocess approach for schema isolation)

### Critical bugs discovered and fixed during implementation:
1. **Pydantic-settings constructor kwargs override env vars** — fixed by adding `_apply_env_overrides()` that applies env vars into the merged dict before `Settings()` construction
2. **Alembic autogenerate hardcodes `schema="public"`** — fixed by replacing with `schema=_schema` referencing module-level settings variable
3. **Integration test schema isolation** — fixed by running migrations in subprocesses (fresh Python process where env vars take effect before singleton initialisation)
4. **`api.api_keys` as JSON string** — fixed by JSON-parsing values in `_apply_env_overrides()`

### What Was Produced
- 38 committed files
- 16/16 tests passing
- All 11 verification checks passing
- PR open: `feature/phase02-database-schema` → `main`

---

## Milestone Summary Table

| Event | Date | Key Artifact | Status |
|---|---|---|---|
| Environment Setup (Phase 1) | 2026-05-30 | `configs/base.yaml`, project scaffold | ✅ Merged |
| Custom slash commands | 2026-05-30 | 10 `.claude/commands/*.md` | ✅ Merged |
| Master Specification | 2026-05-30 | `master-specification.md` (2094 lines) | ✅ Merged |
| System Design Spec | 2026-05-30 | `system_design-spec.md` (1880 lines) | ✅ Merged |
| Database Schema Spec | 2026-05-31 | `database-schema-spec.md` (1933 lines) | ✅ Merged |
| Phase 2 Implementation | 2026-05-31 | 38 files, 10 tables, 16 tests | 🔄 PR open |
