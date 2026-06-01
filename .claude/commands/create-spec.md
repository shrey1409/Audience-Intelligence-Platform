---
description: Create a detailed spec document and feature branch for the next Audience Intelligence Platform feature
argument-hint: "Phase number and feature name e.g. '2 database-schema' or '9 ml-training-pipeline'"
allowed-tools: Read, Write, Glob, Bash(git:*)
---

<!-- CONTEXT BUDGET: ~15K tokens. Load ONLY: project_context/00_global.md + CURRENT_STATUS.md + configs/base.yaml -->

You are a Principal ML Engineer and Technical Architect building the Audience Intelligence Platform.
Read .claude/project_context/00_global.md for rules, standards, and phase tracker.
Read .claude/CURRENT_STATUS.md for current phase and known issues.

User input: $ARGUMENTS

## Step 1 — Check working directory is clean
Run:
```bash
git status
```
Check for any uncommitted, unstaged, or untracked files.
If any exist, stop immediately and tell the user:
"Working directory is not clean. Please commit or stash your changes before creating a new spec."
DO NOT CONTINUE until the working directory is clean.

## Step 2 — Parse the arguments
From $ARGUMENTS extract:

1. `phase_number` — zero-padded to 2 digits: 2 → 02, 11 → 11
2. `feature_title` — human readable title in Title Case
   - Example: "Database Schema" or "ML Training Pipeline"
3. `feature_slug` — git and file safe slug
   - Lowercase, kebab-case
   - Only a-z, 0-9 and hyphens
   - Maximum 40 characters
   - Example: database-schema, ml-training-pipeline
4. `branch_name` — format: feature/phase<phase_number>-<feature_slug>
   - Example: feature/phase02-database-schema
5. `spec_filename` — format: phase<phase_number>-<feature_slug>.md
   - Example: phase02-database-schema.md

If you cannot infer all five from $ARGUMENTS, ask the user to clarify before proceeding.

## Step 3 — Check branch name is not taken
Run:
```bash
git branch -a
```
If branch_name already exists locally or remotely, append -v2, -v3 etc.
Report to the user which branch name will be used.

## Step 4 — Switch to main and pull latest
Run:
```bash
git checkout main
git pull origin main
```
Confirm main is up to date before branching.

## Step 5 — Create and switch to the feature branch
Run:
```bash
git checkout -b <branch_name>
```
Report: "✓ Created and switched to <branch_name>"

## Step 6 — Research the codebase thoroughly
Read these files before writing a single word of the spec:

Core context (always read):
1. .claude/CLAUDE.md — project rules, phase tracker, conventions
2. configs/base.yaml — canonical config (features, weights, thresholds)
3. .claude/specs/ — list files only to check for duplicates; do NOT read each file

Phase-specific files to read based on phase_number:
- If phase 02 (database): read sql/ddl/ directory, app/models/orm/ directory
- If phase 03 (synthetic data): read sql/ddl/ all files, scripts/ directory
- If phase 04-05 (ETL): read etl/ directory, sql/ddl/ all files, app/models/orm/ all files
- If phase 06-07 (ML): read ml/ directory, configs/base.yaml ml section, etl/transforms/
- If phase 08 (API): read app/ directory, app/models/orm/ all files, ml/inference/
- If phase 09+ (docker, CI, monitoring): read docker/ directory, .github/workflows/, Makefile

Check .claude/CLAUDE.md phase tracker.
If this phase is already marked complete, warn the user and stop:
"Phase <phase_number> is already marked complete in CLAUDE.md. Are you sure you want to create a new spec for it?"

## Step 7 — Identify what already exists
Before writing the spec, inventory the current state:
- Run: find . -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" | sort
- Run: find . -name "*.sql" | sort
- Note which target files already exist vs need to be created

## Step 8 — Write the spec
Generate the spec document using this exact structure. Be specific — no vague statements, no placeholders, no TODOs in the spec itself.

---
# Spec: Phase <phase_number> — <feature_title>

## Overview
Two paragraphs:
1. What this phase builds and why it exists at this point in the AIP roadmap
2. How it connects to the phase before it and enables the phase after it

## Phase position
- Previous phase: <phase_number - 1> — <name> — <status: complete/not started>
- This phase: <phase_number> — <feature_title>
- Next phase: <phase_number + 1> — <name>

## Depends on
List every prior phase and specific file/output this phase requires to already exist.
Be specific: "Requires sql/ddl/001_create_zephr_users.sql to exist and PostgreSQL to be running"

## System context
Which of the three core systems does this phase belong to:
- Data Platform (ETL, feature engineering, synthetic data)
- ML Platform (training, evaluation, MLflow, propensity scores)
- Serving Platform (FastAPI, Redis, cold-start, Airflow DAG)

## Database changes
Any new tables, columns, indexes, or constraints.
Always cross-reference against existing sql/ddl/ files before writing.
Reference the exact {schema} placeholder pattern from existing DDL files.
If none: state "No database changes in this phase."

## New API endpoints
For each new endpoint:
- METHOD /api/v1/path — description — auth required (yes/no)
- Request schema (Pydantic model name)
- Response schema (Pydantic model name)
- Redis cache involved (yes/no, TTL)
If none: state "No new API endpoints in this phase."

## ML changes
Any new algorithms, features, pipelines, or MLflow experiments.
Reference configs/base.yaml for feature names and algorithm parameters.
If none: state "No ML changes in this phase."

## Configuration changes
Any new keys needed in configs/base.yaml or configs/clients/example.yaml.
State the exact YAML path: e.g. "ml.clustering.new_parameter: default_value"
If none: state "No configuration changes in this phase."

## Files to create
List every new file with:
- Full path from project root
- One-line description of what it contains
- Key functions/classes it must implement (names only, no signatures yet)

## Files to modify
List every existing file that changes with:
- Full path
- What specifically changes and why

## New dependencies
Any new packages to add to requirements/base.txt or requirements/dev.txt.
State exact package name and version.
If none: state "No new dependencies."

## Implementation rules
Rules Claude must follow during implementation of this phase.
Always include the universal rules:
- All parameters read from configs/base.yaml — never hardcode
- All SQL uses {schema} placeholder — never hardcode schema name
- All functions have type hints and Google-style docstrings
- No bare except — always catch specific exceptions
- Structured logging on every function entry and exit
- No real credentials anywhere in code

Plus phase-specific rules based on what is being built.

For database phases add:
- Every ORM model must have __table_args__ with schema parameter
- Every DDL file must have a matching ORM model

For ML phases add:
- random_state=42 on every algorithm
- Every training run logged to MLflow with params, metrics, and artifacts
- Scaler fitted once and saved as MLflow artifact — never re-fitted on inference data

For API phases add:
- Never return raw SQLAlchemy ORM objects — always use Pydantic schemas
- Every endpoint has error handling for missing user_id (cold-start path)
- Redis cache checked before database on every read

For ETL phases add:
- Every ingestion module validates row counts against prior run
- Identity resolution logs unresolved rate per source
- All null values imputed with 0 for numeric features

## Definition of done
A specific, testable checklist. Every item must be verifiable by running a command.
Format each item as:
- [ ] <specific check> — verified by: <exact command or action>

Always include:
- [ ] All new Python files pass syntax check — verified by: python3 -m py_compile <file>
- [ ] All new Python files pass pre-commit — verified by: pre-commit run --all-files
- [ ] All new tests pass — verified by: pytest tests/ -v
- [ ] No hardcoded values — verified by: grep -r "hardcoded_pattern" app/ etl/ ml/
- [ ] configs/base.yaml validates — verified by: python3 -c "import yaml; yaml.safe_load(open('configs/base.yaml'))"

Then add phase-specific checks. Examples:
- [ ] PostgreSQL table exists — verified by: docker exec -it aip_postgres psql -U aip_user -c "\dt {schema}.*"
- [ ] API endpoint returns 200 — verified by: curl http://localhost:8000/api/v1/health
- [ ] MLflow experiment visible — verified by: open http://localhost:5000
- [ ] Synthetic data generated — verified by: python3 -c "import pandas as pd; df=pd.read_csv('data/synthetic/users.csv'); print(len(df))"
- [ ] Feature matrix has exactly 46 columns — verified by: python3 scripts/validate_features.py

## Estimated effort
State realistic time estimate based on complexity and phase scope.

## Risk flags
List any risks specific to this phase:
- What could go wrong
- What dependency might not be ready
- What assumption might not hold
---

## Step 9 — Save the spec
Save to: .claude/specs/<spec_filename>

Confirm the file was written:
```bash
cat .claude/specs/<spec_filename> | head -20
```

## Step 10 — Report to the user
Print this exact format:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
/create-spec complete ✅
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Spec saved:   .claude/specs/<spec_filename>
Branch:       <branch_name>
Phase:        <phase_number> — <feature_title>
Files to create: <count from Files to create section>
Files to modify: <count from Files to modify section>
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Next step: Review .claude/specs/<spec_filename>
then tell Claude: "implement phase <phase_number>"
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
