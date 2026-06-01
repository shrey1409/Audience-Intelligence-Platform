---
description: Commit and push all phase changes — validates clean state, runs pre-commit, uses conventional commit format
argument-hint: <phase_number> "<commit message>"  e.g. "2 \"add 9 ORM models and DDL scripts\""
allowed-tools: Read, Bash(git:*)
---

<!-- CONTEXT BUDGET: ~8K tokens. Load ONLY: project_context/00_global.md + phase spec (if needed) -->

Read .claude/project_context/00_global.md for git conventions.
The user passed `$ARGUMENTS` as: first token = `PHASE_NUMBER`, rest = `COMMIT_MESSAGE`.

## Step 1 — Verify validation was run
Check if `.claude/specs/phase{N}-*.md` exists. If it doesn't, stop: "Run /phase-start {N} first."

Remind the user: "Have you run /validate-phase {N} and resolved all failures? (y/n)"
If they say no, stop and direct them to `/validate-phase {N}`.

## Step 2 — Check git status
```
git status --short
```
If there are no staged or unstaged changes, stop: "Nothing to commit. Have you saved your files?"

List the changed files so the user can confirm these are the intended changes.

## Step 3 — Check current branch
```
git branch --show-current
```
Verify the branch is `feature/phase{N}-*`. If on `main`, stop with an error:
"You are on main. Commits should go to a feature branch. Run /phase-start {N} {name} first."

## Step 4 — Run pre-commit hooks
```
git add --all
git stash  # save staged changes temporarily
git stash pop
```

Actually, run pre-commit directly:
```
python3 -m pre_commit run --all-files 2>&1 | tail -40
```
If pre-commit fails, report which hooks failed and what to fix. Do NOT proceed with the commit. Do NOT use `--no-verify`.

If pre-commit is not installed, run the manual checks:
```
python3 -m black app/ etl/ ml/ --check 2>&1 | tail -20
python3 -m flake8 app/ etl/ ml/ --max-line-length=88 --extend-ignore=E203,W503 2>&1 | tail -20
```

## Step 5 — Stage changes
```
git add app/ etl/ ml/ sql/ tests/ configs/ scripts/ dags/ docker/ 2>/dev/null
git add -u
```
Do NOT stage `.env`, `venv/`, `.venv/`, `*.pyc`, or `__pycache__/`.

Show staged files:
```
git diff --cached --name-only
```

## Step 6 — Construct commit message
Format: `feat(phase{N}): {COMMIT_MESSAGE}`

Examples of correct format:
- `feat(phase2): add 9 ORM models with SQLAlchemy 2.0 and matching DDL scripts`
- `feat(phase3): implement incremental ETL extractors for all 8 data sources`

## Step 7 — Commit
```
git commit -m "feat(phase{N}): {COMMIT_MESSAGE}

Phase {N} deliverables:
- [list key files from git diff --cached --name-only]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

## Step 8 — Push to remote
```
git push -u origin feature/phase{N}-{name} 2>&1
```
If push fails due to upstream divergence, report the error — do NOT force push without user confirmation.

## Step 9 — Report
```
═══════════════════════════════════════════════
Phase {N} Commit Complete
═══════════════════════════════════════════════
Branch:  feature/phase{N}-{name}
Commit:  {commit_hash} — feat(phase{N}): {message}
Files:   {N} files changed, {X} insertions(+), {Y} deletions(-)

Files committed:
  {list of files}

To open a Pull Request:
  gh pr create --base main --head feature/phase{N}-{name} \
    --title "feat(phase{N}): {message}" \
    --body "Phase {N} complete. See .claude/specs/phase{N}-*.md for acceptance criteria."

Or visit: https://github.com/{owner}/{repo}/compare/feature/phase{N}-{name}
═══════════════════════════════════════════════
```
