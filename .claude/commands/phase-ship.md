---
description: Validate, commit, push, create PR, merge, clean up, and switch back to main after a phase is complete
argument-hint: "Phase number and short description e.g. '2 database-schema'"
allowed-tools: Read, Write, Glob, Bash, mcp__github__create_pull_request, mcp__github__merge_pull_request, mcp__github__delete_branch
---

<!-- CONTEXT BUDGET: ~50K tokens max. Load only files listed below. -->

You have .claude/CLAUDE.md context. Parse user input: $ARGUMENTS as phase_number and phase_slug.

## Step 1 — Validate phase
Read `.claude/specs/phase{N}-{slug}.md` if it exists. If not, ask user to run `/phase-start {N}` first.

## Step 2 — Parse arguments
From $ARGUMENTS extract:
1. `phase_number` — zero-padded to 2 digits (2 → 02)
2. `phase_slug` — lowercase kebab-case (database-schema)
3. `branch_name` — must be feature/phaseNN-phase-slug
4. `spec_path` — .claude/specs/phaseNN-phase-slug.md

If arguments are missing, read current branch name and infer them.
If you cannot infer, ask the user before proceeding.

## Step 3 — Verify current branch
Run:
```bash
git branch --show-current
```
Store as CURRENT_BRANCH.
If CURRENT_BRANCH is main, stop immediately:
"You are on main. Never ship directly from main. Switch to your feature branch first."

## Step 4 — Read the phase spec
Read `spec_path` from .claude/specs/.
Extract:
- SPEC_OVERVIEW — the objective paragraph
- DELIVERABLES — the list of files/outputs
- DEFINITION_OF_DONE — the checklist
- FILES_CREATED — every file created this phase
- FILES_MODIFIED — every file modified this phase

If spec file does not exist, warn the user but continue.

## Step 5 — Verify definition of done
For every item in DEFINITION_OF_DONE:
- Check if the file exists on disk (for file deliverables)
- Check if the module imports without error (for Python files)
Run:
```bash
python3 -c "import ast; import sys
import glob
py_files = glob.glob('**/*.py', recursive=True)
errors = []
for f in py_files:
    if 'venv' in f or '.venv' in f:
        continue
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        errors.append(f'{f}: {e}')
if errors:
    print('SYNTAX ERRORS:')
    for e in errors: print(e)
    sys.exit(1)
else:
    print('All Python files: syntax OK')
"
```
Report which items are complete and which are missing.
If any critical deliverable is missing, warn the user and ask:
"Definition of done is incomplete. Ship anyway? (yes/no)"
Stop if user says no.

## Step 6 — Run pre-commit checks
Run:
```bash
pre-commit run --all-files
```
If pre-commit fails, show the exact errors and stop:
"Pre-commit checks failed. Fix the issues above before shipping."
Do NOT auto-fix and re-run. Show the user what failed.

## Step 7 — Run tests
Run:
```bash
pytest tests/ -v --tb=short -q 2>&1 | tail -20
```
If tests fail, show failures and ask:
"Tests are failing. Ship anyway? (yes/no)"
Stop if user says no.

## Step 8 — Security check
Run these checks and stop if any match:
```bash
grep -r "password\s*=\s*['\"][^'\"]" app/ etl/ ml/ --include="*.py" | grep -v "test_" | grep -v "#"
grep -r "api_key\s*=\s*['\"][^'\"]" app/ etl/ ml/ --include="*.py" | grep -v "test_" | grep -v "#"
grep -r "secret\s*=\s*['\"][^'\"]" app/ etl/ ml/ --include="*.py" | grep -v "test_" | grep -v "#"
```
If any hardcoded secrets found, stop immediately:
"Hardcoded secret detected. Remove it before shipping."

## Step 9 — Generate commit message
Run:
```bash
git diff --staged
git diff
git log main..HEAD --oneline
```
Select the conventional commit prefix based on phase type:
- Phase 1 (environment, scaffold): chore
- Phase 2, 3 (database, data): feat
- Phase 4, 5 (etl, features): feat
- Phase 6, 7 (ml, training): feat
- Phase 8 (api, serving): feat
- Phase 9+ (docker, ci, tests, docs): chore or docs

Format: `<prefix>: phase <N> — <plain english description of what works now>`
Example: `feat: phase 2 — 9 database tables, ORM models, and docker services`

Rules:
- Lowercase only
- No period at end
- Under 72 characters
- Describes what the system can DO now, not what files were changed

## Step 10 — Stage and commit
```bash
git add -A
git commit -m "<generated-message>"
```
Report: "✓ Committed — <message>"

## Step 11 — Push to feature branch
```bash
git push -u origin CURRENT_BRANCH
```
Report: "✓ Pushed — <CURRENT_BRANCH>"

## Step 12 — Create PR via GitHub MCP
Use mcp__github__create_pull_request to create a PR from CURRENT_BRANCH into main.

Title format: "Phase <N> — <plain english phase name>"
Example: "Phase 2 — Database Schema and Docker Services"

PR Body:
```markdown
## Phase <N> — <Phase Name>

### What this phase delivers
<SPEC_OVERVIEW paragraph>

### Files created (<count>)
<bullet list of FILES_CREATED with one-line description each>

### Files modified (<count>)
<bullet list of FILES_MODIFIED with one-line description each>

### Database changes
<list any new tables or schema changes, or "No database changes">

### ML changes
<list any new features, algorithms, or pipeline changes, or "No ML changes">

### Definition of done
<DEFINITION_OF_DONE checklist with every item marked [x]>

### How to validate
<list the make commands or python commands to verify this phase works>
```

Report: "✓ PR created — <PR URL>"

If GitHub MCP is not connected, stop and say:
"GitHub MCP is not connected. Connect it via /mcp then retry.
Alternatively, open this URL to create the PR manually:
https://github.com/shrey1409/Audience-Intelligence-Platform/compare/CURRENT_BRANCH"

## Step 13 — Merge PR via GitHub MCP
Use mcp__github__merge_pull_request to merge using SQUASH merge.
Report: "✓ PR merged to main — squash merge"

## Step 14 — Delete remote branch via GitHub MCP
Use mcp__github__delete_branch to delete CURRENT_BRANCH from GitHub.
Report: "✓ Remote branch deleted — <CURRENT_BRANCH>"

## Step 15 — Switch to main and pull latest
```bash
git checkout main
git pull origin main
```
Report: "✓ Switched to main — up to date"

## Step 16 — Delete local feature branch
```bash
git branch -D CURRENT_BRANCH
```
Report: "✓ Local branch deleted — <CURRENT_BRANCH>"

## Step 17 — Update CLAUDE.md phase tracker
Read .claude/CLAUDE.md.
Find the phase tracker section.
Mark Phase <phase_number> as ✅ complete.
Write the updated file back.
Report: "✓ CLAUDE.md updated — Phase <N> marked complete"

## Final summary
Print exactly:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
/phase-ship complete ✅
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
✓ Syntax check passed
✓ Pre-commit passed
✓ Tests passed
✓ Committed — <message>
✓ Pushed — <branch>
✓ PR created and merged (squash)
✓ Remote branch deleted
✓ Switched to main — up to date
✓ Local branch deleted
✓ CLAUDE.md phase tracker updated
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Next phase: run /phase-start <N+1> <phase-name>
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

## Hard rules
- Never commit directly to main
- Always squash merge
- Always delete both remote and local branch after merge
- Stop if GitHub MCP is not connected — never skip PR creation
- Stop if hardcoded secrets are detected
- Stop if pre-commit fails — never auto-fix silently
- Never proceed to merge if PR creation fails
- Always update CLAUDE.md phase tracker after successful ship
