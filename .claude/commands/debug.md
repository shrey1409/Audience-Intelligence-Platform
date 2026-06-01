---
description: Diagnose and fix a specific problem — reads source, checks recent changes, identifies root cause, suggests exact code fix
argument-hint: "<description of the problem>"  e.g. "ImportError when running app.core.config"
allowed-tools: Read, Glob, Bash(git:*), Bash(python3:*), Bash(docker:*)
---

<!-- CONTEXT BUDGET: ~10K tokens. Load ONLY: project_context/00_global.md + CURRENT_STATUS.md + targeted files based on problem -->

Read .claude/project_context/00_global.md for coding standards and conventions.
The user described the problem in `$ARGUMENTS`. Read it carefully before doing anything else.
Use recovery prompts in project_context/06_session_recovery.md if needed.

## Step 1 — Understand the problem category
Classify the problem into one of these categories based on the description:
- **A. Import error** — `ImportError`, `ModuleNotFoundError`, `cannot import name`
- **B. Config missing** — `KeyError`, `ValidationError`, `setting not found`, `NoneType`
- **C. Database** — `OperationalError`, `ProgrammingError`, `relation does not exist`, `column not found`
- **D. Redis** — `ConnectionRefusedError`, `redis.exceptions`, `cache miss causing crash`
- **E. ML/data** — `ValueError`, `KeyError` on DataFrame columns, shape mismatch, NaN errors
- **F. ETL** — source API failure, unexpected response schema, rate limits, incremental logic bug
- **G. Test failure** — pytest error, fixture not found, mock not called
- **H. Docker/services** — service not running, port conflict, container crash

## Step 2 — Check recent git changes
```
git log --oneline -10
git diff HEAD~1 --name-only
git diff HEAD~1 -- {most_likely_relevant_file}
```
If recent changes touch files related to the problem, read those diffs carefully — the bug is often in the most recently changed file.

## Step 3 — Read relevant source files
Based on the problem category, read:

**A (Import error):** Read the file with the failing import. Check:
- The module path is correct relative to the project root
- `__init__.py` files exist in every directory in the path
- The symbol being imported actually exists in the source file
- There are no circular imports (A imports B which imports A)

**B (Config missing):** Read `configs/base.yaml`, then `app/core/config.py`.
- Verify the key path exists in `base.yaml`
- Verify the Pydantic model mirrors the YAML structure
- Check that `dev.yaml` / `prod.yaml` don't override with incorrect types

**C (Database):** Read the relevant ORM model in `app/models/orm/` and the DDL in `sql/ddl/`.
- Check `__tablename__` matches the DDL table name
- Check `__table_args__` has the correct schema
- Check the column names match between DDL and ORM
- Check the alembic migration history if migrations are used

**D (Redis):** Read `app/core/config.py` for Redis settings, and the file that calls Redis.
- Check the Redis host/port come from config, not hardcoded
- Check TTL values come from `configs/base.yaml` redis.ttl_seconds

**E (ML/data):** Read the ML module that is failing.
- Check feature column names against `configs/base.yaml` ml.features.matrix
- Check for `.fit()` called before `.transform()`
- Check for NaN handling — are missing values imputed before the feature matrix is built?

**F (ETL):** Read the failing ingestion module in `etl/ingestion/`.
- Check the API response parsing handles optional fields
- Check incremental mode compares timestamps correctly (timezone-aware vs naive)
- Check retry logic uses tenacity with the correct exception types

**G (Test failure):** Read the test file and the module under test.
- Check fixture scope matches usage
- Check async test has `@pytest.mark.asyncio`
- Check mock patches the correct import path (where the name is used, not where it's defined)

**H (Docker):** Run:
```
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
```
This shows which services are actually running. Check if PostgreSQL (5432), Redis (6379), MLflow (5000), and Airflow (8080) are up.

## Step 4 — Run targeted diagnostic
Run the most specific diagnostic for the problem, NOT a broad restart:

```
# For import errors:
python3 -c "from {module.path} import {Symbol}" 2>&1

# For config issues:
python3 -c "from app.core.config import settings; print(settings.model_dump())" 2>&1

# For DB issues:
python3 -c "
from app.core.config import settings
print('DB schema:', settings.database.schema)
print('Pool size:', settings.database.pool_size)
" 2>&1

# For feature matrix issues:
python3 -c "
import yaml
with open('configs/base.yaml') as f:
    cfg = yaml.safe_load(f)
features = cfg['ml']['features']['matrix']
print(f'Feature count: {len(features)}')
print(features)
" 2>&1
```

## Step 5 — Identify root cause
State the root cause clearly in one sentence. Examples:
- "The ORM model uses `schema='public'` hardcoded instead of `settings.database.schema`"
- "`etl/ingestion/zephr.py` imports `UserProfile` from `app.models.orm` but that module's `__init__.py` doesn't export it"
- "The `persona_assignments` table DDL uses `public.user_profiles` instead of `{schema}.user_profiles` in the FK reference"

## Step 6 — Suggest the exact fix
Provide the precise code change needed. Show:
- File path and line number
- The current (broken) code
- The corrected code

Example format:
```
FIX: app/models/orm/persona_assignments.py, line 23

CURRENT:
    __table_args__ = {"schema": "public"}

CORRECTED:
    __table_args__ = {"schema": settings.database.schema}
```

Do NOT suggest:
- Restarting all Docker services as the first solution
- Deleting and recreating the virtual environment without evidence it's corrupted
- Wiping the database unless data loss is explicitly acceptable
- Disabling type checking or pre-commit hooks

## Step 7 — Verify the fix
After the fix is applied, run the targeted diagnostic from Step 4 again to confirm the error is resolved.

## Step 8 — Report
```
═══════════════════════════════════════════════
Debug Report
═══════════════════════════════════════════════
Problem:     {description}
Category:    {A-H} — {category name}
Root cause:  {one sentence}

Fix applied: {file_path}:{line_number}
  Before: {old code}
  After:  {new code}

Verification: {diagnostic command output — shows error is gone}

Related files to review:
  - {file that may have the same issue}
═══════════════════════════════════════════════
```
