# Development Workflow — Audience Intelligence Platform

**Document Type:** Workflow Reference
**Created:** 2026-05-31
**Last Updated:** 2026-05-31

---

## Overview

This project uses a **spec-first, phase-by-phase development workflow** enforced through Claude Code slash commands. Every phase follows the same sequence: spec → branch → implement → validate → PR → merge → next phase.

The workflow is designed to ensure:
- No architectural decisions are made ad-hoc during implementation
- Every phase starts from a clean `main` branch
- Every phase ends with a merged PR and updated phase tracker
- Context is never lost between Claude sessions

---

## The Phase Lifecycle

```
main ──► /phase-start N name ──► feature/phaseN-name ──► implement ──► /validate-phase ──► /phase-ship ──► main
```

### Step-by-Step

1. **Check current status**: Read `project_journal/CURRENT_STATUS.md`
2. **Start the phase**: Run `/phase-start N phase-name`
   - Pulls latest main
   - Creates `feature/phaseN-phase-name` branch
   - Generates phase spec to `.claude/specs/phaseNN-phase-name.md`
3. **Review the spec**: Read the generated spec before writing any code
4. **Implement**: Build files in the order specified in the spec
5. **Validate**: Run `/validate-phase` to check all DoD items
6. **Fix any failures**: Never skip a failing check
7. **Ship**: Run `/phase-ship N specification-file`
   - Runs pre-commit
   - Runs tests
   - Checks for hardcoded secrets
   - Creates and merges PR (squash merge)
   - Deletes branches
   - Updates CLAUDE.md phase tracker

---

## Custom Slash Commands

All commands live in `.claude/commands/`. They are multi-step prompts that Claude Code executes as a structured workflow.

### Core Phase Commands

| Command | Usage | Purpose |
|---|---|---|
| `/phase-start N name` | `/phase-start 3 synthetic-data` | Begin a new phase — creates branch + spec |
| `/phase-ship N spec-name` | `/phase-ship 2 database-schema` | Ship a completed phase — validate, PR, merge |
| `/phase-commit` | `/phase-commit` | Mid-phase checkpoint commit without merging |
| `/create-spec N name` | `/create-spec 2 database-schema` | Generate phase spec from master spec |
| `/validate-phase` | `/validate-phase` | Run all DoD checks for current phase |

### Quality Commands

| Command | Usage | Purpose |
|---|---|---|
| `/db-check` | `/db-check` | Verify DDL ↔ ORM column parity for all tables |
| `/ml-check` | `/ml-check` | Validate 46 features, 9 personas, propensity weights |
| `/build-file path` | `/build-file app/services/persona_service.py` | Build a single file completely from spec |
| `/test-gen module` | `/test-gen etl/ingestion/zephr.py` | Generate comprehensive pytest tests |
| `/debug` | `/debug` | Load full project context from CLAUDE.md |

### Ultra Planning Mode

For complex architectural decisions, use Ultra Planning Mode via the `/ultraplan` command. This spawns a cloud-based multi-agent planning session that:
1. Reads all relevant spec files
2. Cross-references requirements
3. Produces an implementation plan
4. Waits for user approval before generating any code

**When to use ultraplan:**
- Before creating a new major specification
- When multiple valid architectural approaches exist
- When the scope exceeds a single session's context
- For cross-cutting concerns that affect multiple phases

---

## Branch Naming Convention

```
feature/phaseN-short-name    Phase work (e.g. feature/phase02-database-schema)
fix/short-description        Bug fixes (e.g. fix/alembic-schema-injection)
chore/short-description      Non-feature work (e.g. chore/update-spec-alias)
```

Always branch from `main`. Always PR back to `main`. Squash merge only.

---

## Pre-commit Hooks

All commits run these checks automatically:
- `trim trailing whitespace` — removes trailing spaces
- `fix end of files` — ensures files end with newline
- `check yaml` — validates YAML syntax
- `check json` — validates JSON syntax
- `check for added large files` — blocks accidental binary commits
- `check for merge conflicts` — blocks unresolved conflict markers
- `detect private key` — scans for API key patterns
- `don't commit to branch` — blocks direct commits to `main`
- `black` — auto-formats Python to 88-char line length
- `isort` — sorts imports (profile=black)
- `flake8` — linting (E501 line length, F401 unused imports, etc.)

**If pre-commit auto-formats files:** Stage the formatted files and re-run the commit. This is expected on first commit of a new file.

---

## Coding Standards

### Python
- Type hints on every function signature (including return types)
- No `Any` types — use proper generics or `Union`
- Google-style docstrings for all public functions (Args, Returns, Raises)
- Maximum 50 lines per function; decompose if longer
- `f-strings` only (no `.format()` or `%`)
- No bare `except:` — always catch specific exceptions

### SQL
- `{schema}` placeholder in ALL table references in DDL files
- No `SELECT *` — always name columns explicitly
- Named constraints: `pk_tablename`, `fk_table_ref`, `idx_table_column`, `uq_table_column`, `chk_table_column`

### Configuration
- All tunable values in `configs/base.yaml`
- Access via `settings.*` — never hardcode
- Secrets (URLs, API keys, passwords) only in `.env` (gitignored)
- Client overrides in `configs/clients/{client}.yaml` (gitignored)

### Logging
- `structlog` for all logging — no bare `print()` in production code
- Every pipeline step logs at start and end with: `step_name`, `start_time`, `rows_processed`, `status`

---

## Environment Setup (Quick Reference)

```bash
# 1. Clone repository
git clone https://github.com/shrey1409/Audience-Intelligence-Platform.git
cd "Audience Intelligence platform"

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Configure environment
cp .env.example .env
# Edit .env: set DATABASE__URL and other required vars

# 6. Start Docker services
docker compose up -d postgres redis

# 7. Run migrations
PYTHONPATH=. python3 scripts/run_migrations.py

# 8. Verify setup
python3 -c "from app.core.config import settings; print(settings.database.schema)"
python3 -c "from app.models.orm import *; print('ORM OK')"
PYTHONPATH=. python3 -m pytest tests/unit/ -v
PYTHONPATH=. python3 -m pytest tests/integration/ -v
```

---

## Session Continuity Protocol

When starting a new Claude Code session on this project:

```
1. Read: project_journal/CURRENT_STATUS.md
2. Read: .claude/CLAUDE.md
3. Ask Claude: "Read .claude/CLAUDE.md and tell me the current phase status"
4. Run: git status && git log --oneline -5
5. Continue from last known state
```

When ending a session:
```
1. Commit any in-progress work (even partial) to the feature branch
2. Update project_journal/CURRENT_STATUS.md
3. If a session log entry is warranted, add to project_journal/session_logs/
```
