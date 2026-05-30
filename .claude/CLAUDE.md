# Audience Intelligence Platform — Master Project Context

## Project Overview
ML-powered audience segmentation and propensity scoring platform for digital publishers.
Ingests behavioral, subscription, email, social, and commerce data from 8 sources; builds a 46-feature matrix per user; trains K-Means clustering to assign one of 9 persona labels; exposes scores via FastAPI.

## Phase Tracker
| Phase | Name                   | Status    | Branch                            |
|-------|------------------------|-----------|-----------------------------------|
| 1     | environment-setup      | COMPLETE  | feature/phase1-environment-setup  |
| 2     | database-schema        | IN PROGRESS | feature/phase2-database-schema  |
| 3     | etl-ingestion          | PENDING   | feature/phase3-etl-ingestion      |
| 4     | feature-engineering    | PENDING   | feature/phase4-feature-engineering |
| 5     | ml-training            | PENDING   | feature/phase5-ml-training        |
| 6     | ml-inference           | PENDING   | feature/phase6-ml-inference       |
| 7     | api-layer              | PENDING   | feature/phase7-api-layer          |
| 8     | airflow-dags           | PENDING   | feature/phase8-airflow-dags       |
| 9     | monitoring             | PENDING   | feature/phase9-monitoring         |

## Tech Stack
| Layer           | Technology                                      |
|-----------------|-------------------------------------------------|
| API             | FastAPI 0.111, Uvicorn                          |
| ORM             | SQLAlchemy 2.0 (async)                          |
| Migrations      | Alembic 1.13                                    |
| Database        | PostgreSQL (schema: public, from configs/base.yaml) |
| Cache           | Redis 5.0                                       |
| Data Processing | Pandas 2.2, NumPy 1.26                          |
| ML              | scikit-learn 1.4, XGBoost 2.0, LightGBM 4.3, HDBSCAN 0.8, Optuna 3.6 |
| Experiment Tracking | MLflow 2.13                               |
| Orchestration   | Apache Airflow                                  |
| Config          | Pydantic-settings 2.7, PyYAML 6.0               |
| Logging         | structlog 24.1                                  |
| Python          | 3.11+                                           |

## Folder Structure
```
.
├── app/
│   ├── core/           # Config loader, DB engine, Redis client, logging setup
│   ├── models/
│   │   └── orm/        # SQLAlchemy ORM models (one file per table)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/  # FastAPI route handlers
│   ├── services/       # Business logic layer (no direct DB calls in endpoints)
│   └── utils/          # Shared helpers
├── etl/
│   ├── ingestion/      # One extractor per source: zephr, ga4, braintree, sailthru, pushly, openweb, trackonomics, transunion
│   ├── transforms/     # Feature engineering transformers
│   └── identity/       # User identity resolution
├── ml/
│   ├── feature_store/  # Feature computation and storage
│   ├── training/
│   │   ├── algorithms/ # K-Means, HDBSCAN, ensemble wrappers
│   │   └── evaluation/ # Silhouette scoring, stability checks
│   ├── inference/      # Persona assignment, propensity scoring
│   ├── pipelines/      # End-to-end pipeline orchestration
│   └── experiments/    # MLflow experiment configs
├── sql/
│   ├── ddl/            # CREATE TABLE scripts (one per table, uses {schema} placeholder)
│   └── analytics/      # Analytical query templates
├── dags/               # Airflow DAG definitions
├── configs/
│   ├── base.yaml       # Source of truth for all config values
│   ├── dev.yaml        # Dev overrides
│   └── prod.yaml       # Prod overrides (no secrets)
├── tests/
│   ├── unit/           # Fast, isolated tests (mock DB/Redis/APIs)
│   └── integration/    # Tests requiring real services
├── scripts/            # run_migrations.py, seed_database.py, run_pipeline.py
├── requirements/
│   ├── base.txt        # Production dependencies
│   └── dev.txt         # Dev/test dependencies
└── docker/             # docker-compose.yml and service configs
```

## Git Branch Naming Convention
```
feature/phaseN-short-name    # Phase work (e.g. feature/phase2-database-schema)
fix/short-description        # Bug fixes
chore/short-description      # Non-feature work
```
Always branch from `main`. Always open a PR back to `main`.

## Coding Standards
- Python 3.11+, type hints on every function signature
- Black (line-length=88) + isort (profile=black) + flake8 + mypy (strict)
- No `Any` types — use proper generics or Union
- No `# type: ignore` without a comment explaining why
- SQLAlchemy 2.0 style: `select()`, `Session.scalars()`, no legacy `Query`
- All DB operations must go through the service layer, never direct in endpoints
- All config values read from `configs/base.yaml` via the app config object — no hardcoded numbers
- All SQL DDL files must use `{schema}` placeholder for the schema name
- All ORM models must have `__table_args__ = {"schema": settings.database.schema}`
- structlog for all logging — no bare `print()` in production code
- No bare `except:` — always catch specific exceptions
- Pydantic models for all API input/output validation

## The 9 Persona Labels
```
loyalist               # Long-tenure, high billing cycles, engaged readers
subscription_focused   # High newsletter count, strong open/click rates
high_value_shopper     # High conversion rate, avg transaction value, affiliate clicks
sports_focused         # Dominant ratio_sports, nl_sports_alerts subscriber
social_engager         # High comments, likes, shares
occasional_buyer       # ratio_shopping dominant, sporadic affiliate clicks
celebrity_entertainment # ratio_celebrity + ratio_entertainment dominant
casual_reader          # Default / low-signal cluster
low_engager            # High bounce rate, days_since_last_visit dominant
```

## The 46 Feature Names (ml.features.matrix)
```
total_sessions, total_pageviews, active_days, avg_session_duration,
avg_pages_per_session, bounce_rate, mobile_ratio, desktop_ratio,
pageviews_per_session, days_since_last_visit, account_age_days,
ratio_sports, ratio_entertainment, ratio_celebrity, ratio_shopping,
ratio_opinion, ratio_world_news, ratio_business, ratio_lifestyle,
has_subscription, subscription_amount, total_billing_cycles, days_until_renewal,
newsletter_count, open_rate, click_through_rate, email_engagement_score,
nl_sports_alerts, nl_morning_report, nl_page_six_daily, nl_celebrity_news,
nl_evening_update, nl_post_opinion,
total_comments, total_likes_given, total_shares, social_engagement_score,
total_affiliate_clicks, total_transactions, total_revenue_generated,
conversion_rate, avg_transaction_value, unique_advertisers_clicked,
age_score, income_score, has_children
```

## Database Schema — 9 Tables
| # | Table Name          | Primary Source     | Description                                      |
|---|---------------------|--------------------|--------------------------------------------------|
| 1 | user_profiles       | Zephr              | Core identity: user_id, email, account_age_days  |
| 2 | user_sessions       | GA4                | Behavioral: sessions, pageviews, bounce_rate     |
| 3 | content_affinity    | GA4                | Section ratios: ratio_sports, ratio_celebrity …  |
| 4 | subscriptions       | Zephr + Braintree  | has_subscription, amount, billing_cycles, renewal|
| 5 | email_engagement    | Sailthru + Pushly  | Newsletter flags, open_rate, CTR, score          |
| 6 | social_activity     | OpenWeb            | Comments, likes, shares, social_engagement_score |
| 7 | commerce_activity   | Trackonomics       | Affiliate clicks, transactions, revenue, CVR     |
| 8 | feature_store       | Computed           | All 46 features per user, updated each pipeline run |
| 9 | persona_assignments | ML output          | user_id → persona label + propensity scores + run_id |

## ETL Sources and Modes
| Source       | Mode          | Key Data                              |
|--------------|---------------|---------------------------------------|
| zephr        | incremental   | User accounts, subscription state     |
| ga4          | incremental   | Sessions, pageviews, content sections |
| braintree    | incremental   | Payments, billing cycles              |
| sailthru     | full_refresh  | Newsletter subscriptions, engagement  |
| pushly       | incremental   | Push notification engagement          |
| openweb      | incremental   | Comments, social reactions            |
| trackonomics | incremental   | Affiliate clicks and transactions     |
| transunion   | full_refresh  | Demographic enrichment (age, income)  |

## Propensity Score Weights (must sum to 1.0 per type)
- **subscription**: newsletter_count_scaled(0.30) + open_rate_scaled(0.25) + days_since_last_visit_scaled_inverted(0.25) + dist_to_subscription_focused_inverted(0.20) = 1.00
- **churn**: days_since_last_visit_scaled(0.40) + bounce_rate_scaled(0.30) + total_billing_cycles_scaled_inverted(0.30) = 1.00
- **commerce**: ratio_shopping_scaled(0.35) + total_affiliate_clicks_scaled(0.30) + dist_to_high_value_shopper_inverted(0.35) = 1.00

## Cold Start Rules (in priority order)
1. ratio_sports > 0.50 → sports_cold_start
2. (ratio_celebrity + ratio_entertainment) > 0.50 → celebrity_cold_start
3. has_subscription == True → subscription_cold_start
4. newsletter_count > 0 → newsletter_cold_start
5. default → new_user

## Never-Do Rules
1. NEVER hardcode config values — always read from `configs/base.yaml` via the settings object
2. NEVER commit `.env` or any file containing real secrets
3. NEVER commit `venv/` or `.venv/` to git
4. NEVER commit real client API keys, database credentials, or PII
5. NEVER use `SELECT *` in production queries — always name columns explicitly
6. NEVER put business logic directly in FastAPI endpoint functions
7. NEVER write SQL DDL without the `{schema}` placeholder
8. NEVER write an ORM model without `__table_args__ = {"schema": settings.database.schema}`
9. NEVER leave TODOs, placeholders, or pseudo-code in committed files
10. NEVER skip type hints on any function
