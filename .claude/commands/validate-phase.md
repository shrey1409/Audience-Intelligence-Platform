---
description: Validate all deliverables for a phase — file presence, syntax, tests, no hardcoded values, no secrets
argument-hint: <phase_number>  e.g. "2"
allowed-tools: Read, Write, Glob, Bash(git:*), Bash(python3:*), Bash(pytest:*)
---

<!-- CONTEXT BUDGET: ~50K tokens max. Load only files listed below. -->

You have .claude/CLAUDE.md context. Read the phase spec below.

The user passed `$ARGUMENTS` as the phase number (e.g. "2").

## Step 1 — Load phase spec
Find and read `.claude/specs/phase{N}-*.md`. If no spec file exists for this phase, stop and tell the user to run `/phase-start {N} {name}` first.

Extract every item from the **Deliverables** checklist.

## Step 2 — Check deliverables exist on disk
For each file listed in the spec's Deliverables section:
- Check if the file exists using Read (will error if missing)
- Check the file has real content (not just a `.gitkeep` or empty `__init__.py`)
- Record: PASS or FAIL with the file path

## Step 3 — Python syntax check
For every `.py` file created this phase (from the deliverables list):
```
python3 -m py_compile {file_path}
```
Record PASS or FAIL per file.

## Step 4 — Run tests
Run pytest on tests related to this phase:
```
pytest tests/unit/ -v --tb=short -q 2>&1 | tail -30
```
If integration tests exist for this phase:
```
pytest tests/integration/ -v --tb=short -q -k "phase{N}" 2>&1 | tail -30
```
Record: tests passed / failed / errors.

## Step 5 — Check for hardcoded values
Grep for common hardcoding patterns across all Python files created this phase:
```
grep -rn --include="*.py" -E "(password|secret|api_key|token)\s*=\s*['\"][^'\"]{4,}" {file_paths}
grep -rn --include="*.py" -E "localhost|127\.0\.0\.1|5432|6379" {file_paths}
grep -rn --include="*.py" -E "schema\s*=\s*['\"]public['\"]" {file_paths}
```
Any match is a FAIL — the value must come from `configs/base.yaml` via settings.

## Step 6 — Check for committed secrets
Grep for secret patterns:
```
grep -rn --include="*.py" --include="*.yaml" --include="*.sql" \
  -E "(BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)" \
  app/ etl/ ml/ sql/ configs/ 2>/dev/null
```
Any match is a FAIL — stop and alert the user immediately.

## Step 7 — Check {schema} placeholder in DDL files
For every `.sql` file in `sql/ddl/` created this phase:
```
grep -L "{schema}" sql/ddl/*.sql 2>/dev/null
```
Any file missing `{schema}` is a FAIL.

## Step 8 — Check ORM model __table_args__
For every ORM model file in `app/models/orm/` created this phase:
```
grep -L "__table_args__" app/models/orm/*.py 2>/dev/null
```
Any file missing `__table_args__` is a FAIL.

## Step 9 — Check acceptance criteria from spec
Go through each acceptance criterion in the spec and evaluate it. Mark PASS, FAIL, or SKIP (if prerequisite not met).

## Step 10 — Report
Print a formatted summary:

```
═══════════════════════════════════════════════
Phase {N} Validation Report
═══════════════════════════════════════════════

DELIVERABLES
  ✓ app/models/orm/user_profiles.py — exists, 87 lines
  ✗ sql/ddl/user_sessions.sql — FILE MISSING

SYNTAX CHECK
  ✓ app/models/orm/user_profiles.py — OK
  ✗ app/models/orm/subscriptions.py — SyntaxError line 42

TESTS
  ✓ 14 passed, 0 failed, 0 errors

HARDCODED VALUES
  ✓ No hardcoded secrets or connection strings found

COMMITTED SECRETS
  ✓ No secret patterns found

DDL {schema} PLACEHOLDERS
  ✓ All DDL files contain {schema}

ORM __table_args__
  ✗ app/models/orm/feature_store.py — missing __table_args__

ACCEPTANCE CRITERIA
  ✓ All ORM models have schema parameter
  ✗ pytest passes with 0 failures — 2 failures found

═══════════════════════════════════════════════
RESULT: FAIL — 3 issues must be resolved before committing

NEXT STEPS:
1. Create missing: sql/ddl/user_sessions.sql
2. Fix SyntaxError in app/models/orm/subscriptions.py line 42
3. Add __table_args__ to app/models/orm/feature_store.py
═══════════════════════════════════════════════
```

Do not suggest running `/phase-commit` until all checks are PASS.
