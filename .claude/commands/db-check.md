---
description: Verify DDL ↔ ORM parity — every table, column, FK, {schema} placeholder, and __table_args__ cross-checked
argument-hint: (no arguments)
allowed-tools: Read, Glob, Bash(git:*)
---

<!-- CONTEXT BUDGET: ~50K tokens max. Load only files listed below. -->

You have .claude/CLAUDE.md context. For feature matrix validation, read: `configs/base.yaml` ml.features.matrix section

## Step 1 — Discover all DDL files
```
Glob: sql/ddl/*.sql
```
Expected: one `.sql` file per table. The 9 expected tables are:
`user_profiles`, `user_sessions`, `content_affinity`, `subscriptions`,
`email_engagement`, `social_activity`, `commerce_activity`, `feature_store`, `persona_assignments`

For each DDL file found, read its full content.

## Step 2 — Discover all ORM model files
```
Glob: app/models/orm/*.py
```
Exclude `__init__.py`. For each ORM file found, read its full content.

## Step 3 — Check {schema} placeholder in every DDL file
For each DDL file:
- Confirm it contains `{schema}` in the `CREATE TABLE` statement
- Confirm it does NOT contain the literal string `public.` (should be `{schema}.` instead)
- Record: PASS or FAIL per file

## Step 4 — Check __table_args__ in every ORM model
For each ORM `.py` file:
- Confirm it contains `__table_args__`
- Confirm `__table_args__` references `settings.database.schema` (not a hardcoded string like `"public"`)
- Record: PASS or FAIL per file

## Step 5 — DDL ↔ ORM table name matching
Build two sets:
- DDL tables: extract table name from `CREATE TABLE {schema}.{name}` in each `.sql` file
- ORM tables: extract `__tablename__` value from each ORM `.py` file

Report:
- Tables in DDL but NOT in ORM (missing ORM model)
- Tables in ORM but NOT in DDL (orphaned ORM model — no DDL backing it)
- Tables present in both (matched)

## Step 6 — Column-level DDL ↔ ORM check
For each matched table pair, compare columns:

**From DDL:** parse every `column_name datatype` line inside `CREATE TABLE (...)`.

**From ORM:** find every `Mapped[...]` annotated attribute and `Column(...)` definition.

Check:
- Every column in the DDL has a corresponding attribute in the ORM model
- Column names match exactly (snake_case in both)
- Nullable DDL columns (`NULL`) map to `Optional[type]` in the ORM
- NOT NULL DDL columns map to non-optional types in the ORM
- Primary key columns are marked with `primary_key=True` in ORM

Report mismatches in a table format:
```
Table: user_profiles
  Column           DDL Type        ORM Type        Status
  ─────────────────────────────────────────────────────────
  user_id          UUID NOT NULL   Mapped[UUID]    ✓
  email            VARCHAR(255)    Mapped[str]     ✓
  account_age_days INTEGER         MISSING         ✗
```

## Step 7 — Foreign key check
For each `REFERENCES` or `FOREIGN KEY` clause in the DDL files:
- Verify the referenced table exists in `sql/ddl/`
- Verify the ORM model has a `ForeignKey(...)` on the corresponding column
- Verify `relationship()` is defined if the FK is referenced elsewhere

Record: PASS or FAIL per FK.

## Step 8 — Index check
For each table, check:
- Primary key index exists
- Every foreign key column has an index (`CREATE INDEX` in DDL)
- `feature_store` table has an index on `computed_at` (for pipeline idempotency queries)
- `persona_assignments` table has an index on `assigned_at` and `run_id`

## Step 9 — feature_store column completeness
This is a critical check. Read `configs/base.yaml` and extract the 46 feature names from `ml.features.matrix`.
Read `sql/ddl/feature_store.sql` (if it exists) and verify all 46 feature names appear as columns.
Read `app/models/orm/feature_store.py` (if it exists) and verify all 46 feature names appear as attributes.

Report any missing features.

## Step 10 — Report
```
═══════════════════════════════════════════════
Database Schema Consistency Report
═══════════════════════════════════════════════

DDL FILES FOUND:       {N}/9
ORM MODELS FOUND:      {N}/9

{schema} PLACEHOLDER
  ✓ user_profiles.sql
  ✗ subscriptions.sql — uses hardcoded "public." instead of "{schema}."

__table_args__ CHECK
  ✓ orm/user_profiles.py
  ✗ orm/subscriptions.py — missing __table_args__

TABLE MATCHING
  ✓ Matched: user_profiles, user_sessions, ...
  ✗ In DDL only (no ORM): content_affinity
  ✗ In ORM only (no DDL): n/a

COLUMN PARITY
  ✓ user_profiles — all 8 columns matched
  ✗ email_engagement — 3 missing columns in ORM: nl_post_opinion, nl_evening_update, nl_morning_report

FOREIGN KEYS
  ✓ All 7 FKs verified

INDEXES
  ✗ user_sessions.sql — missing index on user_id (FK column)

FEATURE STORE (46 features)
  ✓ All 46 features present in DDL and ORM

═══════════════════════════════════════════════
RESULT: FAIL — 4 issues found

FIXES NEEDED:
1. Replace "public." with "{schema}." in sql/ddl/subscriptions.sql
2. Add __table_args__ to app/models/orm/subscriptions.py
3. Create app/models/orm/content_affinity.py
4. Add missing columns to app/models/orm/email_engagement.py
   Missing: nl_post_opinion, nl_evening_update, nl_morning_report
═══════════════════════════════════════════════
```
