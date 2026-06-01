---
description: Start a new phase — pull main, create feature branch, generate phase spec, save to .claude/specs/
argument-hint: <phase_number> <phase-name>  e.g. "3 etl-ingestion"
allowed-tools: Read, Write, Glob, Bash(git:*), Bash(python3:*)
---

<!-- CONTEXT BUDGET: ~12K tokens. Load ONLY: project_context/00_global.md + CURRENT_STATUS.md + configs/base.yaml -->

Read .claude/project_context/00_global.md for git conventions and standards.
Read .claude/CURRENT_STATUS.md for current phase and blockers.

The user has passed two arguments: `$ARGUMENTS` — parse them as `PHASE_NUMBER` (first token) and `PHASE_NAME` (remaining tokens joined with hyphens, lowercase).

## Step 1 — Validate git state
Run `git status --short`. If the working tree is not clean (any modified or untracked files shown), stop and tell the user to commit or stash their changes first.

## Step 2 — Pull latest main
```
git checkout main
git pull origin main
```
If either command fails, report the error and stop.

## Step 3 — Create feature branch
Branch name format: `feature/phase{PHASE_NUMBER}-{PHASE_NAME}`
```
git checkout -b feature/phase{PHASE_NUMBER}-{PHASE_NAME}
```
If the branch already exists, ask the user whether to check it out or abort.

## Step 4 — Read context
Read the following files to inform the spec:
- `configs/base.yaml` — all configuration values (features, personas, ETL sources, thresholds)
- The previous phase spec if it exists at `.claude/specs/phase{PHASE_NUMBER-1}-*.md`
- Any existing files in the directories relevant to this phase (use Glob to find them)

## Step 5 — Generate phase spec
Write a spec file to `.claude/specs/phase{PHASE_NUMBER}-{PHASE_NAME}.md` with this exact structure:

```markdown
# Phase {N}: {Name} Spec

## Objective
<One paragraph: what this phase accomplishes and why it matters to the platform>

## Deliverables
List every file that must exist when this phase is COMPLETE:
- [ ] path/to/file1.py — what it does
- [ ] path/to/file2.py — what it does
(Be exhaustive. Reference the folder structure in CLAUDE.md.)

## Files to Create (new)
- path/to/new_file.py

## Files to Modify (existing)
- path/to/existing_file.py — what changes

## Acceptance Criteria
Each item must be objectively verifiable:
- [ ] All 9 ORM models have __table_args__ with schema parameter
- [ ] pytest tests/unit/ passes with 0 failures
- [ ] No hardcoded values (grep for magic numbers/strings returns nothing)
- [ ] All SQL DDL files contain {schema} placeholder
(Add phase-specific criteria)

## Dependencies
- External: list any Docker services required (PostgreSQL, Redis, MLflow, Airflow)
- Internal: list any modules from prior phases this phase builds on

## Risks
- Risk 1: description → mitigation
- Risk 2: description → mitigation

## Estimated Effort
<S / M / L / XL with brief rationale>

## Config Values Used (from configs/base.yaml)
List every config key this phase will read, e.g.:
- database.schema → used in __table_args__ of every ORM model
- ml.features.matrix → 46 feature names
```

## Step 6 — Report
Print:
```
✓ Branch created: feature/phase{N}-{name}
✓ Spec saved:     .claude/specs/phase{N}-{name}.md

Next: review the spec, then use /build-file to implement each deliverable.
```
