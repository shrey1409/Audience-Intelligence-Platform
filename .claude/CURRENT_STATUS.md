# Current Status — Audience Intelligence Platform

**Last updated:** 2026-06-01 16:00 UTC
**Current phase:** 3 — Synthetic Data Generation (NOT STARTED)
**Current branch:** main (clean)

## Completed Phases

- Phase 1: Environment Setup ✅ — merged to main
- Phase 2: Database Schema ✅ — merged to main
  - 10 tables (9 source + ga4_identity_bridge)
  - 64-column feature_store
  - 16/16 tests passing
  - 4 bugs fixed during verification

## Phase 2 Watch-Outs for Future Phases

- **importlib.reload() does not work for schema override in tests** — use subprocess
- **Pydantic-settings constructor kwargs override env vars** — fixed in config.py
- **Docker volume reset:** `docker compose down -v` for clean slate
- **Alembic schema must come from settings, never hardcoded**

## Context Optimization Complete

- **CLAUDE.md:** 61 lines (was 189)
- **4 reference files** in .claude/specs/reference/
- **Large specs archived** in .claude/archive/
- **All 10 commands optimized** for conditional reading
- **Baseline session context:** ~18K tokens (was 59K, 69% reduction)

---

## Phase 2 — Key Decisions Made

### Database & ORM
- **asyncpg==0.29.0** added to requirements/base.txt for async PostgreSQL
- **Alembic uses dynamic schema** from `settings.database.schema` (not hardcoded "public")
- **Schema parameter in all ORM models:** `__table_args__ = {"schema": settings.database.schema}`
- **VARCHAR + CHECK constraints** used for all enum-like columns (not PostgreSQL ENUM type for portability)

### Tables & Constraints
- **10 tables total:** 8 source staging tables + feature_store + persona_assignments
- **Primary keys on all tables:** Most are (user_id) or (user_id, source_id) for uniqueness
- **UNIQUE constraints enabled ON CONFLICT upserts** in feature_store and persona_assignments
- **Foreign keys with CASCADE:** persona_assignments.user_id → user_profiles.user_id
- **ga4_identity_bridge added as 10th table** (unexpected but necessary for resolving user_pseudo_id → user_id)

### Configuration & Secrets
- **Schema name configured per client:** `configs/clients/{client}.yaml` under `database.schema`
- **Development default schema:** "public" (in configs/base.yaml)
- **Connection pooling:** SQLAlchemy AsyncEngine with pool_size=20, max_overflow=10
- **No secrets in any config file:** All env vars via docker-compose.yml

---

## Known Issues / Watch-Outs for Future Phases

### Test & Config Gotchas
1. **importlib.reload() does NOT work for schema override in tests**
   - Reason: Config is singleton; reload() doesn't reset Pydantic state
   - Workaround: Use subprocess to run tests in separate process (pytest subprocess plugin or custom fixture)
   - Impact: Phase 3+ integration tests must use subprocess isolation

2. **Pydantic-settings constructor kwargs override env vars**
   - Reason: Pydantic v2 changed precedence order
   - Fix applied: Config class uses env_file + .env fallback, not kwargs override
   - Location: app/core/config.py `class Settings(BaseSettings)`

3. **Docker volume persistence across runs**
   - Clean slate requires: `docker compose down -v` (not just `down`)
   - Reason: Postgres data persists in named volume; breaking tests if old schema exists
   - Watch-out: CI may need explicit volume cleanup between test runs

### Schema & Migration Quirks
4. **Alembic auto-generate can miss UNIQUE constraints on composite keys**
   - Workaround: Hand-edit migration files if needed
   - Check: `pytest tests/integration/test_schema_isolation.py` after migration

5. **ON CONFLICT upserts require UNIQUE constraint**
   - feature_store uses: `ON CONFLICT (user_id) DO UPDATE SET ...`
   - persona_assignments uses: `ON CONFLICT (user_id) DO UPDATE SET ...`
   - These tables MUST have UNIQUE constraints or upserts fail silently

6. **CASCADE DELETE can orphan data if not carefully ordered**
   - user_sessions → user_profiles (CASCADE)
   - persona_assignments → feature_store (no CASCADE, explicit FK)
   - Watch-out when dropping test data

### Phase 3+ Blockers (Known Before Starting)
7. **GA4 identity resolution requires user_pseudo_id → user_id mapping**
   - This mapping comes from login events (ga4_identity_bridge table)
   - If users never log in, GA4 features will have low coverage
   - Plan: Cold-start rules handle this (F-25 in master-spec)

8. **Transunion demographics have low coverage (~70%) with match_confidence filter (0.70+)**
   - F-05 in spec requires excluding low-confidence matches
   - Feature store must set age_score, income_score, has_children = 0 for excluded users
   - This is correct behavior (zero imputation per F-08)

---

## Context Window Optimization (Just Applied)

Created `.claude/specs/reference/` directory with 4 focused files:
- **personas.md** — 9 personas, activation strategies
- **kpis.md** — All thresholds, alert levels, config defaults
- **data-sources.md** — 8 ETL sources, coverage, identity resolution
- **engineering-standards.md** — Python, SQL, API, ML, Git standards

**Impact:** Reduced context from ~44K tokens (master-spec) to ~26K tokens (4 reference files)

Updated `.claude/commands/create-spec.md` to reference only:
1. .claude/CLAUDE.md
2. configs/base.yaml
3. .claude/specs/ (list files, don't read each one)

---

## Next Action

### Immediate (Before Phase 3)
1. Clean working directory: commit or discard `project_journal/` directory
2. Review Phase 2 spec one more time: `.claude/specs/phase02-database-schema.md`
3. Merge feature/phase2-database-schema → main (requires PR approval)

### Phase 3 Setup
```bash
# After Phase 2 is merged to main:
/create-spec 3 synthetic-data
```

This will create `.claude/specs/phase03-synthetic-data.md` and branch `feature/phase03-synthetic-data`

---

## Useful Commands Reference

### Local Development
```bash
# Start services
docker compose up -d

# Run tests
pytest tests/ -v
pytest tests/integration/test_schema_isolation.py -v

# Clean slate (warning: deletes data!)
docker compose down -v && docker compose up -d

# Check linting
pre-commit run --all-files

# Reset a single migration
alembic downgrade -1 && alembic upgrade head
```

### Git
```bash
# Current status
git status

# List branches
git branch -a

# After Phase 2 merge, switch to next
git checkout main && git pull && /phase-start
```

---

## Files Modified This Session
- ✅ `.claude/CLAUDE.md` — added "Quick Reference" section
- ✅ `.claude/commands/create-spec.md` — slimmed mandatory reading
- ✅ `.claude/specs/reference/personas.md` — created
- ✅ `.claude/specs/reference/kpis.md` — created
- ✅ `.claude/specs/reference/data-sources.md` — created
- ✅ `.claude/specs/reference/engineering-standards.md` — created
- ➕ `.claude/CURRENT_STATUS.md` — this file

---

## How to Use This File

**At the start of each session:**
```
1. Read .claude/CLAUDE.md (core standards, folder structure)
2. Read .claude/CURRENT_STATUS.md (where we are, known gotchas, next steps)
3. Then proceed with the task
```

**When starting a new phase:**
```
1. Check "Next Action" section of this file
2. Review the phase spec: .claude/specs/phaseN-*.md
3. Update CURRENT_STATUS.md when decisions are made or issues discovered
```

**To report a new gotcha:**
Add to "Known Issues / Watch-Outs" section with:
- Brief description
- Reason (why it happens)
- Workaround (how to avoid it)
- Impact (which future phases affected)
