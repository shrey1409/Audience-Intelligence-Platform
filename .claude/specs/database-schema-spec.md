# AUDIENCE INTELLIGENCE PLATFORM — DATABASE SCHEMA SPECIFICATION

**Version:** 1.1
**Status:** APPROVED FOR PHASE 2 IMPLEMENTATION
**Source:** master-specification.md v1.0 + system_design-spec.md v1.0
**Date:** 2026-05-31 (v1.0) | Corrected: 2026-05-31 (v1.1)
**Scope:** Phase 2 — all 9 staging tables + ga4_identity_bridge + ORM models + migrations

> This document is the PRIMARY INPUT for Claude Code Plan Mode Phase 2 implementation.
> Every section is implementation-ready. No section contains TBD, TODO, or "to be determined."
> Open questions Q1–Q7 are each answered with a binding decision.

---

## CORRECTIONS APPLIED IN v1.1

Six implementation-blocking issues were identified in v1.0 and corrected here:

| # | Correction | Location | Severity |
|---|------------|----------|----------|
| C1 | `Timestamp` → `DateTime` in all ORM imports and mapped_column declarations. `Timestamp` is not a valid SQLAlchemy type; using it causes `ImportError` at runtime. | Section 4 — all 10 models | 🔴 Critical |
| C2 | Removed deprecated `version: "3.9"` from docker-compose.yml. Docker Compose v2 warns on this key; it is not needed. | Section 9.2 | 🟡 Minor |
| C3 | Added `from decimal import Decimal` to the shared ORM import block. All models using `Mapped[Decimal]` and `default=Decimal("0")` fail with `NameError` without this import. | Section 4 — shared imports | 🔴 Critical |
| C4 | Added `date` to datetime imports (`from datetime import date, datetime`). Changed `Mapped[datetime.date]` → `Mapped[date]` throughout. Without this, date-typed columns raise `NameError`. | Section 4 — all models with date columns | 🔴 Critical |
| C5 | Added `ForeignKey()` reference inside `mapped_column()` for all FK columns across all models. Without `ForeignKey()`, SQLAlchemy does not enforce referential integrity at the ORM level and Alembic autogenerate ignores FK relationships. | Section 4 — FK columns in 7 models | 🔴 Critical |
| C6 | Added `alembic/versions/.gitkeep` to Phase 2 deliverables. Git does not track empty directories; without `.gitkeep`, `alembic/versions/` is not committed and Alembic cannot write migration files. | Section 1 — deliverables list | 🟡 Minor |

**All other content from v1.0 is unchanged and correct.**

---

## TABLE OF CONTENTS

1. Phase 2 Scope and Deliverables
2. Pre-Implementation Checks
3. DDL Specification — All 9 Tables + Bridge Table
4. ORM Model Specification — All 10 Models
5. ENUM Definitions
6. Index Strategy
7. SQL DDL File Specification
8. Alembic Initial Migration
9. Docker Infrastructure for Phase 2
10. Test Specification
11. Phase 2 Definition of Done
12. Risks Specific to Phase 2
13. Questions Resolved

---

## SECTION 1: PHASE 2 SCOPE AND DELIVERABLES

> **Q5 resolution applies here:** ga4_identity_bridge is added as a 10th table (see Section 13 Q5).
> The deliverables list below reflects the updated count.

| # | File Path | Action | Contents | Depends On |
|---|-----------|--------|----------|------------|
| 1 | `requirements/base.txt` | **modify** | Add `asyncpg==0.29.0` | nothing |
| 2 | `docker/postgres/init/01_create_databases.sql` | **new** | Creates mlflow and airflow databases on first postgres start | nothing |
| 3 | `docker-compose.yml` | **new** | Phase 2 minimal: postgres + redis only | #2 |
| 4 | `app/core/config.py` | **new** | Settings class, YAML loader, module-level singleton | nothing |
| 5 | `app/core/database.py` | **new** | Async engine (FastAPI), sync engine (ETL/ML/Alembic), get_db | #4 |
| 6 | `app/core/logging.py` | **new** | structlog configure_logging(), module-level logger | #4 |
| 7 | `app/core/security.py` | **new** | APIKeyMiddleware for X-API-Key header validation | #4 |
| 8 | `app/models/orm/base.py` | **new** | DeclarativeBase subclass | nothing |
| 9 | `app/models/orm/enums.py` | **new** | Python Enum classes for all 14 enumerated column types | nothing |
| 10 | `app/models/orm/zephr_users.py` | **new** | ZephrUsers ORM model (PK table — all others FK to this) | #8, #4 |
| 11 | `app/models/orm/ga4_events.py` | **new** | Ga4Events ORM model | #8, #4, #10 |
| 12 | `app/models/orm/ga4_identity_bridge.py` | **new** | Ga4IdentityBridge ORM model (user_pseudo_id → user_id) | #8, #4, #10 |
| 13 | `app/models/orm/braintree_subscriptions.py` | **new** | BraintreeSubscriptions ORM model | #8, #4, #10 |
| 14 | `app/models/orm/sailthru_newsletter.py` | **new** | SailthruNewsletter ORM model | #8, #4, #10 |
| 15 | `app/models/orm/pushly_subscribers.py` | **new** | PushlySubscribers ORM model | #8, #4, #10 |
| 16 | `app/models/orm/openweb_engagement.py` | **new** | OpenwebEngagement ORM model | #8, #4, #10 |
| 17 | `app/models/orm/trackonomics_clicks.py` | **new** | TrackonomicsClicks ORM model | #8, #4, #10 |
| 18 | `app/models/orm/transunion_demographics.py` | **new** | TransunionDemographics ORM model | #8, #4, #10 |
| 19 | `app/models/orm/feature_store.py` | **new** | FeatureStore ORM model (64 columns — most complex) | #8, #4, #10 |
| 20 | `app/models/orm/__init__.py` | **new** | Imports all 10 ORM models so they register with Base.metadata | #10–#19 |
| 21 | `alembic.ini` | **new** | Alembic configuration (no sqlalchemy.url — injected at runtime) | nothing |
| 22 | `alembic/env.py` | **new** | Schema-aware migration env (include_schemas, include_object, version_table_schema) | #4, #20, #21 |
| 23 | `alembic/versions/` | **new dir** | Empty directory; initial migration file added after alembic revision command | #22 |
| 23a | `alembic/versions/.gitkeep` | **new** | Ensures empty alembic/versions/ directory is tracked by Git | #23 |
| 24 | `scripts/run_migrations.py` | **new** | CREATE SCHEMA IF NOT EXISTS + alembic upgrade head | #4, #21, #22, #23 |
| 25 | `sql/ddl/001_create_zephr_users.sql` | **new** | Human-readable DDL reference for zephr_users | nothing |
| 26 | `sql/ddl/002_create_ga4_events.sql` | **new** | Human-readable DDL reference for ga4_events | nothing |
| 27 | `sql/ddl/003_create_ga4_identity_bridge.sql` | **new** | Human-readable DDL reference for ga4_identity_bridge | nothing |
| 28 | `sql/ddl/004_create_braintree_subscriptions.sql` | **new** | Human-readable DDL reference | nothing |
| 29 | `sql/ddl/005_create_sailthru_newsletter.sql` | **new** | Human-readable DDL reference | nothing |
| 30 | `sql/ddl/006_create_pushly_subscribers.sql` | **new** | Human-readable DDL reference | nothing |
| 31 | `sql/ddl/007_create_openweb_engagement.sql` | **new** | Human-readable DDL reference | nothing |
| 32 | `sql/ddl/008_create_trackonomics_clicks.sql` | **new** | Human-readable DDL reference | nothing |
| 33 | `sql/ddl/009_create_transunion_demographics.sql` | **new** | Human-readable DDL reference | nothing |
| 34 | `sql/ddl/010_create_feature_store.sql` | **new** | Human-readable DDL reference for feature_store (64 columns) | nothing |
| 35 | `tests/unit/test_config.py` | **new** | Unit tests for Settings loading (6 tests) | #4 |
| 36 | `tests/unit/test_models.py` | **new** | Unit tests for ORM model instantiation (4 tests) | #10–#19 |
| 37 | `tests/integration/test_migrations.py` | **new** | Integration tests for migration execution (6 tests) | #24, Docker |

**Total new/modified files: 37**

**Build order for implementation:**
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 25–34 (DDL files, any order) → 35 → 36 → 37

---

## SECTION 2: PRE-IMPLEMENTATION CHECKS

### Check 1 — asyncpg in requirements/base.txt

**Result: MISSING. asyncpg==0.29.0 is NOT present in requirements/base.txt.**

Current database packages in requirements/base.txt:
```
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
alembic==1.13.1
```

`asyncpg==0.29.0` is absent. This is a blocking pre-implementation task.

**Action — FIRST task of Phase 2:**
```bash
# 1. Add to requirements/base.txt immediately before any ORM code is written
echo "asyncpg==0.29.0" >> requirements/base.txt

# 2. Install
pip install asyncpg==0.29.0

# 3. Verify import
python3 -c "import asyncpg; print(asyncpg.__version__)"
# Expected: 0.29.0
```

The system_design-spec.md Section 3 requires `asyncpg` for the `create_async_engine` FastAPI path. Without it, `app/core/database.py` will fail on import.

---

### Check 2 — Docker availability

**Action before writing any infrastructure file:**
```bash
docker --version          # must return Docker version
docker compose version    # must return Compose v2
docker ps                 # must not error (daemon running)
```

If Docker is not running, start it before proceeding to Section 9.

---

### Check 3 — Existing file conflicts

Files from the Phase 2 deliverables list that **already exist** on disk:

| File | Status | Action |
|------|--------|--------|
| `requirements/base.txt` | **EXISTS** | Modify — append asyncpg line |
| `app/core/__init__.py` | EXISTS (empty) | No change needed |
| `app/models/orm/__init__.py` | EXISTS (empty) | **Overwrite** — add model imports |
| All other files | DO NOT EXIST | Create new |

No overwrite risks exist for any substantive implementation file.

---

### Check 4 — configs/base.yaml feature count

**Result: CONFIRMED. Exactly 46 features in ml.features.matrix.**

Verified count from base.yaml:
```
total_sessions, total_pageviews, active_days, avg_session_duration,
avg_pages_per_session, bounce_rate, mobile_ratio, desktop_ratio,
pageviews_per_session, days_since_last_visit, account_age_days,      # 11
ratio_sports, ratio_entertainment, ratio_celebrity, ratio_shopping,
ratio_opinion, ratio_world_news, ratio_business, ratio_lifestyle,     # 8 (total 19)
has_subscription, subscription_amount, total_billing_cycles,
days_until_renewal,                                                    # 4 (total 23)
newsletter_count, open_rate, click_through_rate, email_engagement_score,
nl_sports_alerts, nl_morning_report, nl_page_six_daily, nl_celebrity_news,
nl_evening_update, nl_post_opinion,                                    # 10 (total 33)
total_comments, total_likes_given, total_shares, social_engagement_score,  # 4 (total 37)
total_affiliate_clicks, total_transactions, total_revenue_generated,
conversion_rate, avg_transaction_value, unique_advertisers_clicked,   # 6 (total 43)
age_score, income_score, has_children                                  # 3 (total 46)
```

Feature count: **46 ✓** — proceed.

---

### feature_store column count correction

The prompt states "63 columns." The accurate count from cross-referencing Section 8.4 (Master Spec), Section 15 Q2, and Section 15 Q7 is **64 columns**:

- 1 identity PK (user_id)
- 3 metadata columns (created_at, updated_at, is_new_user)
- 46 ML feature columns
- 4 extra nl_* metadata flags NOT in ML matrix (nl_breaking_news, nl_real_estate, nl_tech_news, nl_lifestyle_weekly)
- 10 ML output columns (persona_label, cluster_id, algorithm_used, cluster_score, last_updated, subscription_propensity_score, churn_propensity_score, commerce_propensity_score, soft_persona_scores, cluster_top_features)

**64 total.** The spec uses 64 throughout. The `db-check` skill validation target is 64.

---

## SECTION 3: DDL SPECIFICATION — ALL 9 TABLES + BRIDGE TABLE

---

### 3.1 — zephr_users

**Source system:** Zephr (user registration and subscription state)
**Coverage:** 100% of registered users
**Refresh pattern:** incremental (registration writes + state updates)
**Primary key:** `user_id UUID`
**Universal FK:** This IS the PK table — all other tables reference zephr_users.user_id

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| user_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| email | VARCHAR(254) | NOT NULL, UNIQUE | Sailthru join key; lowercase normalised |
| hashed_email | VARCHAR(64) | NULL | SHA-256 hex; Transunion join key |
| first_name | VARCHAR(100) | NULL | PII — masked in analytics |
| last_name | VARCHAR(100) | NULL | PII — masked in analytics |
| account_age_days | INTEGER | NOT NULL DEFAULT 0 | ML feature #11; days since registration |
| is_registered | BOOLEAN | NOT NULL DEFAULT TRUE | FALSE = soft-deleted |
| registration_date | TIMESTAMP | NOT NULL | UTC; used to compute account_age_days |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_zephr_users_email` UNIQUE ON {schema}.zephr_users(email) — Sailthru identity resolution (email exact match)
- `idx_zephr_users_hashed_email` ON {schema}.zephr_users(hashed_email) — Transunion identity resolution (hashed_email match); nullable column, partial index: `WHERE hashed_email IS NOT NULL`
- `idx_zephr_users_registration_date` ON {schema}.zephr_users(registration_date) — incremental ETL watermark queries

**Foreign key constraints:** None (PK table)

**Special handling:**
- `email` must be stored lowercase-normalised at write time. Constraint: no DBMS-level enforcement (handled in ETL validate step).
- `hashed_email` is SHA-256 of lowercase email = 64 hex characters. CHAR(64) could be used but VARCHAR(64) is consistent with the rest of the schema.

---

### 3.2 — ga4_events

**Source system:** GA4 BigQuery export
**Coverage:** ~60% of registered users (anonymous sessions cannot be resolved)
**Refresh pattern:** incremental (daily BigQuery export, partitioned by event_date)
**Primary key:** `event_id UUID`
**Universal FK:** user_id is NULLABLE — populated by identity stitching via ga4_identity_bridge. user_pseudo_id is always present.

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| event_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NULL, FK → zephr_users | Set by Step 2 identity stitching; NULL = unresolved |
| user_pseudo_id | VARCHAR(64) | NOT NULL | GA4 anonymous ID; bridge table join key |
| event_name | VARCHAR(100) | NOT NULL | e.g. 'page_view', 'session_start', 'scroll' |
| event_date | DATE | NOT NULL | Partition candidate; index target |
| event_timestamp | TIMESTAMP | NOT NULL | UTC microsecond precision |
| session_id | VARCHAR(64) | NULL | GA4 session identifier |
| device_category | VARCHAR(50) | NULL, CHECK | Values: 'desktop', 'mobile', 'tablet' |
| page_category | VARCHAR(50) | NULL, CHECK | Values: see Section 5 PageCategory |
| page_path | TEXT | NULL | Raw URL path; not used in ML features |
| engagement_time_msec | INTEGER | NOT NULL DEFAULT 0 | Used to compute avg_session_duration |
| is_bounce | BOOLEAN | NOT NULL DEFAULT FALSE | Single-page session with no engagement |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_ga4_events_user_id` ON {schema}.ga4_events(user_id) WHERE user_id IS NOT NULL — FK lookup for feature builder JOIN
- `idx_ga4_events_user_pseudo_id` ON {schema}.ga4_events(user_pseudo_id) — identity stitching lookup
- `idx_ga4_events_event_date` ON {schema}.ga4_events(event_date) — time-range ETL queries and future partition pruning
- `idx_ga4_events_user_pseudo_id_event_date` ON {schema}.ga4_events(user_pseudo_id, event_date) — composite for incremental bridge resolution

**Foreign key constraints:**
```sql
CONSTRAINT fk_ga4_events_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE SET NULL  -- not CASCADE: event history preserved if user deleted
```

**Special handling:**
- user_id FK is `ON DELETE SET NULL` (not CASCADE) — GA4 event history is retained for analytics even if a user is removed from zephr_users.
- `CHECK (device_category IN ('desktop', 'mobile', 'tablet'))` applied as column constraint.
- `CHECK (page_category IN ('sports','entertainment','celebrity','business','lifestyle','world_news','opinion','shopping','us_news','page_six'))` applied as column constraint.
- No PostgreSQL table partitioning at Phase 2 — see Section 13 Q1.

---

### 3.3 — ga4_identity_bridge

**Source system:** Derived from GA4 login events + Zephr user_id
**Coverage:** ~60% of GA4 user_pseudo_ids resolve to a user_id
**Refresh pattern:** incremental (appended on each login event during identity stitching)
**Primary key:** `bridge_id UUID`
**Universal FK:** Direct FK to zephr_users.user_id

> This is the 10th table, added per Q5 resolution. It maps GA4 user_pseudo_id → Zephr user_id persistently.

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| bridge_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_pseudo_id | VARCHAR(64) | NOT NULL, UNIQUE | GA4 anonymous ID — one mapping per pseudo_id |
| user_id | UUID | NOT NULL, FK → zephr_users | Resolved identity |
| first_seen_at | TIMESTAMP | NOT NULL | First login event that created this mapping |
| last_seen_at | TIMESTAMP | NOT NULL | Most recent login event that confirmed mapping |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_ga4_bridge_user_pseudo_id` UNIQUE ON {schema}.ga4_identity_bridge(user_pseudo_id) — primary lookup for stitcher
- `idx_ga4_bridge_user_id` ON {schema}.ga4_identity_bridge(user_id) — reverse lookup (find all pseudo_ids for a user)

**Foreign key constraints:**
```sql
CONSTRAINT fk_ga4_bridge_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

---

### 3.4 — braintree_subscriptions

**Source system:** Braintree (payment events)
**Coverage:** ~10% of registered users (subscription rate)
**Refresh pattern:** incremental (event-driven on state change)
**Primary key:** `subscription_id UUID`
**Universal FK:** Direct FK; braintree_customer_id = user_id set at subscription creation

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| subscription_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NOT NULL, FK → zephr_users | Direct FK |
| braintree_customer_id | VARCHAR(50) | NOT NULL, UNIQUE | Braintree internal ID = user_id at creation time |
| plan_id | VARCHAR(50) | NOT NULL, CHECK | Values: 'sports_plus', 'home_delivery', 'digital_all_access' |
| status | VARCHAR(20) | NOT NULL, CHECK | Values: 'active', 'canceled', 'past_due' |
| amount | NUMERIC(10,2) | NOT NULL | Monthly billing amount in USD |
| currency | VARCHAR(3) | NOT NULL DEFAULT 'USD' | ISO 4217 |
| billing_cycle_count | INTEGER | NOT NULL DEFAULT 0 | ML feature: total_billing_cycles |
| next_billing_date | DATE | NULL | NULL if canceled |
| started_at | TIMESTAMP | NOT NULL | Subscription start time UTC |
| canceled_at | TIMESTAMP | NULL | NULL if active |
| payment_method | VARCHAR(20) | NULL, CHECK | Values: 'credit_card', 'paypal' |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_braintree_subscriptions_user_id` ON {schema}.braintree_subscriptions(user_id) — feature builder JOIN
- `idx_braintree_subscriptions_status` ON {schema}.braintree_subscriptions(status) — filter active subscriptions

**Foreign key constraints:**
```sql
CONSTRAINT fk_braintree_subscriptions_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- `CHECK (plan_id IN ('sports_plus', 'home_delivery', 'digital_all_access'))`
- `CHECK (status IN ('active', 'canceled', 'past_due'))`
- `CHECK (payment_method IN ('credit_card', 'paypal'))`
- One user can have multiple subscription rows (history of plan changes). Feature builder takes the most recent active subscription per user.

---

### 3.5 — sailthru_newsletter

**Source system:** Sailthru (email engagement) + Pushly (newsletter opt-in flags)
**Coverage:** ~100% of registered users with email
**Refresh pattern:** full_refresh (weekly full sync)
**Primary key:** `record_id UUID`
**Universal FK:** email → user_id via zephr_users.email exact match

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| record_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NULL, FK → zephr_users | Set by identity stitching; email match |
| email | VARCHAR(254) | NOT NULL | Lowercase; identity stitching join key |
| newsletter_count | SMALLINT | NOT NULL DEFAULT 0 | ML feature #24: count of subscribed newsletters |
| open_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #25: range 0.0000–1.0000 |
| click_through_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #26: range 0.0000–1.0000 |
| email_engagement_score | SMALLINT | NOT NULL DEFAULT 0 | ML feature #27: 0=low, 1=medium, 2=high |
| engagement_tier | VARCHAR(10) | NULL, CHECK | Values: 'low', 'medium', 'high' |
| subscribed_newsletters | TEXT | NULL | JSON array of newsletter name strings |
| nl_sports_alerts | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #28 |
| nl_morning_report | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #29 |
| nl_page_six_daily | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #30 |
| nl_celebrity_news | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #31 |
| nl_evening_update | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #32 |
| nl_post_opinion | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #33 |
| nl_breaking_news | BOOLEAN | NOT NULL DEFAULT FALSE | Metadata only — not in ML matrix |
| nl_real_estate | BOOLEAN | NOT NULL DEFAULT FALSE | Metadata only — not in ML matrix |
| nl_tech_news | BOOLEAN | NOT NULL DEFAULT FALSE | Metadata only — not in ML matrix |
| nl_lifestyle_weekly | BOOLEAN | NOT NULL DEFAULT FALSE | Metadata only — not in ML matrix |
| last_synced_at | TIMESTAMP | NULL | Most recent Sailthru sync timestamp |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_sailthru_newsletter_user_id` ON {schema}.sailthru_newsletter(user_id) WHERE user_id IS NOT NULL
- `idx_sailthru_newsletter_email` ON {schema}.sailthru_newsletter(email) — identity stitching lookup

**Foreign key constraints:**
```sql
CONSTRAINT fk_sailthru_newsletter_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- `CHECK (engagement_tier IN ('low', 'medium', 'high'))`
- Full-refresh mode: ETL truncates the table before each load. user_id FK is SET on re-load.

---

### 3.6 — pushly_subscribers

**Source system:** Pushly (push notification opt-in)
**Coverage:** ~35% of registered users
**Refresh pattern:** incremental (daily delta sync)
**Primary key:** `subscriber_id UUID`
**Universal FK:** external_id = user_id set at push opt-in (direct FK, 100% of records)

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| subscriber_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NOT NULL, FK → zephr_users | Direct FK |
| external_id | VARCHAR(100) | NOT NULL, UNIQUE | = user_id set at push opt-in time |
| platform | VARCHAR(20) | NOT NULL, CHECK | Values: 'web_desktop','web_mobile','ios','android' |
| push_opted_in | BOOLEAN | NOT NULL DEFAULT TRUE | Current opt-in state |
| push_is_active | BOOLEAN | NOT NULL DEFAULT TRUE | FALSE = browser unsubscribed |
| opted_in_at | TIMESTAMP | NOT NULL | First opt-in timestamp UTC |
| opted_out_at | TIMESTAMP | NULL | Most recent opt-out if applicable |
| last_push_sent_at | TIMESTAMP | NULL | Most recent push notification timestamp |
| push_open_count | INTEGER | NOT NULL DEFAULT 0 | Total push opens (informational — not in ML matrix) |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_pushly_subscribers_user_id` ON {schema}.pushly_subscribers(user_id)
- `idx_pushly_subscribers_platform` ON {schema}.pushly_subscribers(platform) — segmentation queries

**Foreign key constraints:**
```sql
CONSTRAINT fk_pushly_subscribers_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- `CHECK (platform IN ('web_desktop', 'web_mobile', 'ios', 'android'))`

---

### 3.7 — openweb_engagement

**Source system:** OpenWeb (SSO-authenticated comments/reactions)
**Coverage:** ~23% of registered users
**Refresh pattern:** incremental (daily delta sync)
**Primary key:** `engagement_id UUID`
**Universal FK:** user_id direct FK via SSO token (100% of OpenWeb records resolve)

> Design note: This table stores individual social engagement events, NOT pre-aggregated totals. The feature builder (Step 3) aggregates by user_id to produce the 4 ML features. This preserves the ability to re-aggregate with different time windows.

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| engagement_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NOT NULL, FK → zephr_users | Direct FK via OpenWeb SSO |
| event_type | VARCHAR(20) | NOT NULL, CHECK | Values: 'comment','like','share' |
| content_id | VARCHAR(100) | NULL | Article or page identifier |
| content_category | VARCHAR(50) | NULL | Content section for engagement |
| engaged_at | TIMESTAMP | NOT NULL | UTC event timestamp |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_openweb_engagement_user_id` ON {schema}.openweb_engagement(user_id) — feature builder GROUP BY user_id
- `idx_openweb_engagement_user_id_event_type` ON {schema}.openweb_engagement(user_id, event_type) — selective aggregation

**Foreign key constraints:**
```sql
CONSTRAINT fk_openweb_engagement_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- `CHECK (event_type IN ('comment', 'like', 'share'))`

---

### 3.8 — trackonomics_clicks

**Source system:** Trackonomics (affiliate click tracking SFTP export)
**Coverage:** ~16% user coverage; multiple click rows per commerce user
**Refresh pattern:** incremental (daily SFTP export)
**Primary key:** `click_id UUID`
**Universal FK:** user_id passed as URL parameter in affiliate links (100% of attributed clicks)

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| click_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NOT NULL, FK → zephr_users | Anonymous clicks excluded at ETL validate step |
| advertiser_id | VARCHAR(100) | NOT NULL | Trackonomics advertiser identifier |
| product_category | VARCHAR(30) | NULL, CHECK | Values: see Section 5 ProductCategory |
| click_timestamp | TIMESTAMP | NOT NULL | UTC |
| converted | BOOLEAN | NOT NULL DEFAULT FALSE | TRUE = purchase confirmed |
| transaction_id | VARCHAR(100) | NULL | NULL if not converted |
| transaction_amount | NUMERIC(10,2) | NULL | NULL if not converted |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_trackonomics_clicks_user_id` ON {schema}.trackonomics_clicks(user_id) — feature builder GROUP BY user_id
- `idx_trackonomics_clicks_user_id_converted` ON {schema}.trackonomics_clicks(user_id, converted) — conversion rate computation
- `idx_trackonomics_clicks_advertiser_id` ON {schema}.trackonomics_clicks(advertiser_id) — unique_advertisers_clicked computation

**Foreign key constraints:**
```sql
CONSTRAINT fk_trackonomics_clicks_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- `CHECK (product_category IN ('electronics','fashion','home','beauty','sports_gear','books','travel'))`

---

### 3.9 — transunion_demographics

**Source system:** Transunion TruAudience API (monthly batch refresh)
**Coverage:** ~70% match rate; records below 0.70 confidence excluded from ML
**Refresh pattern:** full_refresh (monthly batch)
**Primary key:** `demo_id UUID`
**Universal FK:** hashed_email (SHA-256) matched to zephr_users.hashed_email; one row per user

**Column specification:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| demo_id | UUID | PRIMARY KEY | Python-side uuid.uuid4 |
| user_id | UUID | NULL UNIQUE, FK → zephr_users | Set by identity stitching; UNIQUE = one row per user |
| hashed_email | VARCHAR(64) | NOT NULL | Join key: matches zephr_users.hashed_email |
| match_confidence | NUMERIC(4,3) | NOT NULL | Range 0.000–1.000; records < 0.70 excluded from ML |
| excluded | BOOLEAN | NOT NULL DEFAULT FALSE | TRUE if match_confidence < etl.transunion_min_confidence |
| age_range | VARCHAR(20) | NULL, CHECK | See Section 5 AgeRange; NULL if excluded |
| gender | VARCHAR(10) | NULL, CHECK | See Section 5 Gender; PII |
| income_range | VARCHAR(20) | NULL, CHECK | See Section 5 IncomeRange |
| has_children | BOOLEAN | NULL | ML feature #46; NULL if excluded |
| home_ownership | VARCHAR(10) | NULL, CHECK | See Section 5 HomeOwnership; PII |
| education | VARCHAR(20) | NULL, CHECK | See Section 5 Education |
| address_state | VARCHAR(2) | NULL | PII — masked in analytics environments |
| address_zip | VARCHAR(10) | NULL | PII — masked in analytics environments |
| match_date | DATE | NOT NULL | Date of Transunion batch match |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit column |

**Index specification:**
- `idx_transunion_demographics_user_id` UNIQUE ON {schema}.transunion_demographics(user_id) WHERE user_id IS NOT NULL
- `idx_transunion_demographics_hashed_email` ON {schema}.transunion_demographics(hashed_email) — identity stitching lookup
- `idx_transunion_demographics_match_confidence` ON {schema}.transunion_demographics(match_confidence) — filter for < 0.70 exclusion (etl.transunion_min_confidence from base.yaml)
- `idx_transunion_demographics_excluded` ON {schema}.transunion_demographics(excluded) WHERE excluded = FALSE — partial index for ML feature builder (only non-excluded records)

**Foreign key constraints:**
```sql
CONSTRAINT fk_transunion_demographics_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE
```

**Special handling:**
- All ENUM CHECK constraints per Section 5.
- `excluded` flag is set by the ETL validate step based on `etl.transunion_min_confidence` (0.70 from base.yaml). The threshold is never hardcoded.
- Full-refresh: table is truncated and reloaded monthly. user_id FK is populated in identity stitching.

---

### 3.10 — feature_store

**Source system:** Computed (pipeline Step 3+8 output) — one row per registered user
**Coverage:** 100% of registered users (new users get row with is_new_user=TRUE)
**Refresh pattern:** upsert weekly (INSERT ... ON CONFLICT (user_id) DO UPDATE)
**Primary key:** `user_id UUID` — also the upsert conflict target
**Universal FK:** IS the identity column; no FK (denormalised output table)

> **Column count:** 64 total (see Section 2 correction note).

**Identity columns (4):**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| user_id | UUID | PRIMARY KEY | FK source is zephr_users; no explicit FK constraint here |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit: first pipeline run that created this row |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | Audit: last row modification |
| is_new_user | BOOLEAN | NOT NULL DEFAULT FALSE | TRUE if total_sessions < etl.new_user_session_threshold |

**Web behaviour features — 11 columns (from GA4):**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| total_sessions | INTEGER | NOT NULL DEFAULT 0 | ML feature #1; log1p applied before scaling |
| total_pageviews | INTEGER | NOT NULL DEFAULT 0 | ML feature #2; log1p applied before scaling |
| active_days | INTEGER | NOT NULL DEFAULT 0 | ML feature #3 |
| avg_session_duration | NUMERIC(10,2) | NOT NULL DEFAULT 0 | ML feature #4; seconds |
| avg_pages_per_session | NUMERIC(8,4) | NOT NULL DEFAULT 0 | ML feature #5 |
| bounce_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #6; range 0.0000–1.0000 |
| mobile_ratio | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #7; range 0.0000–1.0000 |
| desktop_ratio | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #8; range 0.0000–1.0000 |
| pageviews_per_session | NUMERIC(8,4) | NOT NULL DEFAULT 0 | ML feature #9; derived |
| days_since_last_visit | INTEGER | NOT NULL DEFAULT 0 | ML feature #10 |
| account_age_days | INTEGER | NOT NULL DEFAULT 0 | ML feature #11; from Zephr not GA4 |

**Content affinity features — 8 columns:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| ratio_sports | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #12; range 0.0000–1.0000 |
| ratio_entertainment | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #13 |
| ratio_celebrity | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #14 |
| ratio_shopping | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #15 |
| ratio_opinion | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #16 |
| ratio_world_news | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #17 |
| ratio_business | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #18 |
| ratio_lifestyle | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #19 |

**Subscription features — 4 columns:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| has_subscription | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #20 |
| subscription_amount | NUMERIC(10,2) | NOT NULL DEFAULT 0 | ML feature #21 |
| total_billing_cycles | INTEGER | NOT NULL DEFAULT 0 | ML feature #22 |
| days_until_renewal | INTEGER | NOT NULL DEFAULT 0 | ML feature #23 |

**Email features — 14 columns (10 ML matrix + 4 metadata):**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| newsletter_count | SMALLINT | NOT NULL DEFAULT 0 | ML feature #24 |
| open_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #25 |
| click_through_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #26 |
| email_engagement_score | SMALLINT | NOT NULL DEFAULT 0 | ML feature #27; 0/1/2 |
| nl_sports_alerts | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #28 |
| nl_morning_report | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #29 |
| nl_page_six_daily | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #30 |
| nl_celebrity_news | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #31 |
| nl_evening_update | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #32 |
| nl_post_opinion | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #33 |
| nl_breaking_news | BOOLEAN | NOT NULL DEFAULT FALSE | **Metadata only** — not in ML matrix per Q7 |
| nl_real_estate | BOOLEAN | NOT NULL DEFAULT FALSE | **Metadata only** |
| nl_tech_news | BOOLEAN | NOT NULL DEFAULT FALSE | **Metadata only** |
| nl_lifestyle_weekly | BOOLEAN | NOT NULL DEFAULT FALSE | **Metadata only** |

**Social features — 4 columns:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| total_comments | INTEGER | NOT NULL DEFAULT 0 | ML feature #34; log1p applied |
| total_likes_given | INTEGER | NOT NULL DEFAULT 0 | ML feature #35 |
| total_shares | INTEGER | NOT NULL DEFAULT 0 | ML feature #36 |
| social_engagement_score | INTEGER | NOT NULL DEFAULT 0 | ML feature #37; derived: (comments×3)+(likes×1)+(shares×2) |

**Commerce features — 6 columns:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| total_affiliate_clicks | INTEGER | NOT NULL DEFAULT 0 | ML feature #38; log1p applied |
| total_transactions | INTEGER | NOT NULL DEFAULT 0 | ML feature #39 |
| total_revenue_generated | NUMERIC(12,2) | NOT NULL DEFAULT 0 | ML feature #40 |
| conversion_rate | NUMERIC(5,4) | NOT NULL DEFAULT 0 | ML feature #41; range 0.0000–1.0000 |
| avg_transaction_value | NUMERIC(10,2) | NOT NULL DEFAULT 0 | ML feature #42 |
| unique_advertisers_clicked | INTEGER | NOT NULL DEFAULT 0 | ML feature #43 |

**Demographic features — 3 columns:**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| age_score | SMALLINT | NOT NULL DEFAULT 0 | ML feature #44; 0=unknown, 1–6 ordinal encoding of AgeRange |
| income_score | SMALLINT | NOT NULL DEFAULT 0 | ML feature #45; 0=unknown, 1–6 ordinal encoding of IncomeRange |
| has_children | BOOLEAN | NOT NULL DEFAULT FALSE | ML feature #46; FALSE = unknown or no children |

**ML output columns — 10 columns (written by Step 8):**

| Column Name | SQL Type | Constraints | Notes |
|---|---|---|---|
| persona_label | VARCHAR(50) | NULL | One of 9 labels or cold-start label; NULL before first pipeline run |
| cluster_id | SMALLINT | NULL | NULL before first pipeline run |
| algorithm_used | VARCHAR(50) | NULL, CHECK | Values: see AlgorithmUsed enum |
| cluster_score | NUMERIC(6,4) | NULL | Silhouette contribution score 0.0–1.0 |
| last_updated | TIMESTAMP | NULL | Timestamp of last ML write-back (Step 8) |
| subscription_propensity_score | NUMERIC(6,4) | NULL | Range 0.0000–1.0000 |
| churn_propensity_score | NUMERIC(6,4) | NULL | Range 0.0000–1.0000 |
| commerce_propensity_score | NUMERIC(6,4) | NULL | Range 0.0000–1.0000 |
| soft_persona_scores | TEXT | NULL | JSON string: {persona_label: score, ...}; NULL for non-GMM algorithms |
| cluster_top_features | TEXT | NULL | JSON string: [[feature_name, importance_score], ...] top-5 |

**Index specification:**
- `idx_feature_store_persona_label` ON {schema}.feature_store(persona_label) WHERE persona_label IS NOT NULL — downstream segmentation queries
- `idx_feature_store_cluster_id` ON {schema}.feature_store(cluster_id) WHERE cluster_id IS NOT NULL — cluster-level analytics
- `idx_feature_store_persona_label_cluster_id` ON {schema}.feature_store(persona_label, cluster_id) — combined filter (most common downstream query)
- `idx_feature_store_last_updated` ON {schema}.feature_store(last_updated) WHERE last_updated IS NOT NULL — stale assignment detection
- `idx_feature_store_is_new_user` ON {schema}.feature_store(is_new_user) WHERE is_new_user = TRUE — new user exclusion filter in feature builder

**Special handling:**
- `CHECK (algorithm_used IN ('kmeans', 'bisecting_kmeans', 'gmm', 'hdbscan', 'ensemble'))`
- The PK on user_id is the unique constraint for `INSERT ... ON CONFLICT (user_id) DO UPDATE`. No separate UNIQUE constraint needed (PK implies UNIQUE — see Section 13 Q4).
- `soft_persona_scores` uses TEXT not JSONB. Rationale: JSONB adds storage overhead and query complexity for what is purely a read-through field serialised by Python. The API deserialises it with `json.loads()`.
- `cluster_top_features` uses TEXT for the same reason.

---

## SECTION 4: ORM MODEL SPECIFICATION — ALL 10 MODELS

### Import requirements common to all models

```python
from __future__ import annotations
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.orm.base import Base
```

### __table_args__ pattern (same for all models)

```python
__table_args__ = {"schema": settings.database.schema}
```

---

### 4.1 — ZephrUsers

```
Class: ZephrUsers
__tablename__: "zephr_users"

user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
hashed_email: Mapped[str | None] = mapped_column(String(64), nullable=True)
first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
account_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
is_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
registration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

Imports: standard set above.
Relationships: none in Phase 2.

---

### 4.2 — Ga4Events

```
Class: Ga4Events
__tablename__: "ga4_events"

event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="SET NULL"),
    nullable=True
)
user_pseudo_id: Mapped[str] = mapped_column(String(64), nullable=False)
event_name: Mapped[str] = mapped_column(String(100), nullable=False)
event_date: Mapped[date] = mapped_column(Date, nullable=False)
event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
device_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
page_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
page_path: Mapped[str | None] = mapped_column(Text, nullable=True)
engagement_time_msec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
is_bounce: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
```

Additional import: `from datetime import date` (for `datetime.date` type annotation, use `date` directly).

---

### 4.3 — Ga4IdentityBridge

```
Class: Ga4IdentityBridge
__tablename__: "ga4_identity_bridge"

bridge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_pseudo_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"),
    nullable=False
)
first_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

### 4.4 — BraintreeSubscriptions

```
Class: BraintreeSubscriptions
__tablename__: "braintree_subscriptions"

subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"),
    nullable=False
)
braintree_customer_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
plan_id: Mapped[str] = mapped_column(String(50), nullable=False)
status: Mapped[str] = mapped_column(String(20), nullable=False)
amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
billing_cycle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
canceled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

Additional import: `from decimal import Decimal` and `from datetime import date`.

---

### 4.5 — SailthruNewsletter

```
Class: SailthruNewsletter
__tablename__: "sailthru_newsletter"

record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID | None] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="SET NULL"),
    nullable=True
)
email: Mapped[str] = mapped_column(String(254), nullable=False)
newsletter_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
open_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
click_through_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
email_engagement_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
engagement_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)
subscribed_newsletters: Mapped[str | None] = mapped_column(Text, nullable=True)
nl_sports_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_morning_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_page_six_daily: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_celebrity_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_evening_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_post_opinion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_breaking_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_real_estate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_tech_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_lifestyle_weekly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

### 4.6 — PushlySubscribers

```
Class: PushlySubscribers
__tablename__: "pushly_subscribers"

subscriber_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"),
    nullable=False
)
external_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
platform: Mapped[str] = mapped_column(String(20), nullable=False)
push_opted_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
push_is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
opted_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
opted_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
last_push_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
push_open_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

### 4.7 — OpenwebEngagement

```
Class: OpenwebEngagement
__tablename__: "openweb_engagement"

engagement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"),
    nullable=False
)
event_type: Mapped[str] = mapped_column(String(20), nullable=False)
content_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
content_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
engaged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
```

---

### 4.8 — TrackonomicsClicks

```
Class: TrackonomicsClicks
__tablename__: "trackonomics_clicks"

click_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE"),
    nullable=False
)
advertiser_id: Mapped[str] = mapped_column(String(100), nullable=False)
product_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
click_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
converted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
transaction_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
```

---

### 4.9 — TransunionDemographics

```
Class: TransunionDemographics
__tablename__: "transunion_demographics"

demo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True, nullable=True)
hashed_email: Mapped[str] = mapped_column(String(64), nullable=False)
match_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
age_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
income_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
has_children: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
home_ownership: Mapped[str | None] = mapped_column(String(10), nullable=True)
education: Mapped[str | None] = mapped_column(String(20), nullable=True)
address_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
address_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
match_date: Mapped[date] = mapped_column(Date, nullable=False)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

### 4.10 — FeatureStore (64 columns — complete explicit specification)

```
Class: FeatureStore
__tablename__: "feature_store"
__table_args__: {"schema": settings.database.schema}

# --- Identity (4) ---
user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
is_new_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

# --- Web behaviour (11) ---
total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
total_pageviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
active_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
avg_session_duration: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
avg_pages_per_session: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"))
bounce_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
mobile_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
desktop_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
pageviews_per_session: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"))
days_since_last_visit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
account_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# --- Content affinity (8) ---
ratio_sports: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_entertainment: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_celebrity: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_shopping: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_opinion: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_world_news: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_business: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
ratio_lifestyle: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))

# --- Subscription (4) ---
has_subscription: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
subscription_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
total_billing_cycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
days_until_renewal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# --- Email ML features (10) ---
newsletter_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
open_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
click_through_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
email_engagement_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
nl_sports_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_morning_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_page_six_daily: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_celebrity_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_evening_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_post_opinion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

# --- Email metadata flags (4 — NOT in ML matrix) ---
nl_breaking_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_real_estate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_tech_news: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
nl_lifestyle_weekly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

# --- Social (4) ---
total_comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
total_likes_given: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
total_shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
social_engagement_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# --- Commerce (6) ---
total_affiliate_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
total_revenue_generated: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
conversion_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
avg_transaction_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
unique_advertisers_clicked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# --- Demographic (3) ---
age_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
income_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
has_children: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

# --- ML output (10) ---
persona_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
cluster_id: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
algorithm_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
cluster_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
subscription_propensity_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
churn_propensity_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
commerce_propensity_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
soft_persona_scores: Mapped[str | None] = mapped_column(Text, nullable=True)
cluster_top_features: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**Column count verification:** 4 + 11 + 8 + 4 + 14 + 4 + 6 + 3 + 10 = **64 ✓**

---

## SECTION 5: ENUM DEFINITIONS

### Decision: VARCHAR + CHECK CONSTRAINT (applied consistently to all 14 ENUMs)

**Rationale:** PostgreSQL native ENUM types (`CREATE TYPE ... AS ENUM`) are type-safe at the database level but require `ALTER TYPE ... ADD VALUE` — a DDL operation that cannot be rolled back and causes Alembic autogenerate issues. For this project, which will evolve (new algorithms, new subscription plans, new product categories), VARCHAR + CHECK is strongly preferred:
1. Adding a new valid value requires only updating the CHECK constraint in a migration (standard `ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT`).
2. Alembic autogenerate reliably detects CHECK constraint changes.
3. Python Enum classes enforce type safety at the application layer.
4. No `CREATE TYPE` statements to manage across multiple client schemas.

**Implementation pattern:** Python Enum class in `app/models/orm/enums.py` provides type safety for application code. SQLAlchemy `String` column in ORM. SQL `CHECK` constraint in DDL.

---

### Python Enum definitions (app/models/orm/enums.py)

```python
from enum import Enum

class DeviceCategory(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    # Used by: ga4_events.device_category

class PageCategory(str, Enum):
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    CELEBRITY = "celebrity"
    BUSINESS = "business"
    LIFESTYLE = "lifestyle"
    WORLD_NEWS = "world_news"
    OPINION = "opinion"
    SHOPPING = "shopping"
    US_NEWS = "us_news"
    PAGE_SIX = "page_six"
    # Used by: ga4_events.page_category

class SubscriptionPlan(str, Enum):
    SPORTS_PLUS = "sports_plus"
    HOME_DELIVERY = "home_delivery"
    DIGITAL_ALL_ACCESS = "digital_all_access"
    # Used by: braintree_subscriptions.plan_id

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    # Used by: braintree_subscriptions.status

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    # Used by: braintree_subscriptions.payment_method

class EmailEngagementTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    # Used by: sailthru_newsletter.engagement_tier

class PushPlatform(str, Enum):
    WEB_DESKTOP = "web_desktop"
    WEB_MOBILE = "web_mobile"
    IOS = "ios"
    ANDROID = "android"
    # Used by: pushly_subscribers.platform

class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME = "home"
    BEAUTY = "beauty"
    SPORTS_GEAR = "sports_gear"
    BOOKS = "books"
    TRAVEL = "travel"
    # Used by: trackonomics_clicks.product_category

class AgeRange(str, Enum):
    AGE_18_24 = "age_18_24"
    AGE_25_34 = "age_25_34"
    AGE_35_44 = "age_35_44"
    AGE_45_54 = "age_45_54"
    AGE_55_64 = "age_55_64"
    AGE_65_PLUS = "age_65_plus"
    # Used by: transunion_demographics.age_range
    # age_score mapping: AGE_18_24=1, AGE_25_34=2, ..., AGE_65_PLUS=6

class Gender(str, Enum):
    M = "m"
    F = "f"
    NON_BINARY = "non_binary"
    UNKNOWN = "unknown"
    # Used by: transunion_demographics.gender (PII)

class IncomeRange(str, Enum):
    LT_30K = "lt_30k"
    RANGE_30_50K = "range_30_50k"
    RANGE_50_75K = "range_50_75k"
    RANGE_75_100K = "range_75_100k"
    RANGE_100_150K = "range_100_150k"
    GT_150K = "gt_150k"
    # Used by: transunion_demographics.income_range
    # income_score mapping: LT_30K=1, GT_150K=6

class HomeOwnership(str, Enum):
    OWNER = "owner"
    RENTER = "renter"
    UNKNOWN = "unknown"
    # Used by: transunion_demographics.home_ownership (PII)

class Education(str, Enum):
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"
    # Used by: transunion_demographics.education (PII)

class AlgorithmUsed(str, Enum):
    KMEANS = "kmeans"
    BISECTING_KMEANS = "bisecting_kmeans"
    GMM = "gmm"
    HDBSCAN = "hdbscan"
    ENSEMBLE = "ensemble"
    # Used by: feature_store.algorithm_used
```

**Total ENUMs defined: 14 ✓**

---

## SECTION 6: INDEX STRATEGY

### Complete index list across all 10 tables

| Index Name | Table | Column(s) | Type | Rationale |
|---|---|---|---|---|
| `idx_zephr_users_email` | zephr_users | email | B-tree UNIQUE | Sailthru identity stitching (email exact match); also enforces uniqueness |
| `idx_zephr_users_hashed_email` | zephr_users | hashed_email | B-tree partial (NOT NULL) | Transunion identity stitching (hashed_email match) |
| `idx_zephr_users_registration_date` | zephr_users | registration_date | B-tree | Incremental ETL watermark; account_age_days computation |
| `idx_ga4_events_user_id` | ga4_events | user_id | B-tree partial (NOT NULL) | Feature builder JOIN on user_id; partial index excludes ~40% NULL rows |
| `idx_ga4_events_user_pseudo_id` | ga4_events | user_pseudo_id | B-tree | Identity stitching lookup (bridge resolution) |
| `idx_ga4_events_event_date` | ga4_events | event_date | B-tree | Time-range ETL incremental queries; future partition pruning |
| `idx_ga4_events_pseudo_id_date` | ga4_events | (user_pseudo_id, event_date) | B-tree composite | Composite for incremental bridge resolution within a date window |
| `idx_ga4_bridge_user_pseudo_id` | ga4_identity_bridge | user_pseudo_id | B-tree UNIQUE | Primary stitcher lookup; UNIQUE enforces one mapping per pseudo_id |
| `idx_ga4_bridge_user_id` | ga4_identity_bridge | user_id | B-tree | Reverse lookup: find all pseudo_ids for a user |
| `idx_braintree_user_id` | braintree_subscriptions | user_id | B-tree | Feature builder JOIN |
| `idx_braintree_status` | braintree_subscriptions | status | B-tree | Filter active subscriptions for feature computation |
| `idx_sailthru_user_id` | sailthru_newsletter | user_id | B-tree partial (NOT NULL) | Feature builder JOIN |
| `idx_sailthru_email` | sailthru_newsletter | email | B-tree | Identity stitching email match |
| `idx_pushly_user_id` | pushly_subscribers | user_id | B-tree | Feature builder JOIN |
| `idx_pushly_platform` | pushly_subscribers | platform | B-tree | Segmentation queries |
| `idx_openweb_user_id` | openweb_engagement | user_id | B-tree | Feature builder GROUP BY user_id |
| `idx_openweb_user_event_type` | openweb_engagement | (user_id, event_type) | B-tree composite | Selective aggregation by event type |
| `idx_trackonomics_user_id` | trackonomics_clicks | user_id | B-tree | Feature builder GROUP BY user_id |
| `idx_trackonomics_user_converted` | trackonomics_clicks | (user_id, converted) | B-tree composite | Conversion rate computation |
| `idx_trackonomics_advertiser_id` | trackonomics_clicks | advertiser_id | B-tree | unique_advertisers_clicked COUNT DISTINCT |
| `idx_transunion_user_id` | transunion_demographics | user_id | B-tree UNIQUE partial (NOT NULL) | Feature builder JOIN; UNIQUE = one row per user |
| `idx_transunion_hashed_email` | transunion_demographics | hashed_email | B-tree | Identity stitching lookup |
| `idx_transunion_match_confidence` | transunion_demographics | match_confidence | B-tree | Filter records below etl.transunion_min_confidence |
| `idx_transunion_excluded` | transunion_demographics | excluded | B-tree partial (excluded=FALSE) | Feature builder excludes flagged records |
| `idx_feature_store_persona_label` | feature_store | persona_label | B-tree partial (NOT NULL) | Downstream segmentation queries (persona cohort lists) |
| `idx_feature_store_cluster_id` | feature_store | cluster_id | B-tree partial (NOT NULL) | Cluster-level analytics |
| `idx_feature_store_persona_cluster` | feature_store | (persona_label, cluster_id) | B-tree composite | Most common downstream query pattern |
| `idx_feature_store_last_updated` | feature_store | last_updated | B-tree partial (NOT NULL) | Stale assignment detection; health endpoint |
| `idx_feature_store_is_new_user` | feature_store | is_new_user | B-tree partial (is_new_user=TRUE) | New user exclusion filter in feature builder |

**Total indexes: 29**

**Note on API lookup:** The single-user persona API (`GET /api/v1/persona/{user_id}`) reads exclusively from Redis. When it hits the feature store (cold-start path), the lookup is by `user_id` which is the PK — the automatic primary key index covers this with O(log n) lookup. No additional index needed for the API path.

---

## SECTION 7: SQL DDL FILE SPECIFICATION

### Q7 Resolution: Role of DDL files vs Alembic migrations

**Decision: Alembic migrations are the authoritative execution mechanism. DDL files are human-readable reference documentation.**

Rationale:
- `scripts/run_migrations.py` executes `alembic upgrade head` — never processes DDL files directly.
- DDL files in `sql/ddl/` exist so that any engineer can read the intended schema without running Python or connecting to a database.
- They serve as the specification that `/db-check` validates against ORM models.
- The contract: every Alembic migration that changes the schema MUST have a corresponding DDL file update committed in the same PR.
- They are NEVER the source of truth for what is actually in the database — the Alembic migration history is.

**No PostgreSQL extensions required.** UUID generation uses Python-side `uuid.uuid4()` (not `gen_random_uuid()` from `pgcrypto`, and not `uuid_generate_v4()` from `uuid-ossp`). No extensions need to be created.

### DDL file naming and run order

```
sql/ddl/001_create_zephr_users.sql          ← create first (PK table)
sql/ddl/002_create_ga4_events.sql           ← no FK at create time (user_id nullable)
sql/ddl/003_create_ga4_identity_bridge.sql  ← FK → zephr_users
sql/ddl/004_create_braintree_subscriptions.sql
sql/ddl/005_create_sailthru_newsletter.sql
sql/ddl/006_create_pushly_subscribers.sql
sql/ddl/007_create_openweb_engagement.sql
sql/ddl/008_create_trackonomics_clicks.sql
sql/ddl/009_create_transunion_demographics.sql
sql/ddl/010_create_feature_store.sql        ← create last (no FK — denormalised output table)
```

### DDL file template structure

Every DDL file must follow this structure:

```sql
-- sql/ddl/00N_create_{table_name}.sql
-- Source: {source system}
-- Refresh: {incremental|full_refresh}
-- Coverage: {expected user coverage %}

CREATE TABLE {schema}.{table_name} (
    -- columns in Section 3 order
    -- PK first, then columns, then audit columns last
);

-- Constraints
ALTER TABLE {schema}.{table_name}
    ADD CONSTRAINT fk_{table}_{column}
    FOREIGN KEY ({column})
    REFERENCES {schema}.zephr_users(user_id)
    ON DELETE {CASCADE|SET NULL};

ALTER TABLE {schema}.{table_name}
    ADD CONSTRAINT chk_{table}_{column}
    CHECK ({column} IN (...));

-- Indexes (after CREATE TABLE)
CREATE INDEX idx_{table}_{column}
    ON {schema}.{table_name}({column});
```

**Key rules enforced in every DDL file:**
- `{schema}` placeholder appears in EVERY table reference (CREATE TABLE, FK REFERENCES, index ON clause).
- No `CREATE TYPE` statements (VARCHAR + CHECK per Section 5 decision).
- No `gen_random_uuid()` or `uuid_generate_v4()` (Python-side UUID generation).
- No `SERIAL` or `BIGSERIAL` (UUID PKs only).

---

## SECTION 8: ALEMBIC INITIAL MIGRATION

### Why manual (not autogenerated)

The initial migration must be manual because autogenerate diffs against an existing database — when no tables exist yet, autogenerate produces an empty migration. The initial migration creates all 10 tables from scratch in FK-dependency order.

### Migration file name format

```
alembic/versions/20260531_a1b2c3d4_initial_schema.py
```

Format: `YYYYMMDD_REVID_slug.py` — matches `alembic.ini file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s`.

### upgrade() — table creation order

```
upgrade() must CREATE tables in this order:
1.  zephr_users                (PK table; all FKs point here)
2.  ga4_events                 (nullable user_id FK)
3.  ga4_identity_bridge        (user_id FK → zephr_users)
4.  braintree_subscriptions    (user_id FK → zephr_users)
5.  sailthru_newsletter        (nullable user_id FK)
6.  pushly_subscribers         (user_id FK → zephr_users)
7.  openweb_engagement         (user_id FK → zephr_users)
8.  trackonomics_clicks        (user_id FK → zephr_users)
9.  transunion_demographics    (nullable user_id FK)
10. feature_store              (PK = user_id; no FK constraint — denormalised)
```

### downgrade() — reverse order

```
downgrade() must DROP tables in reverse order:
10. feature_store
9.  transunion_demographics
8.  trackonomics_clicks
7.  openweb_engagement
6.  pushly_subscribers
5.  sailthru_newsletter
4.  braintree_subscriptions
3.  ga4_identity_bridge
2.  ga4_events
1.  zephr_users
```

### Implementation choice: op.create_table() vs op.execute()

**Decision: `op.create_table()` (Alembic API) for table creation; `op.execute(text(...))` for indexes and constraints.**

Rationale:
- `op.create_table()` is idiomatic Alembic, generates correct cross-database DDL, and is reversible with `op.drop_table()` in downgrade().
- `op.execute(text(...))` is used for index creation (`CREATE INDEX`) and complex CHECK constraints that `op.create_table()` cannot represent natively.
- The schema name is injected via `settings.database.schema` imported at migration time from `app.core.config`.

### Schema handling in migrations

```python
from app.core.config import settings

_schema = settings.database.schema  # read once at migration load time

def upgrade() -> None:
    op.create_table(
        "zephr_users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        # ... all columns ...
        schema=_schema,    # schema parameter on op.create_table()
    )
    # Index creation uses op.execute with explicit schema
    op.execute(
        text(f"CREATE UNIQUE INDEX idx_zephr_users_email "
             f"ON {_schema}.zephr_users(email)")
    )
```

The `schema=_schema` parameter on `op.create_table()` ensures all DDL is schema-qualified without string interpolation inside the column definitions.

---

## SECTION 9: DOCKER INFRASTRUCTURE FOR PHASE 2

### 9.1 — docker/postgres/init/01_create_databases.sql

```sql
-- Creates additional databases for MLflow and Airflow on first postgres container start.
-- audience_intelligence is created by POSTGRES_DB environment variable — do not create here.
-- This script runs only on the FIRST start (when postgres_data volume is empty).

CREATE DATABASE mlflow OWNER aip_user;
CREATE DATABASE airflow OWNER aip_user;
```

### 9.2 — docker-compose.yml (Phase 2 minimal — postgres + redis only)

```yaml

services:
  postgres:
    image: postgres:15
    container_name: aip_postgres
    environment:
      POSTGRES_USER: aip_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: audience_intelligence
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aip_user -d audience_intelligence"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aip_redis
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

**Phase 2 note:** mlflow, airflow-webserver, airflow-scheduler, api, grafana, and prometheus services are intentionally excluded. They are added in Phase 9 (Docker + CI/CD per the master spec roadmap). This keeps Phase 2 focused on the database schema.

### 9.3 — .env additions for Phase 2

Create `.env` in the project root (gitignored) with these values:

```bash
# Required — no YAML defaults; ValidationError at startup if absent
DATABASE__URL=postgresql://aip_user:devpassword123@localhost:5432/audience_intelligence
REDIS__URL=redis://localhost:6379/0
MLFLOW__TRACKING_URI=http://localhost:5000
API__API_KEYS=["dev-api-key-001"]
API__ADMIN_API_KEY=dev-admin-key-001

# Optional — override YAML defaults for Phase 2 development
APP_ENV=development
DATABASE__SCHEMA=public
LOG_LEVEL=INFO

# Docker Compose variable (required by docker-compose.yml)
POSTGRES_PASSWORD=devpassword123
```

**Variables that need real values:**
- `POSTGRES_PASSWORD` — choose any local dev password; must match `DATABASE__URL`
- All others can use the defaults shown above

**Variables using YAML defaults (do not need to be in .env unless overriding):**
- `DATABASE__SCHEMA` defaults to `public` from base.yaml
- `LOG_LEVEL` defaults to INFO

---

## SECTION 10: TEST SPECIFICATION

### Shared fixtures (tests/conftest.py)

```python
# Fixtures required by multiple test modules

@pytest.fixture(scope="session")
def test_db_url() -> str:
    """PostgreSQL URL for integration tests — requires docker compose up -d postgres."""
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://aip_user:devpassword123@localhost:5432/audience_intelligence"
    )
    return url

@pytest.fixture(scope="function")
def test_schema(test_db_url: str) -> Generator[str, None, None]:
    """Creates a fresh test schema, yields schema name, drops it after test."""
    schema = f"test_{uuid.uuid4().hex[:8]}"
    engine = create_engine(test_db_url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
    yield schema
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        conn.commit()
    engine.dispose()
```

---

### tests/unit/test_config.py

```
Test 1: test_settings_loads_from_base_yaml
    Verify Settings.from_yaml_and_env() succeeds with base.yaml present.
    Assert settings.project.name == "audience_intelligence_platform"
    Assert settings.database.schema == "public"
    Fixture: monkeypatch to set required env vars (DATABASE__URL, REDIS__URL, MLFLOW__TRACKING_URI, API__API_KEYS, API__ADMIN_API_KEY)

Test 2: test_yaml_deep_merge_env_override
    Load base.yaml (database.schema = "public").
    Set DATABASE__SCHEMA=nypost in env.
    Assert settings.database.schema == "nypost"
    Fixture: monkeypatch

Test 3: test_missing_database_url_raises_validation_error
    Unset DATABASE__URL from env.
    Assert pytest.raises(ValidationError) on Settings.from_yaml_and_env()
    Fixture: monkeypatch to remove env var

Test 4: test_missing_client_file_raises_file_not_found_error
    Set CLIENT_NAME=nonexistent_client in env.
    Assert pytest.raises(FileNotFoundError) on Settings.from_yaml_and_env()
    Fixture: monkeypatch

Test 5: test_ml_features_matrix_has_46_features
    Load settings normally.
    Assert len(settings.ml.features.matrix) == 46
    Fixture: standard monkeypatch with required env vars

Test 6: test_propensity_weights_sum_to_1_0
    Load settings normally.
    subscription_sum = sum(settings.ml.propensity.subscription.weights.dict().values())
    churn_sum = sum(settings.ml.propensity.churn.weights.dict().values())
    commerce_sum = sum(settings.ml.propensity.commerce.weights.dict().values())
    Assert abs(subscription_sum - 1.0) < 1e-9
    Assert abs(churn_sum - 1.0) < 1e-9
    Assert abs(commerce_sum - 1.0) < 1e-9
```

---

### tests/unit/test_models.py

```
Test 1: test_all_orm_models_instantiate_without_db
    For each model class [ZephrUsers, Ga4Events, Ga4IdentityBridge, BraintreeSubscriptions,
      SailthruNewsletter, PushlySubscribers, OpenwebEngagement, TrackonomicsClicks,
      TransunionDemographics, FeatureStore]:
        inst = ModelClass()  — no arguments (all have defaults or are nullable)
        Assert isinstance(inst, ModelClass)
    No database connection required.

Test 2: test_uuid4_default_generates_valid_uuid
    user = ZephrUsers(email="test@example.com", registration_date=datetime.utcnow())
    Assert isinstance(user.user_id, uuid.UUID)
    Assert user.user_id.version == 4

Test 3: test_table_args_schema_matches_settings
    from app.core.config import settings
    for ModelClass in all_model_classes:
        assert ModelClass.__table_args__["schema"] == settings.database.schema

Test 4: test_feature_store_has_64_columns
    from sqlalchemy import inspect
    from app.models.orm.feature_store import FeatureStore
    mapper = inspect(FeatureStore)
    column_count = len(mapper.columns)
    assert column_count == 64, f"Expected 64, got {column_count}"
```

---

### tests/integration/test_migrations.py

> Requires: `docker compose up -d postgres` before running.
> Use `test_schema` fixture for clean isolation.

```
Test 1: test_run_migrations_creates_schema_if_absent
    Set DATABASE__SCHEMA to a fresh schema name.
    Call run_migrations() (from scripts/run_migrations).
    Query information_schema.schemata for the schema name.
    Assert schema exists.

Test 2: test_alembic_upgrade_head_completes_without_error
    With test_schema fixture:
        Set DATABASE__SCHEMA to test schema.
        Call run_migrations().
        Assert no exception raised.
        Query alembic_version table in test schema.
        Assert one row exists (head revision).

Test 3: test_all_10_tables_exist_after_migration
    With test_schema fixture after migration:
        Query information_schema.tables WHERE table_schema = test_schema.
        table_names = {row.table_name for row in result}
        Assert table_names == {
            "zephr_users", "ga4_events", "ga4_identity_bridge",
            "braintree_subscriptions", "sailthru_newsletter",
            "pushly_subscribers", "openweb_engagement",
            "trackonomics_clicks", "transunion_demographics", "feature_store"
        }

Test 4: test_feature_store_has_64_columns_in_db
    With test_schema fixture after migration:
        Query information_schema.columns WHERE table_name='feature_store'
          AND table_schema=test_schema.
        Assert count == 64

Test 5: test_fk_constraint_active
    With test_schema fixture after migration:
        Insert a braintree_subscriptions row with a non-existent user_id.
        Assert IntegrityError (FK violation) raised.

Test 6: test_alembic_downgrade_returns_to_base
    With test_schema fixture after migration:
        Run alembic downgrade to base.
        Query information_schema.tables WHERE table_schema = test_schema.
        Assert 0 tables exist (all dropped by downgrade).
        Assert alembic_version table is absent.
```

---

## SECTION 11: PHASE 2 DEFINITION OF DONE

Every item has an exact verification command. All items must pass before Phase 2 is shipped.

```
[ ] asyncpg==0.29.0 in requirements/base.txt
    Verify: grep asyncpg requirements/base.txt
    Expected: asyncpg==0.29.0

[ ] Docker services start cleanly
    Verify: docker compose up -d postgres redis && docker compose ps
    Expected: both services show "healthy" status

[ ] All 10 tables created in configured schema
    Verify: docker exec aip_postgres psql -U aip_user -d audience_intelligence \
              -c "SELECT table_name FROM information_schema.tables \
                  WHERE table_schema='public' ORDER BY table_name;"
    Expected: 10 rows including ga4_identity_bridge

[ ] feature_store has exactly 64 columns
    Verify: docker exec aip_postgres psql -U aip_user -d audience_intelligence \
              -c "SELECT COUNT(*) FROM information_schema.columns \
                  WHERE table_schema='public' AND table_name='feature_store';"
    Expected: 64

[ ] All ORM models import without errors
    Verify: python3 -c "from app.models.orm import *; print('OK')"
    Expected: OK (no ImportError, no ValidationError)

[ ] Settings load without errors
    Verify: python3 -c "from app.core.config import settings; print(settings.database.schema)"
    Expected: public (or configured schema name)

[ ] YAML feature count correct
    Verify: python3 -c "from app.core.config import settings; print(len(settings.ml.features.matrix))"
    Expected: 46

[ ] asyncpg import works
    Verify: python3 -c "import asyncpg; print(asyncpg.__version__)"
    Expected: 0.29.0

[ ] Alembic migration runs cleanly on fresh schema
    Verify: DATABASE__SCHEMA=phase2_test python3 scripts/run_migrations.py
    Expected: no error; alembic_version row written to phase2_test schema

[ ] All unit tests pass
    Verify: pytest tests/unit/ -v
    Expected: all tests PASSED; no FAILED or ERROR

[ ] All integration tests pass
    Verify: pytest tests/integration/ -v  (requires docker compose up -d postgres)
    Expected: all tests PASSED

[ ] Pre-commit passes on all new files
    Verify: pre-commit run --all-files
    Expected: all hooks Passed

[ ] /db-check skill passes
    Verify: run /db-check in Claude Code
    Expected: every DDL column has a matching ORM mapped_column, all 10 tables verified
```

**Total DoD items: 13**

---

## SECTION 12: RISKS SPECIFIC TO PHASE 2

### Risk 1: ENUM types — VARCHAR + CHECK schema evolution

**Decision taken:** VARCHAR + CHECK (see Section 5). This eliminates the risk entirely for this project.

**Residual risk:** CHECK constraints are not validated at Alembic autogenerate time by default — adding a new CHECK value requires a manual migration and DDL file update. Mitigation: the `/db-check` skill includes a CHECK constraint comparison step (verify DDL CHECK values match the Python Enum class values).

---

### Risk 2: feature_store 64-column DDL ↔ ORM mismatch

**Likelihood:** High — one miscounted or misspelled column is very likely during implementation.

**Mitigation:**
1. Section 4.10 provides every single `mapped_column()` declaration explicitly. The implementer copies from this spec, not from memory.
2. Test 4 in `tests/unit/test_models.py` asserts `column_count == 64` — this catches any count discrepancy at unit test time.
3. Test 4 in `tests/integration/test_migrations.py` queries the live database column count — catches DDL ↔ migration discrepancies.
4. `/db-check` skill is the final gate before Phase 2 ships.

**Rule:** The implementer must NOT abbreviate the feature_store ORM model or DDL. Every column must be written out explicitly.

---

### Risk 3: ga4_events index creation speed at 15M rows

**Context:** At Phase 2, the ga4_events table is empty (no data until Phase 5 synthetic data generation). Index creation at Phase 2 is instantaneous.

**Future risk (Phase 5+):** After synthetic data is seeded (15M rows), `CREATE INDEX` on user_pseudo_id and event_date will take ~10–30 seconds on a developer machine. This is acceptable.

**Decision:** Create all indexes inside the Alembic initial migration (alongside table creation). They run on an empty table at Phase 2. If indexes need to be added to a populated table in a future migration, use `CREATE INDEX CONCURRENTLY` to avoid table locks.

---

### Risk 4: asyncpg + psycopg2-binary coexistence

**Known compatibility:** asyncpg and psycopg2-binary serve different SQLAlchemy drivers and do not conflict. They can coexist in the same virtualenv without issue. asyncpg is used by `create_async_engine` (FastAPI async path); psycopg2-binary is used by `create_engine` (ETL/ML/Alembic sync path).

**Risk:** None at the library level. Both can be imported simultaneously.

**Verification:** `python3 -c "import asyncpg; import psycopg2; print('both OK')"` must succeed after Phase 2 pre-implementation step.

---

### Risk 5: Alembic autogenerate and CHECK constraints

**Issue:** Alembic autogenerate does NOT detect CHECK constraint changes by default in all versions. Changes to `CHECK (column IN (...))` may not generate a migration automatically.

**Mitigation:**
1. The initial migration is MANUAL — CHECK constraints are written explicitly in `op.execute()` calls inside the initial migration.
2. For future constraint changes, always write a MANUAL migration (not autogenerated). The pattern: `op.execute(text("ALTER TABLE {schema}.{table} DROP CONSTRAINT chk_...; ALTER TABLE {schema}.{table} ADD CONSTRAINT chk_... CHECK (...)"))`
3. Document this in the project's runbook (Phase 15).

---

### Risk 6: Docker volume persistence blocking clean-slate development

**Issue:** If `postgres_data` Docker volume already exists from a prior run, the `docker/postgres/init/` SQL scripts (which create the mlflow and airflow databases) do NOT re-run. The postgres container starts with the existing data volume.

**Mitigation — clean slate procedure:**
```bash
# Stop and remove containers + volumes
docker compose down -v   # -v removes named volumes including postgres_data

# Verify volumes are removed
docker volume ls | grep aip

# Restart — init scripts will run on fresh volume
docker compose up -d postgres redis

# Re-run migrations
python3 scripts/run_migrations.py
```

**Documentation:** This procedure must be in the project README (Phase 15). The `-v` flag is the critical difference between `docker compose down` (preserves data) and `docker compose down -v` (full reset).

---

## SECTION 13: QUESTIONS RESOLVED

### Q1 — ga4_events partitioning

**Decision: NO partitioning at Phase 2. Standard B-tree indexes only.**

At the 15M-row synthetic dataset scale (dev tier), PostgreSQL table partitioning adds schema complexity with no performance benefit:
- Table partitions require `PARTITION BY RANGE event_date` on the parent table and `CREATE TABLE ga4_events_YYYY_MM PARTITION OF ga4_events FOR VALUES FROM (...) TO (...)` for each partition.
- Alembic does not natively support partitioned table management — requires manual migrations for every new partition.
- At 15M rows, a B-tree index on `event_date` is sufficient for all ETL incremental queries (< 50ms per range scan).

**Scale trigger for partitioning:** When ga4_events exceeds 50M rows (mid-publisher tier, ~500K users). At that scale, the migration to a partitioned table requires a full table rebuild (`CREATE TABLE ... PARTITION BY RANGE` + `INSERT INTO ... SELECT FROM` old table). This migration is planned for the transition from pandas to dask backend (Phase 14 scaling work).

**DDL design consequence:** ga4_events uses `event_id UUID PRIMARY KEY` (not a composite PK that includes event_date). This means adding partitioning later requires dropping the PK constraint and recreating a composite PK — a planned breaking migration documented in the project risk log.

---

### Q2 — ENUM vs VARCHAR + CHECK

**Decision: VARCHAR + CHECK CONSTRAINT for ALL 14 ENUM types.**

See full justification in Section 5. Applied consistently. No exceptions.

---

### Q3 — Relationship definitions in ORM models

**Decision: FK column mappings only in Phase 2. No `relationship()` objects.**

The Phase 2 ORM models define FK columns (e.g., `user_id: Mapped[uuid.UUID]`) but NO SQLAlchemy `relationship()` definitions.

Rationale:
1. Phase 2 deliverables do not include any service layer code that uses ORM joins.
2. The feature builder (Phase 7) uses raw SQL aggregation queries via `session.execute()`, not ORM relationship traversal.
3. The API service layer (Phase 12) will use `selectinload()` / `joinedload()` with explicit options — these can be added to queries without `relationship()` on the model.
4. `relationship()` objects require `back_populates` pairs on both sides, which doubles the model complexity for no Phase 2 benefit.

**When to add:** Phase 12 (API layer) if ORM relationship traversal is needed for the persona service query patterns. Add then, not now.

---

### Q4 — feature_store upsert and unique constraint

**Confirmed:** The `user_id` column in `feature_store` is the PRIMARY KEY. PostgreSQL automatically creates a unique B-tree index on all PRIMARY KEY columns. Therefore:

```sql
INSERT INTO {schema}.feature_store (user_id, persona_label, ...)
VALUES (%s, %s, ...)
ON CONFLICT (user_id) DO UPDATE SET
    persona_label = EXCLUDED.persona_label,
    last_updated = EXCLUDED.last_updated,
    ...
```

This upsert pattern works without any additional `UNIQUE` constraint beyond the PK. No DDL change required.

**Performance note:** The `ON CONFLICT` clause must name `user_id` (not a column expression) — this matches the implicit unique index on the PK column directly.

---

### Q5 — ga4 bridge table

**Decision: ga4_identity_bridge is added as a 10th table.**

A persistent bridge table is required because:
1. The mapping from `user_pseudo_id` → `user_id` is discovered incrementally as users log in to GA4-tracked sessions. Without persistence, each ETL run must re-derive all mappings from the full event log — expensive and lossy for incremental processing.
2. The bridge table is small (~60% of total users = ~60K rows at dev scale). Storage cost is negligible.
3. The identity stitcher (Phase 6) writes to this table on every incremental run. Without it, incremental GA4 ingestion cannot correctly attribute sessions to previously-resolved users.

**Impact on Phase 2 deliverables:** Added `ga4_identity_bridge` to all sections. The Phase 2 deliverables list now includes 10 tables (not 9). The DDL numbering is 001–010.

---

### Q6 — Missing asyncpg in requirements

**Exact pre-implementation step:**

```bash
# Step 1: Add to requirements/base.txt (add after psycopg2-binary line)
# Open requirements/base.txt and insert:
asyncpg==0.29.0

# Step 2: Install in active virtualenv
pip install asyncpg==0.29.0

# Step 3: Verify
python3 -c "import asyncpg; print(f'asyncpg {asyncpg.__version__} OK')"

# Step 4: Commit the requirements/base.txt change as the first commit of Phase 2
git add requirements/base.txt
git commit -m "feat: phase 2 — add asyncpg==0.29.0 for async SQLAlchemy engine"
```

This must be the FIRST committed change in Phase 2 before any ORM or database.py code is written.

---

### Q7 — Alembic vs DDL files coexistence

**Decision: Alembic migrations are authoritative for execution. DDL files are authoritative for human reference.**

Full rationale in Section 7. The operational rule:

| Action | Who does it | What to update |
|--------|-------------|----------------|
| Add a new table | Engineer | Create DDL file + write Alembic migration + new ORM model |
| Rename a column | Engineer | Update DDL file + write manual Alembic migration (autogenerate treats as drop+add) + update ORM model |
| Add an index | Engineer | Update DDL file + write `op.execute("CREATE INDEX...")` migration |
| Validate sync | CI / db-check | Compare DDL file columns vs ORM mapped_columns vs live DB schema |

The `sql/ddl/` files are committed alongside the Alembic migration in the same PR. Divergence between them is a CI failure (db-check enforces this).

---

## COMPLETION SUMMARY

╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Database Schema Specification v1.1 complete ✅
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Saved to: .claude/specs/database-schema-spec.md
Sections completed: 13
Tables fully specified: 10 (9 source + ga4_identity_bridge)
Total columns specified: 126 across all 10 tables (feature_store: 64)
ENUMs defined: 14
Indexes specified: 29
Phase 2 files to create: 37
Open questions resolved: 7/7
Definition of done items: 13
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Next step: Review database-schema-spec.md.
Approve → run /create-spec 2 database-schema in Claude Code
to begin Phase 2 implementation.
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
