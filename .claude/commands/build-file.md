---
description: Build a single project file completely — no TODOs, no placeholders, fully implemented
argument-hint: <relative_file_path>  e.g. "app/core/config.py"
allowed-tools: Read, Write, Glob, Bash(git:*), Bash(python3:*)
---

<!-- CONTEXT BUDGET: ~15K tokens. Load ONLY: project_context/00_global.md + CURRENT_STATUS.md + configs/base.yaml + target file -->

Read .claude/project_context/00_global.md for coding standards.
Read .claude/CURRENT_STATUS.md for phase context.
The user passed `$ARGUMENTS` as the file path to build (relative to project root).

## Step 1 — Load config context
Read `configs/base.yaml` — this is the single source of truth for all config values.
Never hardcode values that appear in this file. Reference them via the settings object.

## Step 2 — Identify related files
Based on the target file path, use Glob to find related files to read for consistency:
- If building `app/models/orm/X.py` → read `sql/ddl/X.sql` (matching table DDL), `app/models/orm/__init__.py`
- If building `app/core/config.py` → read `configs/base.yaml`, `app/core/__init__.py`
- If building `app/api/v1/endpoints/X.py` → read the matching `app/services/X.py` and `app/schemas/X.py`
- If building `etl/ingestion/X.py` → read `configs/base.yaml` etl.sources.X section, `etl/__init__.py`
- If building `ml/X.py` → read `configs/base.yaml` ml section thoroughly
- Always read `app/core/__init__.py` to understand what's exported from core

## Step 3 — Check if file already exists
If the target file already exists and has content beyond a `.gitkeep` or empty `__init__.py`, warn the user:
```
WARNING: {path} already exists with {N} lines of content.
Proceeding will overwrite it. Reading current content first...
```
Then read the existing file.

## Step 4 — Build the file
Write the complete, production-ready file. Enforce these rules:

**Python files must:**
- Have type hints on every function and method signature
- Use structlog for logging: `log = structlog.get_logger(__name__)`
- Read config via the settings object (from `app/core/config.py`), never from `os.environ` directly
- Use SQLAlchemy 2.0 style: `select()`, `Session.scalars()`, `async with session` patterns
- Have no `TODO`, `FIXME`, `pass` (except abstract methods), or placeholder strings
- Have no bare `except:` — always catch specific exception types
- Have no `print()` statements — use structlog

**ORM model files must:**
- Import settings from `app.core.config`
- Set `__tablename__` to match the DDL table name exactly
- Set `__table_args__ = {"schema": settings.database.schema}`
- Define every column that exists in the corresponding DDL
- Use correct SQLAlchemy 2.0 `Mapped[type]` annotations
- Define `__repr__` method

**SQL DDL files must:**
- Use `{schema}` placeholder in `CREATE TABLE {schema}.table_name`
- Include `CREATE INDEX` statements for foreign keys and common query patterns
- Include comments on non-obvious columns

**Config/core files must:**
- Use Pydantic `BaseSettings` or `BaseModel`
- Map every section of `configs/base.yaml` to a typed model
- Never set default values for secrets (database URL, API keys)

**ETL ingestion files must:**
- Read source config from `configs/base.yaml` etl.sources section
- Implement incremental vs full_refresh logic based on the mode in config
- Use structlog with bound context: `log.bind(source="sourcename", run_id=run_id)`
- Handle API errors with tenacity retry logic

## Step 5 — Syntax check
After writing, run:
```
python3 -m py_compile {file_path} && echo "Syntax OK"
```
If it fails, fix the syntax error and rewrite the file. Report the result.

## Step 6 — Report
```
✓ Built: {file_path}
  Lines: {N}
  Syntax: OK

Functions/classes defined:
  - ClassName
  - function_name(args) -> return_type

Next steps:
  - Run /test-gen {file_path} to generate tests
  - Or continue with next deliverable from .claude/specs/
```
