# SOURCE DOCUMENT 1: Audience Intelligence Spec v3

AUDIENCE INTELLIGENCE PLATFORM

Phase 1 — Complete Engineering Specification

Multi-Algorithm ML Audience Segmentation System

Version 3.0  |  Revised & Approved

Incorporates all 8 correction items from peer review

Confidential — For Internal Engineering Use

Revision History

This document supersedes v2.0. All peer review corrections have been applied.

1. Business Problem & Objectives

1.1 Core Problem Statement

Digital publishers own massive reader datasets spanning web behaviour, email engagement, social interactions, push notifications, and commerce — yet monetise them as if these datasets don't exist. Audience segments are editorial guesses hardcoded into CMS rules: they are defined by humans, not discovered from data.

The consequences are measurable and costly:

Newsletters reach the wrong readers → low CTR, high unsubscribe rates

Ad inventory is sold at run-of-site CPMs instead of premium, persona-verified rates

Subscription upsells trigger at random moments to unqualified users → low conversion

Churn is detected too late — only after a subscriber cancels, not while they are drifting

High-value readers (Loyalists, High Value Shoppers) are invisible and therefore untargeted

1.2 Primary Revenue Goals

1.3 Secondary Goals

Build a reusable, vendor-agnostic product deployable to any digital publisher regardless of existing tech stack

Replace intuition-driven editorial segmentation with ML clustering that discovers natural audience groups from actual behaviour

Create adaptive segments — personas evolve automatically as new data is ingested, no manual reconfiguration

Surface hidden micro-segments that editorial teams would never define manually

Provide a single unified reader view across web, email, push, social, and commerce

Support flexible cluster counts — 5 for small publishers, 12+ for large — without re-architecting the pipeline

1.4 NYPost Validation Benchmark

2. Specification Corrections — v3.0 [v3.0 REVISED]

The following 8 items were identified during peer review of v2.0. Each correction is documented below with the original problem, the fix applied, and where it appears in the updated spec.

Fix 1 — F-01: feature_store removed from input list

CORRECTION APPLIED:

F-01 now reads: Ingest delta data from 8 source tables (zephr_users, ga4_events, braintree_subscriptions, sailthru_newsletter, pushly_subscribers, openweb_engagement, trackonomics_clicks, transunion_demographics). feature_store is a pipeline output and is written in Step 8. It is never read as an ETL source.

Fix 2 — F-18a/b/c: Propensity Score Derivation Formulas

CORRECTION APPLIED — Propensity scores are derived from centroid distances and scaled feature combinations, NOT from separate supervised models. The formulas are:

Fix 3 — Feature Count: Canonical 46-Feature List

CORRECTION APPLIED — The canonical ML feature matrix contains exactly 46 numeric columns. This list is authoritative. It is reproduced in configs/base.yaml under ml.features.matrix. Any engineer needing the feature list reads it from config, never hardcodes it.

Fix 4 — Cold-Start Rules Defined

CORRECTION APPLIED — Cold-start rules are defined below and stored in configs/base.yaml under cold_start.rules. cold_start.py reads rules from config, never hardcodes them.

Rule evaluation order matters: conditions are checked top-to-bottom and the first match wins. A user with both sports content and a newsletter subscription gets sports_cold_start, not newsletter_cold_start.

These rules are applied by the GET /persona/{user_id} endpoint when the user_id is not found in the Redis cache (cold-start path). The API response includes persona_label and a is_cold_start: true flag so downstream systems can handle cold-start users differently.

Fix 5 — F-31: Persona Distribution Drift Alert [v3.0 REVISED]

NEW REQUIREMENT F-31:

Fix 6 — F-32: Feature Importance Computation Method [v3.0 REVISED]

NEW REQUIREMENT F-32:

Fix 7 — Git Strategy: Branch Convention & configs/clients/ Security

CORRECTION APPLIED:

Fix 8 — Database Scope: PostgreSQL vs BigQuery vs Redshift

CORRECTION APPLIED — Authoritative database scope decision:

Connection pattern in app/core/config.py: DatabaseSettings has POSTGRES_URL, BIGQUERY_PROJECT, BIGQUERY_DATASET, REDIS_URL as separate fields. ETL modules use the connection appropriate to their source. The feature engineering pipeline writes ONLY to PostgreSQL.

3. Functional Requirements (Complete — v3.0)

All requirements from v2.0 are included below with v3.0 corrections applied. Requirements marked [v3.0] are new or corrected.

3.1 Data Ingestion

3.2 Feature Engineering

3.3 ML Pipeline

3.4 API Serving

3.5 Monitoring & Alerting

4. Non-Functional Requirements

5. ML Architecture

5.1 ML Objective

5.2 Algorithm Selection Framework

5.3 4-Stage Algorithm Pipeline (Per Client Deployment)

5.4 K Selection by Publisher Size

6. System Architecture

6.1 Architecture Diagram (Text Representation)

The following describes the end-to-end data flow from source systems to downstream activation:

6.2 Airflow DAG — 9 Steps

7. Technology Decision Log

8. Project Folder Structure

Every file and directory listed below is intentional. Rationale follows the structure.

9. Database Design Plan

9.1 Schema Strategy

9.2 Table Summary

10. Synthetic Data Generation Strategy

10.1 Design Principles

10.2 Synthetic Data Volumes

11. Expected Persona Definitions & ML Outputs

11.1 Primary Personas

11.2 Propensity Scores

12. Success KPIs

12.1 ML Model KPIs

12.2 Business Performance KPIs

13. Deployment & Scaling Strategy

13.1 Scaling Tiers

13.2 Infrastructure Components

14. Project Roadmap — 15 Phases

15. Risk Register

16. Phase 1 Approval Checklist

Upon approval of this document, Phase 2 (Design) will begin. Phase 2 will produce: system sequence diagrams for all 9 Airflow steps, full OpenAPI contract for all 4 API endpoints, database ERD for all 9 tables, component interaction diagrams, and the detailed design for the FeatureEngineering backend abstraction layer.

Version | Change | Status
v1.0 | Initial spec draft | Superseded
v2.0 | Phase 1 spec — full system scope | Superseded
v3.0 | 8 peer-review corrections applied. F-01 fixed. F-18 propensity formulas specified. 46 features listed explicitly. Cold-start rules defined. F-31 distribution drift added. F-32 feature importance method added. Git conventions updated. Database scope clarified. | CURRENT

ℹ  NOTE
Every section updated in this revision is marked with [v3.0 REVISED] in the section heading. Sections without this marker are unchanged from v2.0.

Goal | Mechanism | Target | Primary Signal
Subscription Revenue | Identify Subscription-Focused readers before they churn. Trigger upsell at the right behavioural moment. | +15–25% subscription conversion rate vs non-personalised baseline | Braintree + Sailthru + Zephr
Ad Revenue | Serve advertisers verified high-intent segments commanding premium CPMs. | +20–40% CPM uplift on segmented vs run-of-site inventory | GA4 + Trackonomics
Newsletter Engagement | Personalise newsletter content per persona — each reader receives articles matching proven content affinity. | +30–50% CTR improvement on segmented newsletters | Sailthru + GA4
Churn Reduction | Identify Low Engagers and dormant users early, trigger re-engagement before they leave. | -20% annual churn rate on identified at-risk segments | Zephr + GA4 recency

✓  DECISION
This platform is directly inspired by the New York Post Data Labs initiative, which segmented 66 million users across 8 source systems using Bisecting K-Means, discovering 9 personas. This blueprint extends that foundation with a multi-algorithm evaluation framework so the product is not locked to a single clustering approach.

✗  FIX REQUIRED
ORIGINAL PROBLEM: F-01 incorrectly listed feature_store as one of the 9 input tables to ingest. feature_store is a pipeline OUTPUT written in Step 8, not a source system. A junior engineer reading the original spec would wire up an ingestion module for a table that doesn't exist as a source.

✗  FIX REQUIRED
ORIGINAL PROBLEM: F-18 said 'compute 3 propensity scores' with no derivation method. Without formulas, Phase 11 engineers might build a separate logistic regression model for each score — adding a supervised training dependency where none was intended.

F-18a | subscription_propensity_score = sigmoid(
  w1 × newsletter_count_scaled +
  w2 × open_rate_scaled +
  w3 × (1 − days_since_last_visit_scaled) +
  w4 × dist_to_subscription_focused_centroid_inverted
)
Weights: w1=0.30, w2=0.25, w3=0.25, w4=0.20. Calibrated against held-out Braintree conversion labels in offline evaluation. Weights stored in configs/base.yaml as propensity.subscription.weights.
F-18b | churn_propensity_score = sigmoid(
  w1 × days_since_last_visit_scaled +
  w2 × bounce_rate_scaled +
  w3 × (1 − total_billing_cycles_scaled)
)
Weights: w1=0.40, w2=0.30, w3=0.30. Higher days_since_last_visit and bounce_rate with fewer billing cycles = higher churn risk.
F-18c | commerce_propensity_score = sigmoid(
  w1 × ratio_shopping_scaled +
  w2 × total_affiliate_clicks_scaled +
  w3 × dist_to_high_value_shopper_centroid_inverted
)
Weights: w1=0.35, w2=0.30, w3=0.35. Distance to high_value_shopper centroid is the dominant signal.
Sigmoid | All three scores use: sigmoid(x) = 1 / (1 + e^(-x)). Output range is always 0.0–1.0. Centroid distances are inverted (1 − normalised_distance) so that proximity = high score.
Weight Storage | All weights live in configs/base.yaml under propensity: section. No weights are hardcoded in Python. Weights can be overridden per client in configs/clients/{client}.yaml.

✗  FIX REQUIRED
ORIGINAL PROBLEM: Section 6.3 stated '46 features total' but did not list them explicitly. Different engineers building the feature builder, the scaler, and the clustering algorithm could produce different feature matrices. This fix establishes the canonical feature list as the single source of truth.

# | Feature Name | Source | Type | Notes
1 | total_sessions | GA4 | INTEGER | Log1p transformed
2 | total_pageviews | GA4 | INTEGER | Log1p transformed
3 | active_days | GA4 | INTEGER
4 | avg_session_duration | GA4 | FLOAT | Seconds
5 | avg_pages_per_session | GA4 | FLOAT
6 | bounce_rate | GA4 | FLOAT | 0.0–1.0
7 | mobile_ratio | GA4 | FLOAT | 0.0–1.0
8 | desktop_ratio | GA4 | FLOAT | 0.0–1.0
9 | pageviews_per_session | GA4 | FLOAT | Derived
10 | days_since_last_visit | GA4 | INTEGER | Recency signal
11 | account_age_days | Zephr | INTEGER | Tenure signal
12 | ratio_sports | GA4 | FLOAT | Content affinity
13 | ratio_entertainment | GA4 | FLOAT | Content affinity
14 | ratio_celebrity | GA4 | FLOAT | Content affinity
15 | ratio_shopping | GA4 | FLOAT | Content affinity
16 | ratio_opinion | GA4 | FLOAT | Content affinity
17 | ratio_world_news | GA4 | FLOAT | Content affinity
18 | ratio_business | GA4 | FLOAT | Content affinity
19 | ratio_lifestyle | GA4 | FLOAT | Content affinity
20 | has_subscription | Braintree+Zephr | BINARY | 0 or 1
21 | subscription_amount | Braintree | FLOAT | Monthly USD
22 | total_billing_cycles | Braintree | INTEGER | Tenure signal
23 | days_until_renewal | Braintree | INTEGER | Churn proximity
24 | newsletter_count | Sailthru | SMALLINT
25 | open_rate | Sailthru | FLOAT | 0.0–1.0
26 | click_through_rate | Sailthru | FLOAT | 0.0–1.0
27 | email_engagement_score | Sailthru | SMALLINT | 0/1/2
28 | nl_sports_alerts | Sailthru | BINARY | Newsletter flag
29 | nl_morning_report | Sailthru | BINARY | Newsletter flag
30 | nl_page_six_daily | Sailthru | BINARY | Newsletter flag
31 | nl_celebrity_news | Sailthru | BINARY | Newsletter flag
32 | nl_evening_update | Sailthru | BINARY | Newsletter flag
33 | nl_post_opinion | Sailthru | BINARY | Newsletter flag
34 | total_comments | Openweb | INTEGER | Social signal
35 | total_likes_given | Openweb | INTEGER | Social signal
36 | total_shares | Openweb | INTEGER | Social signal
37 | social_engagement_score | Openweb | INTEGER | Derived composite
38 | total_affiliate_clicks | Trackonomics | INTEGER | Log1p transformed
39 | total_transactions | Trackonomics | INTEGER
40 | total_revenue_generated | Trackonomics | FLOAT | USD
41 | conversion_rate | Trackonomics | FLOAT | 0.0–1.0
42 | avg_transaction_value | Trackonomics | FLOAT | USD
43 | unique_advertisers_clicked | Trackonomics | INTEGER | Commerce breadth
44 | age_score | Transunion | SMALLINT | Ordinal 1–6
45 | income_score | Transunion | SMALLINT | Ordinal 1–6
46 | has_children | Transunion | BINARY | 0 or 1

ℹ  NOTE
Columns EXCLUDED from ML matrix (stored in feature_store but not fed to clustering): user_id, email, persona_label, cluster_id, algorithm_used, cluster_score, last_updated, subscription_plan, push_opted_in, push_is_active, push_platform_* (these are metadata or post-clustering outputs). The 46 columns above are the only inputs to StandardScaler and all clustering algorithms.

✗  FIX REQUIRED
ORIGINAL PROBLEM: The spec referenced 'rule-based cold-start logic' in F-25 and cold_start.py but defined no rules. Engineers building the API and the business logic module would produce incompatible implementations.

Sessions | Condition (evaluated in order) | persona_label Assigned
0–1 | Any — new registration | new_user
2–4 | ratio_sports > 0.50 in available session data | sports_cold_start
2–4 | (ratio_celebrity + ratio_entertainment) > 0.50 | celebrity_cold_start
2–4 | has_subscription = TRUE (from Zephr at registration) | subscription_cold_start
2–4 | newsletter_count > 0 (from first Sailthru sync) | newsletter_cold_start
2–4 | None of the above | new_user
5–9 | User included in next weekly batch run. First ML persona assigned within 3–10 days. | ML-assigned (batch)
10+ | Stable ML persona. Full propensity scores. All activation channels. | ML-assigned (stable)

✗  FIX REQUIRED
ORIGINAL PROBLEM: F-26 through F-30 covered silhouette score, stability, coverage, and runtime — but not persona distribution drift. A data pipeline failure (e.g. sports content ingestion breaks) can cause a persona's share to drop dramatically without triggering any existing alert.

F-31 Definition | Weekly persona distribution (% of users per persona) is logged to MLflow as a JSON artifact and surfaced in Grafana as a stacked bar trend chart.
Alert Condition | Alert if any persona changes by > 30% RELATIVE week-over-week. Formula: abs(this_week_pct - last_week_pct) / last_week_pct > 0.30. Example: Sports Focused drops from 10.0% to 6.5% = 35% relative drop = alert fires.
Alert Channel | PagerDuty severity P2 (not P1 — this is a data quality signal, not a system outage). Includes: persona name, current %, prior week %, relative change %, and link to Grafana panel.
False Positive Mitigation | Low Engager is exempt from this alert — its share can fluctuate significantly as new user volumes change. Alert applies to all other 8 personas. Threshold configurable per client in configs/clients/{client}.yaml.
Implementation | Computed in Step 8 (Write-Back) after clustering. Distribution dict written to MLflow via mlflow_logger.log_persona_distribution(). Grafana panel reads from MLflow via the MLflow API.

✗  FIX REQUIRED
ORIGINAL PROBLEM: Section 6.6 mentioned 'feature importance per cluster' as an MLflow artifact but provided no computation method. Without this, Phase 9 produces numerically labelled clusters with no mechanism to name them.

F-32 Definition | After each clustering run, compute per-cluster feature importance as the normalised centroid deviation from the global mean. Formula: importance[cluster][feature] = abs(centroid[cluster][feature] − global_mean[feature]) / global_std[feature]
Output | Top 5 features per cluster logged to MLflow as a JSON artifact: {cluster_id: [[feature_name, importance_score], ...]}. Also written to feature_store.cluster_top_features column as JSON string for API access.
Algorithm Variants | K-Means / Bisecting K-Means: use cluster centroids directly. GMM: use component means. HDBSCAN: use per-cluster feature medians (HDBSCAN has no centroids).
Persona Naming Logic | The persona_naming module in ml/training/evaluation/interpretability.py takes the top-5 feature list per cluster and maps it to a persona_label using a lookup table defined in configs/base.yaml under personas.naming_rules. Example rule: if ratio_sports is rank-1 AND nl_sports_alerts is in top-3 → label = sports_focused.
Business Use | Grafana dashboard shows the top-5 feature bars per persona. This is the output that allows the business team to understand why Cluster 3 is called Sports Focused. Without it, cluster labels are opaque numbers.
Implementation File | ml/training/evaluation/interpretability.py — compute_feature_importance(centroids, feature_names, global_stats) → dict. Called by clustering_pipeline.py after every run.

✗  FIX REQUIRED
ORIGINAL PROBLEM: The Git strategy showed feature/phase2-database-schema but did not formalise the phase-branching convention. Also missing: a .gitignore rule preventing real client credentials from being committed to configs/clients/.

Branch Convention | Every phase gets its own branch off main. Branch names MUST include the phase number. Format: feature/phaseN-<description>. Example: feature/phase4-database-schema, feature/phase9-ml-training-pipeline.
Sequential Merges | Phases are merged to main in order. Phase 5 branch is cut from main AFTER Phase 4 is merged. No parallel phase branches. This ensures the folder structure and config files are stable before the next phase builds on them.
configs/clients/ Rule | configs/clients/ contains per-client configuration that may include API keys, schema names, and proprietary business thresholds. This directory is NEVER committed with real credentials. Rules: (1) Add configs/clients/*.yaml to .gitignore EXCEPT configs/clients/example.yaml. (2) configs/clients/example.yaml is a template with placeholder values. (3) Real client files created locally from the template and never staged.
Pre-commit Hook | A pre-commit hook (added in Phase 14) scans staged files for patterns matching API keys, passwords, and connection strings. Any match blocks the commit and prints the offending line. Hook config lives in .pre-commit-config.yaml.
PR Requirements | Every PR must: (1) pass CI (lint + tests), (2) include the phase number in the PR title, (3) have a description referencing the deliverables in the roadmap. No direct pushes to main. Branch protection enforced via GitHub repository settings.

✗  FIX REQUIRED
ORIGINAL PROBLEM: The spec listed PostgreSQL as the database but the production path references BigQuery and Redshift. The GA4 ETL module reads from BigQuery but writes to PostgreSQL — two different connection types that both need to be in the spec before anyone writes database connection code.

Database | Role | Environment | Notes
PostgreSQL | Application database for feature_store, all 8 source staging tables, metadata tables, pipeline audit logs. | Development + Small/Mid client production | SQLAlchemy ORM. Schema-per-client pattern. All DDL uses {schema} placeholder. Never hardcode public schema.
Google BigQuery | GA4 event source (read-only). GA4 BigQuery export is the native GA4 data path. ETL reads from BigQuery and writes aggregate user features to PostgreSQL. | Any client using GA4 | BigQuery connection is a READ source only. It is never the application database. Connection string in .env as BIGQUERY_PROJECT and BIGQUERY_DATASET.
Amazon Redshift | Large-client alternative to PostgreSQL for feature_store at > 10M users. | Large client production only | Not implemented in Phase 4. The SQLAlchemy abstraction layer means migration requires only a config change, not a code rewrite. Designed in, not built yet.
Redis | Persona serving cache. Not a database — a cache layer. TTL = 7 days. | All environments | Separate from all SQL databases. Connection string in .env as REDIS_URL.

ID | Requirement | Status
F-01 [v3.0] | Ingest delta data from 8 source tables: zephr_users, ga4_events, braintree_subscriptions, sailthru_newsletter, pushly_subscribers, openweb_engagement, trackonomics_clicks, transunion_demographics. feature_store is a pipeline OUTPUT written in Step 8 — it is never an ETL source. | CORRECTED
F-02 | Resolve all source-specific IDs to universal user_id (UUID) via identity stitching. Resolution map: ga4 user_pseudo_id → user_id via bridge table; sailthru email → user_id via zephr_users.email; transunion hashed_email → user_id via zephr_users.hashed_email; pushly external_id = user_id; openweb user_id = user_id via SSO. | Unchanged
F-03 | Validate row counts and schema on every ingestion run. Abort pipeline if any source deviates > 20% from prior week's row count. Log deviation percentage per source to MLflow. | Unchanged
F-04 | Support full-refresh and incremental (delta) ingestion modes per source. Mode configurable in configs/base.yaml under etl.{source}.mode. | Unchanged
F-05 | Transunion match confidence check: exclude records where match_confidence < 0.70 from the ML feature matrix. Records are stored in transunion_demographics table but flagged. ETL logs match rate and exclusion count. | Unchanged

ID | Requirement | Status
F-06 | Aggregate GA4 event rows to one user-level row. Computed aggregates: total_sessions, total_pageviews, active_days, avg_session_duration, avg_pages_per_session, bounce_rate (single-page sessions < 10s / total), mobile_ratio, desktop_ratio, pageviews_per_session, days_since_last_visit, and all 8 ratio_* content affinity features (each = pageviews in category / total pageviews). | Unchanged
F-07 | Apply log1p transformation before StandardScaler to: total_sessions, total_pageviews, total_affiliate_clicks, total_comments. These features are right-skewed with large outliers. log1p(0) = 0 so zero-padded null users are unaffected. | Unchanged
F-08 | NULL handling: users absent from optional sources (Pushly = 35% coverage, Openweb = 23%, Trackonomics = 16%) receive 0 for all numeric features in that source block. Never drop users for missing source data. | Unchanged
F-09 | Exclude new users from clustering: users with total_sessions ≤ 4 AND no commerce, social, or subscription data from any source are assigned is_new_user = TRUE. These users receive persona_label = 'new_user' and skip all clustering steps. | Unchanged
F-10 | Derived feature: social_engagement_score = (total_comments × 3) + (total_likes_given × 1) + (total_shares × 2). Computed after join, before scaling. | Unchanged
F-11 | Derived feature: email_engagement_score ordinal encoding: 0 if open_rate < 0.15 (low), 1 if 0.15 ≤ open_rate ≤ 0.35 (medium), 2 if open_rate > 0.35 (high). Thresholds configurable in configs/base.yaml. | Unchanged
F-12 | Expand subscribed_newsletters pipe-delimited field into 10 binary nl_* flags: nl_sports_alerts, nl_morning_report, nl_page_six_daily, nl_celebrity_news, nl_evening_update, nl_post_opinion, nl_breaking_news, nl_real_estate, nl_tech_news, nl_lifestyle_weekly. Missing newsletter subscription = 0. | Unchanged

ID | Requirement | Status
F-13 | Implement 4-stage algorithm evaluation pipeline per client deployment. Stage 1: HDBSCAN discovery (no K specified). Stage 2: BisectingKMeans + GMM evaluated at K = (natural_K ± 3). Stage 3: best algorithm+K selected by composite score. Stage 4: production runs with weekly monitoring. | Unchanged
F-14 | Composite score for algorithm+K selection: silhouette score (40% weight) + business interpretability score (40%) + stability across 3 runs with different random seeds (20%). Interpretability score is computed by interpretability.py — a cluster passes if it has a distinct nameable profile, a distinct activation strategy, and contains ≥ 0.5% of total users. | Unchanged
F-15 | Support 5 algorithms: BisectingKMeans (sklearn), KMeans (sklearn), GaussianMixture (sklearn), HDBSCAN (hdbscan library), Ensemble (majority vote across KMeans + GMM + HDBSCAN). | Unchanged
F-16 | Fit StandardScaler on ML feature matrix after log1p transforms. Persist scaler as MLflow artifact (scaler.pkl) with every run. Inference always loads the training-time scaler — never re-fits on new data mid-pipeline. | Unchanged
F-17 | Write back to feature_store after each run: persona_label, cluster_id, algorithm_used, cluster_score, last_updated. Write is upsert (INSERT ... ON CONFLICT DO UPDATE) — never append, never truncate-reload. | Unchanged
F-18 [v3.0] | Compute 3 propensity scores per user using centroid distance formulas defined in Fix 2 (Section 2). Scores are NOT from supervised models. Weights stored in configs/base.yaml. Full formulas: see Section 2, Fix 2. | CORRECTED
F-19 | GMM runs produce soft_persona_scores: a 9-element float array (posterior probabilities) summing to 1.0. Stored as JSON string in feature_store.soft_persona_scores. Exposed via API in soft_scores field. | Unchanged
F-20 | Safety gate: if silhouette score < 0.30 after production clustering run, do not write new persona assignments. Keep prior week's assignments. Send P1 alert to PagerDuty. Log incident to MLflow with full diagnostics. | Unchanged

ID | Requirement | Status
F-21 | GET /api/v1/persona/{user_id} — returns: persona_label, cluster_id, propensity_scores (subscription, churn, commerce), soft_scores (GMM only, null otherwise), algorithm_used, last_updated, is_cold_start (bool). | Unchanged
F-22 | GET /api/v1/personas/batch — body: {user_ids: [UUID, ...]} max 1,000 IDs per request. Returns map of user_id → persona response. Batch reads from Redis pipeline (single round-trip). | Unchanged
F-23 | GET /api/v1/health — returns: pipeline_last_run (timestamp), silhouette_score (last run), persona_coverage_pct, redis_connected (bool), db_connected (bool). | Unchanged
F-24 | POST /api/v1/admin/pipeline/trigger — admin API key required. Triggers Airflow DAG run via Airflow REST API. Returns dag_run_id for tracking. | Unchanged
F-25 [v3.0] | Cold-start path: user_id not in Redis cache → apply rules from Fix 4 (Section 2) → return cold-start persona with is_cold_start: true. Never return 404 for a valid user_id. Cold-start rules defined in configs/base.yaml. | CORRECTED

ID | Requirement | Status
F-26 | Weekly silhouette score logged to Grafana. Alert (PagerDuty P2) if drops > 0.05 vs prior week. | Unchanged
F-27 | Persona stability (% users with same persona as prior week) tracked. Trigger Stage 2 re-evaluation if < 80% for 3 consecutive weeks. | Unchanged
F-28 | Feature coverage (% users with data per source) tracked daily. PagerDuty P1 alert if GA4 coverage < 90%. | Unchanged
F-29 | Pipeline runtime tracked per step. Alert if any step exceeds 2× its rolling median runtime (computed over last 4 runs). | Unchanged
F-30 | MLflow logs per run: algorithm, K, silhouette, per-cluster silhouette, persona distribution, feature importance top-5 per cluster, scaler artifact, inertia curve across K=5 to K=15. | Unchanged
F-31 [v3.0 NEW] | Weekly persona distribution (% users per persona) logged to MLflow + Grafana. PagerDuty P2 alert if any persona changes by > 30% relative WoW. Low Engager exempt (high natural variance). Threshold configurable per client. Implementation in Step 8 (Write-Back). | NEW
F-32 [v3.0 NEW] | After each clustering run: compute per-cluster feature importance as abs(centroid[feature] − global_mean[feature]) / global_std[feature]. Log top-5 features per cluster to MLflow as JSON. Write to feature_store.cluster_top_features. Used by Grafana dashboard and persona naming logic in interpretability.py. | NEW

Category | Requirement | Measurement
Latency | GET /persona/{user_id} p99 < 10ms (Redis). Batch endpoint p99 < 100ms. | Prometheus histogram in Grafana
Throughput | API handles 10,000 req/sec at peak ad serving load. | Load test in CI with locust
Availability | Persona serving API: 99.9% uptime SLA. Pipeline downtime acceptable during weekly batch window (Sunday 02:00–06:00 UTC). | Uptime Robot
Scalability | Feature engineering supports 1M–100M users via backend swap: pandas (dev) → dask (mid) → pyspark (large). Same interface, config-driven. | Backend flag in configs/base.yaml
Security | PII fields (last_name, email) masked in analytics environments. hashed_email never exposed via API. All endpoints require API key (X-API-Key header). Keys rotated quarterly. | Automated PII scan in CI
Reproducibility | All MLflow runs reproducible: random_state=42 everywhere, scaler artifact logged, K selection rationale documented in MLflow run tags. | MLflow run comparison
Multi-tenancy | Each client has isolated PostgreSQL schema. No cross-client queries possible via ORM (schema enforced at session level). | Integration test: cross-schema access rejected
Auditability | Every clustering run logs: trigger source (manual/schedule), algorithm selected, rationale, silhouette, delta vs prior week. | MLflow run history
Test Coverage | ≥ 80% coverage on ETL, feature engineering, and API code. All ML pipeline steps have integration tests against synthetic data. | pytest-cov report in CI
Config-Driven | No hardcoded K, algorithm choice, feature lists, thresholds, weights. All tunable parameters in YAML. | grep check in CI: fail if hardcoded values detected

Type | Unsupervised clustering. No ground-truth labels exist for training. The algorithm discovers natural behavioural segments.
Primary Output | persona_label (9 human-readable classes) + cluster_id (integer for programmatic use)
Secondary Output | 3 propensity scores (subscription, churn, commerce) — centroid-distance based, not supervised
Tertiary Output | soft_persona_scores (GMM only): 9-element float array summing to 1.0. Per-cluster feature importance top-5.
Evaluation | No train/test split — unsupervised. Quality measured by silhouette score, Davies-Bouldin index, and business interpretability score. Persona stability WoW is the production health metric.

Algorithm | Mechanism | Best For | Weakness
Bisecting K-Means | Recursively divide largest cluster until K reached. | Large publishers (10M+). Fast, deterministic, scalable. | Assumes spherical clusters. Sensitive to outliers.
Standard K-Means | Iteratively assign to nearest centroid. | Mid-size (1M–10M) with balanced personas. | Local minima risk — run multiple seeds.
GMM | Probabilistic soft membership assignments. | Publishers wanting nuanced soft scores, overlapping personas. | Slower. Needs regularisation. Degenerate solutions possible.
HDBSCAN | Density-based. Finds clusters as dense regions. | Discovery phase — find natural K before running K-Means. | Non-deterministic. Outliers = noise not a cluster.
Ensemble | Majority vote: K-Means + GMM + HDBSCAN. | Premium clients: accuracy > speed. | 3x compute cost. High pipeline complexity.

Stage | Name | Description | Output | Timing
1 | Discovery | Run HDBSCAN on full feature matrix. Do NOT specify K. Let algorithm reveal natural dense groups. | Natural K estimate (e.g. K=7). Cluster size distribution. Outlier rate. | Week 1
2 | Evaluation | Run BisectingKMeans + GMM across K = (natural_K ± 3). Score each with silhouette, inertia, Davies-Bouldin, and business interpretability. | Silhouette scores, inertia curves, top-3 candidate configs. | Weeks 1–2
3 | Selection | Select algorithm+K with highest composite score: silhouette 40% + interpretability 40% + stability 20%. Document in MLflow. | Final config: e.g. BisectingKMeans K=9, silhouette=0.41. | Week 2
4 | Production | Run selected config weekly. Monitor silhouette + stability. Re-trigger Stage 2 if silhouette drops > 0.05 or stability < 80% for 3 weeks. | Weekly persona assignments. Monitoring reports. | Week 3 onwards

Publisher Size | Recommended K | Rationale
Small (< 1M users) | 5–7 | Small user base per cluster. Over-segmenting creates clusters too small to activate.
Mid (1M–10M) | 7–9 | Standard range. Matches NYPost's 9-cluster finding.
Large (10M–50M) | 9–12 | Supports finer-grained segmentation. Sub-cluster Low Engagers into 2–3 groups.
Niche/vertical | 4–6 | Sports-only or finance-only publishers: less content diversity, fewer meaningful archetypes.
Multi-brand | 12–15 | Multiple properties (news + sports + entertainment) add cluster complexity.

SOURCE SYSTEMS (8 tables)
Zephr  ·  GA4/BigQuery  ·  Braintree  ·  Sailthru  ·  Pushly  ·  Openweb  ·  Trackonomics  ·  Transunion
         ↓ Daily/Weekly delta ingestion
AIRFLOW ETL PIPELINE (9 Steps)
1: Ingest → 2: Identity Stitch → 3: Feature Eng → 4: Validate → 5: Scale
6: Algo Eval → 7: Cluster → 8: Write-Back → 9: Cache Refresh
         ↓                          ↓
PostgreSQL (feature_store)     MLflow Registry (scaler, centroids, metrics)
         ↓
Redis Cache (persona per user_id, TTL = 7 days)
         ↓
FastAPI Persona Serving API
GET /persona/{user_id}  ·  GET /personas/batch  ·  GET /health  ·  POST /admin/pipeline/trigger
         ↓
DOWNSTREAM ACTIVATION
Sailthru (newsletter)  ·  GAM/Xandr (ads)  ·  Zephr (upsell)  ·  CMS (homepage)
         ↓
MONITORING: Grafana + PagerDuty + MLflow

Step | Name | Description | Fail Behaviour
1 | Source Ingestion | Pull delta data from all 8 sources. Validate row counts ± 20% vs prior week. | Abort pipeline if any source deviates > 20%
2 | Identity Stitching | Resolve all source IDs to user_id. Log unresolved rates per source. | Continue with resolved users. Log unresolved rate.
3 | Feature Engineering | Aggregate GA4 to user level. Compute ratio_*, bounce_rate, mobile_ratio, log1p transforms, derived features. | Abort if feature matrix row count < 80% of prior week
4 | Feature Validation | Check feature distributions for drift. Flag if > 20% mean shift on any feature. Abort if > 3 features drift simultaneously. | Abort pipeline. Use prior week. P1 alert.
5 | StandardScaler Fit | Fit scaler on ML feature matrix. Save to MLflow. Apply log1p (already applied in Step 3). | Abort if scaler fit fails (data shape mismatch)
6 | Algorithm Evaluation | Run BisectingKMeans + GMM for K=5 to K=15. Compute silhouette + interpretability. Select best config. Skip if same config as prior week. | Use prior week's config if evaluation fails
7 | Production Clustering | Run selected algorithm at chosen K. Compute silhouette. If < 0.30, abort write-back. | Abort write-back. Keep prior week. P1 alert.
8 | Write-Back | Upsert persona_label, cluster_id, algorithm_used, cluster_score, last_updated to feature_store. Log persona distribution (F-31). Log feature importance (F-32). | Abort and alert. Do not partial-write.
9 | Cache Refresh + Notify | Push updated records to Redis (TTL=7d). Fire webhooks to Sailthru, ad server, CMS. | Continue even if webhook fails. Log failure.

Decision | Choice | Rationale | Alternatives Rejected
Application DB | PostgreSQL 15 | ACID, UUID support, schema-per-client pattern, Docker-friendly, SQLAlchemy-native. | MySQL (weaker UUID/JSON support), SQLite (no multi-tenant schemas)
GA4 Source | BigQuery (read-only) | GA4 native export path. Read via google-cloud-bigquery in ETL module. Never the application DB. | Direct GA4 API (rate-limited, no historical data)
Feature Engineering | Pandas (dev), swap layer to Dask/PySpark via config | Sufficient for 100K synthetic rows. Interface abstraction means no rewrite at scale. | PySpark from day one (overkill for dev, heavy Docker footprint)
ML Framework | scikit-learn + hdbscan | BisectingKMeans, GMM, silhouette_score all native. MLflow-compatible. Reproducible. | PyTorch (overkill for clustering), Spark MLlib (reserved for > 10M users)
Experiment Tracking | MLflow (self-hosted) | Tracks params, metrics, artifacts, model registry. Docker Compose service. Free. | W&B (SaaS cost), Neptune (SaaS cost)
Hyperparameter Tuning | Optuna | Bayesian optimisation. Async-friendly. MLflow integration. Best-in-class for K and algorithm tuning. | GridSearchCV (exhaustive, slow for K=5 to K=15 × 5 algorithms)
API Framework | FastAPI | Async, auto OpenAPI docs, Pydantic validation, industry standard for ML serving. | Flask (no async), Django REST (heavy)
Cache | Redis 7 | Sub-ms reads, TTL support, Redis pipeline for batch reads, Docker Compose service. | Memcached (no TTL per key), DynamoDB (cloud cost, latency)
Orchestration | Airflow 2.x (Docker Compose) | DAG-based, widely understood, 9-step pipeline maps naturally. MWAA upgrade path when needed. | Prefect (less mature), Dagster (steeper learning curve for this team)
Config | Pydantic Settings + YAML | Type-safe config. Environment variable override. Hierarchical: base → client override. | Dynaconf (less standard), raw JSON (no type safety)
Testing | Pytest | Fixtures, parametrize, coverage, CI-native. Industry standard. | Unittest (verbose), Nose (deprecated)
CI/CD | GitHub Actions | Native GitHub integration. Free tier sufficient. Docker build + lint + test pipeline. | Jenkins (infra overhead), CircleCI (cost)

audience_intelligence_platform/
│
├── app/                            # FastAPI application
│   ├── api/v1/endpoints/
│   │   ├── persona.py              # GET /persona/{id}, /personas/batch
│   │   ├── health.py               # GET /health
│   │   └── pipeline.py             # POST /admin/pipeline/trigger
│   ├── core/
│   │   ├── config.py               # Pydantic settings (all env vars)
│   │   ├── logging.py              # Structured JSON logger
│   │   └── security.py             # API key middleware
│   ├── models/orm/                 # SQLAlchemy ORM (9 tables, schema param)
│   ├── schemas/persona.py          # Pydantic response schemas
│   ├── services/
│   │   ├── persona_service.py      # Business logic
│   │   └── cache_service.py        # Redis read/write
│   ├── utils/cold_start.py         # Rule-based cold-start logic
│   └── main.py
│
├── etl/
│   ├── ingestion/                  # 8 source ingestion modules
│   │   ├── zephr.py
│   │   ├── ga4.py                  # Reads from BigQuery
│   │   ├── braintree.py
│   │   ├── sailthru.py
│   │   ├── pushly.py
│   │   ├── openweb.py
│   │   ├── trackonomics.py
│   │   └── transunion.py
│   ├── identity/stitcher.py        # ID resolution across all 8 sources
│   └── transforms/feature_engineering.py
│
├── ml/
│   ├── training/
│   │   ├── train.py                # Entry point
│   │   ├── algorithms/
│   │   │   ├── bisecting_kmeans.py
│   │   │   ├── gmm.py
│   │   │   ├── hdbscan_discovery.py
│   │   │   └── ensemble.py
│   │   └── evaluation/
│   │       ├── metrics.py          # Silhouette, Davies-Bouldin, inertia
│   │       └── interpretability.py # Feature importance (F-32), naming
│   ├── inference/predict.py
│   ├── pipelines/
│   │   ├── feature_pipeline.py     # Steps 3–5
│   │   └── clustering_pipeline.py  # Steps 6–8
│   ├── feature_store/
│   │   ├── builder.py              # Assembles 46-feature matrix
│   │   └── validator.py            # Feature drift detection (Step 4)
│   └── experiments/mlflow_logger.py
│
├── sql/
│   ├── ddl/                        # 9 SQL scripts with {schema} placeholder
│   │   ├── 001_create_zephr_users.sql
│   │   ├── 002_create_ga4_events.sql
│   │   ├── ... (through 009)
│   │   └── 009_create_feature_store.sql
│   └── analytics/
│       ├── persona_distribution.sql
│       └── feature_coverage.sql
│
├── data/
│   ├── raw/                        # gitignored
│   ├── processed/                  # gitignored
│   ├── synthetic/                  # Generated files committed for dev
│   └── external/                   # Transunion batch files (gitignored)
│
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_algorithm_evaluation.ipynb
│   └── 04_persona_profiling.ipynb
│
├── tests/
│   ├── unit/
│   │   ├── test_feature_engineering.py
│   │   ├── test_algorithms.py
│   │   ├── test_propensity_scores.py
│   │   └── test_persona_service.py
│   ├── integration/
│   │   ├── test_etl_pipeline.py
│   │   ├── test_api_endpoints.py
│   │   └── test_cold_start.py
│   └── conftest.py
│
├── configs/
│   ├── base.yaml                   # Canonical config (features, weights, rules)
│   ├── dev.yaml                    # Dev overrides (pandas backend)
│   ├── prod.yaml                   # Prod overrides (dask/spark backend)
│   └── clients/
│       ├── example.yaml            # COMMITTED — template only
│       └── nypost.yaml             # NOT committed (gitignored)
│
├── dags/audience_intelligence_dag.py  # Airflow 9-step DAG
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.pipeline
│   └── Dockerfile.mlflow
│
├── scripts/
│   ├── generate_synthetic_data.py
│   ├── seed_database.py
│   ├── run_pipeline.py
│   └── evaluate_algorithms.py
│
├── .github/workflows/
│   ├── ci.yml                      # Lint + test on every PR
│   └── cd.yml                      # Docker build + push on merge to main
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── Makefile
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── .env.example
└── .pre-commit-config.yaml

Schema Pattern | Every SQL DDL script uses a {schema} placeholder. Every SQLAlchemy ORM model includes __table_args__ = {'schema': settings.DB_SCHEMA}. This supports multi-tenant deployment (schema-per-client) without any code changes — only a config value changes.
Table Count | 9 tables: 8 source staging tables + 1 output table (feature_store). All source tables store both raw and resolved user_id. Raw source IDs retained for debugging identity resolution failures.
Primary Keys | All PKs are UUID type. Avoids sequential ID leakage. Enables distributed ID generation without coordination.
Universal FK | user_id UUID is the universal foreign key. All 8 source tables reference zephr_users(user_id). Referential integrity enforced at DB level in production; relaxed in synthetic data generation for performance.
Audit Columns | All tables have created_at TIMESTAMP DEFAULT NOW() and updated_at TIMESTAMP. ETL upserts update updated_at. Enables point-in-time debugging.
Indexes | user_id indexed on all FK columns. event_date indexed on ga4_events (partition key for large-scale query performance). persona_label + cluster_id indexed on feature_store (downstream query patterns). match_confidence indexed on transunion_demographics.
feature_store Update Pattern | Upsert only: INSERT INTO feature_store ... ON CONFLICT (user_id) DO UPDATE SET .... Never truncate-reload. This preserves the prior week's assignment if Step 7 silhouette gate fires.

Table | Rows (100K users) | Refresh Pattern | Join Key | Notes
zephr_users | 100K | Registration write + incremental updates | user_id (PK) | Master identity table. Golden record.
ga4_events | 15M | Daily BigQuery export, partitioned by date | user_pseudo_id → user_id via bridge | Only event-level table. Aggregated in Step 3.
braintree_subscriptions | 10K | Event-driven on state change | customer_id = user_id | 10% subscription rate in synthetic data.
sailthru_newsletter | 100K | Weekly refresh or daily delta | email → user_id via zephr_users | 1 aggregate row per user.
pushly_subscribers | 35K | Daily delta sync | external_id = user_id | 35% opt-in coverage.
openweb_engagement | 23K | Daily delta sync | user_id via SSO (direct FK) | 23% coverage. Most reliable join.
trackonomics_clicks | 500K | Daily SFTP export | user_id as URL parameter | Multiple clicks per user. 16% coverage.
transunion_demographics | 70K | Monthly batch refresh | hashed_email → user_id | 70% match rate. Exclude < 0.70 confidence.
feature_store | 100K | Weekly full upsert (Steps 3–8) | user_id (PK) | ML-ready output table. 46 feature columns + 5 output columns.

Persona Injection | Every synthetic user is pre-assigned a ground-truth persona during generation. Feature distributions are drawn from persona-specific parameter sets. This allows validation that the ML pipeline recovers near the injected persona distribution.
Class Imbalance | Persona distribution mirrors documented real-world proportions: Low Engager ≈ 50%, Casual Reader ≈ 15%, Sports Focused ≈ 10%, etc. Class imbalance is real — the pipeline must handle it.
Coverage Gaps | Source coverage is simulated: Pushly 35%, Openweb 23%, Trackonomics 16%, Transunion 70%. Users absent from a source get NULL in the raw table and 0 in the feature matrix.
Seasonality | GA4 event timestamps follow weekly patterns (higher weekday traffic) and annual patterns (sports content spikes during NFL/NBA/MLB seasons). Timestamps span a 12-month synthetic observation window.
Outliers | 1–2% of users are anomalous: bot-like users (thousands of sessions in hours), power users (top 0.01% pageviews), payment failures. These test pipeline robustness without breaking the clustering.
Referential Integrity | All FKs resolve: every user_id in a child table exists in zephr_users. No orphan records. Identity stitching is designed to succeed on 95%+ of synthetic data.
Realistic Distributions | Not uniform random. Loyalists get total_sessions ~ Normal(150, 30). Low Engagers get total_sessions ~ Normal(3, 1.5). Parameter sets defined in scripts/generate_synthetic_data.py::PERSONA_PARAMS dict.

Table | Synthetic Rows | Notes
zephr_users | 100,000 | All 9 personas represented in documented proportions
ga4_events | 15,000,000 | ~150 events/user avg. Partitioned by event_date over 12 months.
sailthru_newsletter | 100,000 | 1 row per user (aggregate)
braintree_subscriptions | 10,000 | 10% subscription rate. Mix of Active/Canceled/Past Due.
pushly_subscribers | 35,000 | 35% of users. Mix of platforms.
openweb_engagement | 23,000 | 23% of users. Heavy right skew on total_comments.
trackonomics_clicks | 500,000 | Multiple clicks per commerce user. 16% user coverage.
transunion_demographics | 70,000 | 70% match rate. match_confidence drawn from Beta(8,2).
feature_store (output) | ~95,000 | ~5% excluded as new_user (is_new_user = TRUE)

Persona | Approx Size (65M base) | Defining Features (top signals) | Primary Activation
loyalist | 738K (1.1%) | High total_sessions (500+/yr), high account_age_days, desktop_ratio > 0.6, total_billing_cycles > 12, open_rate > 0.40 | Renewal campaigns, premium content, loyalty rewards
subscription_focused | 1.8M (2.8%) | newsletter_count 4–5, high open_rate, Sports+ uptake, is_registered completeness | Subscription conversion, tier upsell
high_value_shopper | 413K (0.6%) | Highest conversion_rate, avg_transaction_value, unique_advertisers_clicked, ratio_shopping > 0.35 | Premium affiliate placements, retail brand campaigns
sports_focused | 6.6M (10.1%) | ratio_sports > 0.50, nl_sports_alerts = 1, high push click_rate on sports alerts, age_score 1–2 (18–34) | Sports+ upsell, sports brand advertising
social_engager | 5.0M (7.7%) | Highest total_comments, total_likes_given, total_shares. Community-first behaviour. | Community features, UGC campaigns, comment-driven content
occasional_buyer | 1.9M (2.9%) | Moderate total_affiliate_clicks, highest ratio_shopping, low conversion_rate vs high_value_shopper | Retargeting, commerce content promotion
celebrity_entertainment | 6.3M (9.7%) | Highest ratio_celebrity + ratio_entertainment combined. High total_shares on entertainment. | Entertainment brand advertising, Page Six campaigns
casual_reader | 10.0M (15.4%) | Broad content (no dominant ratio_*), moderate sessions, low subscription intent, mobile_ratio > 0.6 | Newsletter acquisition, recommendation engine
low_engager | 32.9M (50.6%) | Lowest engagement across all signals. bounce_rate > 0.70. No strong content preference. days_since_last_visit > 60. | Re-engagement flows, win-back sequences

Score | Range | High Score Meaning | Formula Location
subscription_propensity_score | 0.0–1.0 | High likelihood of converting to paid subscription within 90 days | Section 2, Fix 2, F-18a. Weights in configs/base.yaml::propensity.subscription.weights
churn_propensity_score | 0.0–1.0 | High likelihood of subscription cancellation within 30 days | Section 2, Fix 2, F-18b. Weights in configs/base.yaml::propensity.churn.weights
commerce_propensity_score | 0.0–1.0 | High likelihood of affiliate click converting to transaction | Section 2, Fix 2, F-18c. Weights in configs/base.yaml::propensity.commerce.weights
soft_persona_scores (GMM only) | 9-element float[] | Posterior probability of membership in each persona. Enables nuanced multi-label targeting. | Output of GaussianMixture.predict_proba(). Stored as JSON string.

KPI | Target | Cadence | Alert Rule
Silhouette Score (overall) | > 0.35 | Weekly | P2 alert if drops > 0.05 vs prior week
Silhouette Score (per cluster) | > 0.25 for all clusters | Weekly | P2 alert if any cluster < 0.20
Persona Stability (WoW) | > 85% users same persona | Weekly | Re-trigger Stage 2 if < 80% for 3 consecutive weeks
Algorithm Consistency (KMeans vs GMM) | > 75% agreement on non-Low-Engager users | Weekly | Trigger ensemble mode if < 70% agreement
Feature Coverage — GA4 | > 95% | Daily | P1 alert if < 90%
Feature Coverage — Transunion | > 65% | Monthly | P2 alert if < 60%
Cluster Size Balance | Largest cluster < 60% of total users | Weekly | Re-evaluate K if Low Engager > 60%
Persona Distribution Drift (F-31) | No persona changes > 30% relative WoW | Weekly | P2 alert. Low Engager exempt.

KPI | Target | Cadence | Alert Rule
Newsletter CTR by Persona | +30–50% CTR lift vs unsegmented control | Per send / weekly | Flag if lift < 15% for 3 consecutive weeks
Subscription Conversion Rate | +15–25% vs non-segmented baseline | Monthly | Alert if rate drops > 5% vs prior month
Ad CPM by Segment | +20–40% premium for Sports Focused and High Value Shoppers | Monthly | Monthly revenue team report
Revenue Per User (RPU) | High Value Shoppers RPU > 5× Low Engager RPU | Monthly | Track cohort RPU trend over 6 months
Churn Rate by Persona | Overall churn -20% YoY after activation | Monthly | Alert if any persona churn > 5% in a month
Re-engagement Rate (Low Engager) | 5–10% re-engagement rate per campaign | Per campaign | Benchmark each campaign vs prior
Persona Coverage | ≥ 80% of registered users have ML persona | Weekly | Alert if coverage drops below 75%
Commerce Conversion Rate Lift | +25% conversion lift vs non-segmented | Monthly | Monthly affiliate performance report

Tier | Infrastructure | Feature Engineering | Clustering | Pipeline Cadence
Small (< 1M users) | Single machine or small cloud VM (16GB RAM). All services via Docker Compose. | Pandas. Feature store fits in RAM. Step 3 < 10 min. | scikit-learn. All 5 algorithms evaluatable in < 2 hours. | Weekly clustering. Daily feature refresh optional.
Mid (1M–10M) | Cloud VM (32–64GB RAM). Dask for feature engineering. | Dask. Step 3 < 30 min. Parallel aggregation. | scikit-learn BisectingKMeans. Evaluation 2–4 hours. | Weekly clustering. Daily feature refresh.
Large (10M–50M) | Spark cluster (5–10 nodes, 32GB each). Managed Airflow. | PySpark. Step 3 < 2 hours. | Spark MLlib for KMeans. HDBSCAN on 10% sample. 4–8 hours. | Weekly clustering. Daily feature refresh.
NYPost Scale (50M–100M) | 20-node Spark cluster. MWAA or Cloud Composer. | PySpark. 3–4 hours. | Spark MLlib. HDBSCAN monthly only. 2–3 hours. | Weekly clustering. Daily feature updates.

✓  DECISION
Phase 4 builds for Small tier (Pandas + scikit-learn + Docker Compose). The FeatureEngineering class backend parameter and MLBackend abstraction are implemented from day one, making tier upgrades a config change, not a rewrite.

Component | Technology | Purpose | SLA
Application DB | PostgreSQL 15 (Docker) | Stores all 9 tables including feature_store | 99.9% uptime in production
Feature Engineering | Pandas (dev) / Dask / PySpark (prod) | Steps 3–5 of Airflow DAG | Complete within batch window
ML Training | scikit-learn / Spark MLlib | Steps 6–7: algorithm evaluation + clustering | Complete within batch window
Model Registry | MLflow (Docker) | Artifact storage, experiment tracking, model versioning | Best effort (not on serving path)
Orchestration | Airflow 2.x (Docker Compose) | 9-step DAG with validation gates | Weekly trigger reliability
Persona Serving API | FastAPI + Uvicorn (Docker) | Real-time persona retrieval | p99 < 10ms, 99.9% uptime
Cache Layer | Redis 7 (Docker) | Persona + propensity per user_id, TTL = 7 days | p99 < 1ms read
Monitoring | Grafana + Prometheus (Docker) | Pipeline metrics, silhouette trend, business KPIs | Alerts within 5 min of trigger

Phase | Name | Key Deliverables | Depends On
1 | SPEC (COMPLETE) | This document. All 8 corrections applied. | —
2 | DESIGN | Sequence diagrams. API contract (OpenAPI). DB ERD. Component interaction map. | Phase 1 approved
3 | TASKS | Full task breakdown. File-by-file build plan. Acceptance criteria per file. | Phase 2 approved
4 | DATABASE | 9 SQL DDL scripts ({schema} placeholder). SQLAlchemy ORM models. Index definitions. Migration scripts. configs/clients/nypost.yaml template. | Phase 3
5 | SYNTHETIC DATA | generate_synthetic_data.py: 9 tables, persona injection, realistic distributions, referential integrity. seed_database.py. | Phase 4
6 | ETL PIPELINE | 8 ingestion modules. identity/stitcher.py. Row count validation. Delta vs full-refresh modes. | Phase 5
7 | FEATURE ENGINEERING | feature_store/builder.py (46 features). validator.py (drift detection). log1p transforms. NULL handling. | Phase 6
8 | EDA | 4 Jupyter notebooks: distributions, feature correlations, source coverage analysis, preliminary cluster exploration. | Phase 7
9 | ML TRAINING | 5 algorithm modules. evaluation/metrics.py. evaluation/interpretability.py (F-32). clustering_pipeline.py. K selection logic. | Phase 8
10 | MLFLOW | mlflow_logger.py. Experiment tracking integration. Artifact logging. Model registry setup. Scaler persistence. | Phase 9
11 | PROPENSITY SCORES | 3 propensity score modules (F-18a/b/c formulas). Weight loading from config. Integration with feature_store write-back. | Phase 10
12 | FASTAPI | 4 endpoints. Redis cache service. Cold-start logic (F-25 rules from config). Batch endpoint. Health endpoint. | Phase 11
13 | AIRFLOW DAG | 9-step DAG. Validation gates. Fail-safe fallback logic. persona distribution drift logging (F-31). | Phase 12
14 | DOCKER + CI/CD | 3 Dockerfiles. docker-compose.yml (all 7 services). GitHub Actions ci.yml + cd.yml. Pre-commit hooks. | Phase 13
15 | TESTING + DOCS | Pytest suite (≥ 80% coverage). README with local setup. API reference. Architecture decision log. | Phase 14

Risk | Likelihood | Impact | Mitigation
GA4 identity resolution failures (anonymous users never log in) | High | Medium | Log unresolved rates in Step 2. Anonymous users excluded from clustering — they remain as 'anonymous' and get run-of-site content. Rate tracked in Grafana.
Low Engager cluster dominates (> 60% of users) | Medium | High | Sub-cluster Low Engagers into 2–3 groups at higher K. Cluster size balance check (F-KPI) automatically alerts and triggers K re-evaluation.
Silhouette score below 0.30 safety threshold | Medium | High | Step 7 silhouette gate: abort write-back, keep prior week's assignments, fire P1 alert. System fails safe — users always have a persona.
Transunion match rate below 65% | Low | Medium | Demographic features are supplementary (3 of 46 features). Pipeline continues without them. Missing demographics = 0 imputation. Alert if match rate drops > 10% vs prior month.
Pipeline runtime exceeds SLA at growing data volumes | Medium | Medium | Dask/PySpark swap layer designed in from Phase 4. Trigger migration when Step 3 exceeds 30 minutes consistently.
Persona drift from data quality issue (not modelling issue) | Medium | High | Feature drift detection gate in Step 4 aborts pipeline if > 3 features drift > 20% simultaneously. This catches pipeline failures before they corrupt persona assignments.
Real client API credentials committed to Git | Low | Critical | configs/clients/*.yaml gitignored (except example.yaml). Pre-commit hook scans for credential patterns. Enforced in Phase 14.
Cluster interpretability fails (unnamed clusters) | Low | Medium | F-32 feature importance computation + persona naming rules in configs/base.yaml::personas.naming_rules guarantee every cluster gets a label. Tested in Phase 9 integration tests.

✓  DECISION
All 8 correction items from peer review have been incorporated into this document. The checklist below confirms each item is resolved before Phase 2 begins.

Item | Correction | Location in Doc | Status
1 | F-01: feature_store removed from input list | Section 3.1, F-01 | ✓ RESOLVED
2 | F-18a/b/c: Propensity score derivation formulas specified | Section 2 Fix 2; Section 3.3 F-18 | ✓ RESOLVED
3 | 46 features listed explicitly in canonical list | Section 2 Fix 3; Section 5.1 (46-feature table) | ✓ RESOLVED
4 | Cold-start rules defined and referenced to configs/base.yaml | Section 2 Fix 4; Section 3.4 F-25 | ✓ RESOLVED
5 | F-31: Persona distribution drift alert added | Section 2 Fix 5; Section 3.5 F-31 | ✓ RESOLVED
6 | F-32: Feature importance computation method defined | Section 2 Fix 6; Section 3.5 F-32 | ✓ RESOLVED
7 | Git convention formalised; configs/clients/ gitignore rule added | Section 2 Fix 7; Section 8 folder structure | ✓ RESOLVED
8 | PostgreSQL vs BigQuery vs Redshift scope clarified | Section 2 Fix 8; Section 7 Tech Decisions | ✓ RESOLVED

Sign-off | Name / Role | Date | Signature
Technical Review
ML Architecture
Product Owner



---

# SOURCE DOCUMENT 2: Audience Intelligence Blueprint v2

Contents

1. Business Objective

1.1  Primary Revenue Goals

1.2  Secondary Goals

Build a reusable, vendor-agnostic product deployable to any digital publisher regardless of their existing tech stack.

Replace intuition-driven editorial segmentation with ML clustering that discovers natural audience groups from actual behaviour.

Create adaptive segments — personas evolve automatically as new data is ingested, no manual reconfiguration needed.

Surface hidden micro-segments that editorial teams would never define manually, unlocking net-new revenue opportunities.

Provide a single unified view of each reader across web, email, push, social, and commerce touchpoints.

Support flexible cluster counts — 5 clusters for small publishers, 12+ for large publishers — without re-architecting the pipeline.

2. Complete Schema — All Tables & Fields

The platform uses 9 tables: 8 source tables and 1 output feature store. All connect through user_id, the universal identifier issued by Zephr at registration.

2.1  zephr_users — Master Identity (Golden Record)

Join key: user_id — primary key, all other tables reference this

2.2  ga4_events — Web Behaviour

Join key: user_pseudo_id → user_id via bridge table (resolved on login event)

2.3  braintree_subscriptions — Payments

Join key: customer_id → user_id (set equal at subscription creation)

2.4  sailthru_newsletter — Email Engagement

Join key: email → user_id via zephr_users.email (100% registered user coverage)

2.5  pushly_subscribers — Push Notifications

Join key: external_id → user_id (set equal at push opt-in, ~35% user coverage)

2.6  openweb_engagement — Social Engagement

Join key: user_id directly via SSO token — no resolution needed (~23% coverage)

2.7  trackonomics_clicks — Commerce & Affiliate

Join key: user_id passed as URL parameter in affiliate links (~16% coverage)

2.8  transunion_demographics — Third-Party Demographics

Join key: hashed_email batch-matched to Transunion TruAudience API (~70% match rate)

2.9  feature_store — ML Feature Matrix (Output Table)

One row per registered user. All 8 source tables aggregate here. The ML-ready subset has 40+ normalised numeric features. persona_label, cluster_id, algorithm_used, and confidence score are written back after each pipeline run.

Web Behaviour Features — from GA4

Content Affinity Features — from GA4 (all FLOAT, 0.0–1.0)

Subscription Features — from Braintree + Zephr

Email Features — from Sailthru

Social Features — from Openweb

Commerce Features — from Trackonomics

Demographic Features — from Transunion

Output Columns — written back after clustering

3. ML Strategy — Algorithms, Cluster Selection & Optimisation

3.1  Algorithm Comparison & Selection Framework

Five algorithms are evaluated for every new client deployment. Each has distinct strengths depending on data characteristics:

3.2  Optimal Cluster Count Selection

How many clusters (K) is the right number is one of the most important — and most misunderstood — decisions in the pipeline. The answer varies by publisher size, content breadth, and business granularity requirements.

Method 1 — Elbow Method (Inertia Curve)

Plot inertia (sum of squared distances from centroid) against K from 5 to 20. The elbow point — where adding more clusters gives diminishing returns — indicates the optimal K.

Method 2 — Silhouette Score (Best Separation)

The silhouette score measures how similar a user is to their own cluster vs other clusters. Range: -1 (wrong cluster) to +1 (perfect cluster). Target overall score > 0.35. Run for K=5 to K=15 and select K with highest silhouette score.

Method 3 — Business Interpretability Check

After identifying the statistically optimal K, verify each cluster is actually interpretable and actionable for the business team. A cluster only earns its place if it passes three checks:

It has a distinct, nameable behavioural profile (e.g. high sports ratio + high push click rate = Sports Focused)

It has a distinct activation strategy that differs from adjacent clusters

It contains at least 0.5% of total users (too small = not scalable for campaigns)

If a cluster fails these checks, merge it with its nearest neighbour and reduce K by 1.

Recommended K Ranges by Publisher Size

3.3  Recommended Algorithm Pipeline (Per Client Deployment)

The platform runs a standardised 4-stage algorithm evaluation on every new client deployment, then selects the best-performing configuration:

3.4  Expected ML Outputs & Personas

The pipeline produces persona assignments, propensity scores, soft membership probabilities (GMM), and model diagnostics.

Primary Output: Persona Assignments

Secondary Output: Propensity Scores

Tertiary Output: Model Diagnostics (per run)

Overall silhouette score and per-cluster silhouette scores

Algorithm used and K selected for this run

Inertia curve across K=5 to K=15 (stored in MLflow)

Persona stability report: % of users who changed persona vs prior week

Feature importance per cluster: top 5 features driving each centroid

Coverage report: % of users with data from each source system

Outlier rate: % of users classified as noise by HDBSCAN in discovery stage

4. Expected KPIs

KPIs are measured at two levels: ML model quality (is the clustering working?) and business performance (is it making money?).

4.1  ML Model KPIs

4.2  Business Performance KPIs

5. Data Volume Expectations

5.1  Row Counts per Source (per year, per 1M registered users)

5.2  Scaling Tiers

6. Deployment Expectations

6.1  Infrastructure Stack

6.2  Airflow DAG — 9 Steps

7. Batch vs Real-Time Inference

7.1  Why Batch for Clustering

7.2  What IS Real-Time

7.3  New User Cold-Start Strategy

8. Expected Users of the System

8.1  Technical Users

8.2  Business Users

8.3  End Users (Readers)

8.4  Publishing Client Users (SaaS Deployment Model)

— End of Document —

Audience Intelligence Platform
Complete Product Blueprint — Multi-Algorithm ML Edition
Inspired by the New York Post Data Labs Audience Segmentation Initiative
Covers: Schema · Business Objective · ML Outputs · KPIs · Data Volumes · Deployment · Inference Strategy · System Users
Version 2.0  |  Confidential — For Prospective Publishing Clients

1.  Business Objective | 3
2.  Complete Schema — All 9 Tables | 4
3.  ML Strategy — Algorithms, Cluster Selection & Optimisation | 12
3.1  Algorithm Comparison & Selection Framework | 12
3.2  Optimal Cluster Count Selection | 13
3.3  Recommended Algorithm Pipeline | 14
3.4  Expected ML Outputs & Personas | 15
4.  Expected KPIs | 17
5.  Data Volume Expectations | 18
6.  Deployment Expectations | 19
7.  Batch vs Real-Time Inference | 21
8.  Expected Users of the System | 22

Core Problem Statement
Digital publishers hold massive reader datasets but monetise them poorly. Traditional audience segments are editorial guesses — defined by humans, not data. Newsletters reach the wrong readers, ads serve low-intent users, subscription upsells are untargeted, and high-value readers are indistinguishable from low-value ones. Revenue is lost at every touchpoint.

Goal | Mechanism | Target | Primary Signal
Subscription Revenue | Identify Subscription-Focused readers before they churn. Trigger targeted upsell at the right moment. | +15–25% subscription conversion rate vs non-personalised baseline | Braintree + Sailthru + Zephr
Ad Revenue | Serve advertisers verified high-intent segments commanding premium CPMs. | +20–40% CPM uplift on segmented vs run-of-site inventory | GA4 + Trackonomics
Newsletter Engagement | Personalise newsletter content per persona — each reader receives articles matching their proven content affinity. | +30–50% CTR improvement on segmented newsletters | Sailthru + GA4
Churn Reduction | Identify Low Engager and dormant users early, trigger re-engagement before they leave. | -20% annual churn rate on identified at-risk segments | Zephr + GA4 recency

NYPost Validation
This platform is directly inspired by the New York Post Data Labs initiative which segmented 66 million users across 8 source systems using Bisecting K-Means, discovering 9 personas. This blueprint extends that foundation by adding a multi-algorithm evaluation framework so your product is not locked to a single clustering approach and can optimise cluster quality for each client's unique data profile.

Role Legend
PK = Primary Key  |  FK = Foreign Key  |  ML Feature = direct input to clustering algorithm  |  Derived = computed from other fields  |  Metadata = stored for reference, not in ML matrix

Field Name | Data Type | Role | Description
user_id | UUID | PK | Universal unique identifier. Issued by Zephr at registration. The single key that ties all 8 sources together.
email | VARCHAR(255) | FK | User email. Join key to Sailthru. Unique, not null, stored lowercase.
hashed_email | VARCHAR(64) | FK | SHA-256 hash of email. Join key to Transunion for privacy-safe demographic enrichment.
registration_date | TIMESTAMP | Metadata | Timestamp of first account creation. Immutable. Used to derive account_age_days.
account_age_days | INTEGER | ML Feature | DERIVED: days since registration_date. Long tenure strongly correlates with Loyalist persona.
is_new_user | BOOLEAN | ML Feature | DERIVED: TRUE if account_age_days < 30. New users excluded from clustering run.
first_name | VARCHAR(100) | Metadata | Registration first name. Newsletter personalisation only — not in ML features.
last_name | VARCHAR(100) | Metadata | Registration last name. PII — masked in analytics environments.
address_state | VARCHAR(2) | Metadata | US state from registration. Geographic reporting and regional ad targeting.
address_zip | VARCHAR(10) | Metadata | ZIP code. Hyperlocal content targeting and home delivery eligibility.
subscription_entitlements | VARCHAR(50) | ML Feature | Active plan from Zephr entitlement engine. Cross-validated against Braintree.
last_login | TIMESTAMP | ML Feature | Most recent login. Recency signal. Dormant registered users identified here first.
is_registered | BOOLEAN | Metadata | Always TRUE in this table. Filter flag distinguishing registered vs anonymous GA4 users.

Field Name | Data Type | Role | Description
event_id | UUID | PK | Unique event identifier generated at ingestion.
user_pseudo_id | VARCHAR(64) | FK | GA4 anonymous cookie ID. Resolved to user_id via bridge table when user logs in.
user_id | UUID | FK | Resolved universal identifier. NULL for users who have never logged in.
event_date | DATE | Metadata | Event date YYYYMMDD (GA4 BigQuery format). Used for active_days and days_since_last_visit.
event_name | VARCHAR(50) | Metadata | GA4 event type: page_view, session_start, scroll, click. Pipeline filters to page_view.
session_id | VARCHAR(128) | Metadata | Session identifier. Groups events for bounce rate and pages-per-session aggregation.
device_category | ENUM | ML Feature | desktop / mobile / tablet. Aggregated to mobile_ratio and desktop_ratio features.
page_category | ENUM | ML Feature | sports, entertainment, celebrity, business, lifestyle, world_news, opinion, shopping, us_news, page_six. Produces ratio_* features.
page_path | VARCHAR(255) | Metadata | Full URL path. Used to assign page_category when not pre-tagged by CMS.
session_duration_sec | INTEGER | ML Feature | Session length in seconds. Aggregated to avg_session_duration.
is_bounce | BOOLEAN | ML Feature | Single page view under 10 seconds. Aggregated to bounce_rate. Primary Low Engager signal.
country | VARCHAR(50) | Metadata | GA4 geo country. Filter to target market.
state | VARCHAR(2) | Metadata | GA4 geo state. Cross-validated against Zephr address_state.

Field Name | Data Type | Role | Description
subscription_id | UUID | PK | Unique Braintree subscription identifier.
customer_id | UUID | FK | = user_id. Set programmatically at subscription creation from Zephr registration flow.
plan_id | ENUM | ML Feature | sports_plus ($9.99), home_delivery ($14.99), digital_all_access ($19.99). One-hot encoded.
status | ENUM | ML Feature | Active / Canceled / Past Due. Active = has_subscription TRUE. Past Due = churn risk signal.
amount | DECIMAL(8,2) | ML Feature | Monthly billing amount USD. Higher amounts correlate with Loyalist and Subscription-Focused.
billing_day_of_month | SMALLINT | Metadata | Billing day. Payment timing analysis only.
created_at | TIMESTAMP | Metadata | Subscription creation date. Used to compute subscription tenure.
paid_through_date | DATE | ML Feature | Date paid through. Days until renewal = churn proximity signal.
number_of_billing_cycles | INTEGER | ML Feature | Successful billing cycles. High count = long-term committed subscriber. Loyalist signal.
payment_method | ENUM | Metadata | credit_card or paypal. Payment analytics only.

Field Name | Data Type | Role | Description
sailthru_id | UUID | PK | Sailthru internal ID. Not used as join key.
user_id | UUID | FK | Resolved from email match to Zephr. Universal identifier for feature store joins.
email | VARCHAR(255) | FK | Primary join key to zephr_users. Exact match required (lowercase, trimmed).
subscribed_newsletters | TEXT | ML Feature | Pipe-delimited newsletter IDs. Exploded into 10 binary nl_* feature flags.
newsletter_count | SMALLINT | ML Feature | Active newsletter subscriptions. Subscription-Focused persona subscribes to 4–5 simultaneously.
open_rate | FLOAT | ML Feature | Emails opened / sent (0.0–1.0). Loyalists typically exceed 0.40.
click_through_rate | FLOAT | ML Feature | Opened emails with link click (0.0–1.0). Key differentiator for High Value Shoppers.
total_emails_sent | INTEGER | Metadata | Delivered email count. Denominator for open_rate.
total_opens | INTEGER | Metadata | Raw open count. Numerator for open_rate.
total_clicks | INTEGER | Metadata | Raw click count. Numerator for click_through_rate.
last_open_date | DATE | ML Feature | Most recent email open. Email recency signal.
engagement_tier | ENUM | ML Feature | low / medium / high based on open_rate thresholds.
email_engagement_score | SMALLINT | Derived | DERIVED: 0=low, 1=medium, 2=high. Direct ML matrix input.

Field Name | Data Type | Role | Description
subscriber_id | UUID | PK | Pushly internal subscriber ID.
external_id | UUID | FK | = user_id. Set at push opt-in time. Direct FK to zephr_users.
opted_in | BOOLEAN | ML Feature | Push opt-in status. Encoded as push_opted_in. Opt-in itself is a meaningful engagement signal.
opt_in_date | DATE | Metadata | Opt-in date. Push tenure analysis.
platform | ENUM | ML Feature | web_desktop / web_mobile / ios / android. One-hot encoded to push_platform_* features.
notifications_sent | INTEGER | Metadata | Total delivered. Denominator for click_rate.
notifications_clicked | INTEGER | Metadata | Total clicks. Numerator for click_rate.
click_rate | FLOAT | ML Feature | Clicked / sent. High rates characteristic of Sports Focused users on breaking sports alerts.
last_clicked_at | TIMESTAMP | ML Feature | Most recent click. Push recency signal.
preferred_category | ENUM | ML Feature | Category of most-clicked notifications. Secondary content affinity signal.
is_active | BOOLEAN | ML Feature | Push subscription active (not revoked). Encoded as push_is_active.

Field Name | Data Type | Role | Description
openweb_user_id | UUID | PK | Openweb internal ID.
user_id | UUID | FK | Direct FK via SSO token. Most reliable join — no resolution step required.
email | VARCHAR(255) | FK | Secondary join key for data quality validation.
total_comments | INTEGER | ML Feature | Total comments posted. Defining Social Engagers feature.
total_likes_given | INTEGER | ML Feature | Total likes given. Community participation signal.
total_shares | INTEGER | ML Feature | Total article shares. Strong Celebrity & Entertainment signal.
articles_commented_on | INTEGER | ML Feature | Unique articles with user comments. Breadth of engagement.
avg_comment_length | INTEGER | Metadata | Average comment character length. Long-form = Opinion readers.
top_commented_category | ENUM | ML Feature | Content category with most comments. Cross-validates GA4 content affinity.
social_engagement_score | INTEGER | Derived | DERIVED: (comments×3)+(likes×1)+(shares×2). Composite community activity score.
is_verified | BOOLEAN | Metadata | Verified badge. Not in ML features.
toxicity_flag | BOOLEAN | Metadata | Comment toxicity flag. Moderation only.
last_activity | TIMESTAMP | ML Feature | Most recent social action. Social recency.

Field Name | Data Type | Role | Description
click_id | UUID | PK | Unique click event identifier.
user_id | UUID | FK | user_id passed as URL parameter. NULL for anonymous affiliate clicks.
click_timestamp | TIMESTAMP | Metadata | Exact click time. Temporal commerce behaviour analysis.
advertiser | VARCHAR(100) | ML Feature | Advertiser name. Aggregated to unique_advertisers_clicked.
product_category | ENUM | ML Feature | electronics, fashion, home, beauty, sports_gear, books, travel. Commerce intent signal.
transaction_amount | DECIMAL(10,2) | ML Feature | Purchase value if did_transact=TRUE, else 0. Aggregated to total_revenue_generated.
commission | DECIMAL(8,2) | ML Feature | Publisher commission. Aggregated to total_commission — direct platform revenue per user.
did_transact | BOOLEAN | ML Feature | Click resulted in purchase. Aggregated to conversion_rate. Defines High Value Shoppers.
source_article_category | VARCHAR(50) | Metadata | Originating article category. Which editorial content drives commerce.
device | ENUM | Metadata | desktop / mobile / tablet. Cross-validates device preference with GA4.

Field Name | Data Type | Role | Description
transunion_id | UUID | PK | Transunion enrichment record ID.
hashed_email | VARCHAR(64) | FK | SHA-256 hash. Join key to zephr_users.hashed_email.
user_id | UUID | FK | Resolved from hashed_email join to Zephr.
age_range | ENUM | ML Feature | 18-24, 25-34, 35-44, 45-54, 55-64, 65+. Sports Focused skews 18–34.
age_score | SMALLINT | Derived | DERIVED: ordinal 1–6. Numeric K-Means input.
gender | ENUM | ML Feature | M / F / Non-binary / Unknown. Persona demographic profiling.
income_range | ENUM | ML Feature | <30k through 150k+. High income correlates with High Value Shoppers.
income_score | SMALLINT | Derived | DERIVED: ordinal 1–6. Numeric K-Means input.
home_ownership | ENUM | ML Feature | owner / renter / unknown. Home delivery subscription propensity.
education | ENUM | ML Feature | high_school, some_college, bachelors, graduate. Correlates with Opinion readers.
state | VARCHAR(2) | Metadata | State from Transunion. Cross-validated with Zephr address_state.
has_children | BOOLEAN | ML Feature | Household includes children. Home delivery and family lifestyle signal.
match_confidence | FLOAT | Metadata | Match confidence 0.65–1.0. Records below 0.70 excluded from demographic features.

Null Handling
Users absent from a source receive 0 for numeric features — never dropped. Users with total_sessions ≤ 4 AND no other source data are excluded and assigned 'new_user' until next run.

Field Name | Data Type | Role | Description
total_sessions | INTEGER | ML Feature | Total sessions in observation period.
total_pageviews | INTEGER | ML Feature | Total page views. Loyalists: 500+ per year.
active_days | INTEGER | ML Feature | Distinct days with at least one session.
avg_session_duration | FLOAT | ML Feature | Average seconds per session.
avg_pages_per_session | FLOAT | ML Feature | Average pages per session. High = content discovery behaviour.
bounce_rate | FLOAT | ML Feature | Single-page sessions under 10s / total sessions. Primary Low Engager signal.
mobile_ratio | FLOAT | ML Feature | Mobile sessions / total. Loyalists skew desktop; casual readers skew mobile.
desktop_ratio | FLOAT | ML Feature | Desktop sessions / total.
pageviews_per_session | FLOAT | Derived | total_pageviews / total_sessions. Normalised reading depth.
days_since_last_visit | INTEGER | ML Feature | Days from last session to reference date. Recency / churn signal.
account_age_days | INTEGER | ML Feature | Days since Zephr registration. Long tenure = Loyalist.

Field Name | Data Type | Role | Description
ratio_sports | FLOAT | ML Feature | Sports pageviews / total. Primary Sports Focused differentiator.
ratio_entertainment | FLOAT | ML Feature | Entertainment proportion. Combined with ratio_celebrity for Celebrity cluster.
ratio_celebrity | FLOAT | ML Feature | Celebrity/Page Six proportion. Highest in Celebrity & Entertainment.
ratio_shopping | FLOAT | ML Feature | Shopping content proportion. Correlated with Trackonomics commerce features.
ratio_opinion | FLOAT | ML Feature | Opinion content proportion. Long-form politically engaged readers.
ratio_world_news | FLOAT | ML Feature | World news proportion. News-first casual readers.
ratio_business | FLOAT | ML Feature | Business content proportion. Correlated with higher income_score.
ratio_lifestyle | FLOAT | ML Feature | Lifestyle content (health, wellness, food).

Field Name | Data Type | Role | Description
has_subscription | BOOLEAN | ML Feature | Active paid subscription. One of the strongest single cluster separators.
subscription_plan | VARCHAR(50) | Metadata | Plan name or none.
subscription_amount | DECIMAL | ML Feature | Monthly amount USD. Higher = higher commitment tier.
total_billing_cycles | INTEGER | ML Feature | Successful billing cycles. Long history = primary Loyalist tenure feature.

Field Name | Data Type | Role | Description
newsletter_count | SMALLINT | ML Feature | Active newsletter subscriptions. Primary Subscription-Focused differentiator.
open_rate | FLOAT | ML Feature | Email open rate 0.0–1.0.
click_through_rate | FLOAT | ML Feature | Email link click rate 0.0–1.0.
email_engagement_score | SMALLINT | ML Feature | Ordinal 0/1/2 low/medium/high.
nl_sports_alerts | BOOLEAN | ML Feature | Subscribed to Sports Alerts newsletter.
nl_morning_report | BOOLEAN | ML Feature | Subscribed to Morning Report. Habitual daily reader.
nl_page_six_daily | BOOLEAN | ML Feature | Subscribed to Page Six Daily. Celebrity signal.
nl_celebrity_news | BOOLEAN | ML Feature | Subscribed to Celebrity News.
nl_evening_update | BOOLEAN | ML Feature | Subscribed to Evening Update.
nl_post_opinion | BOOLEAN | ML Feature | Subscribed to Post Opinion. Opinion reader signal.

Field Name | Data Type | Role | Description
total_comments | INTEGER | ML Feature | Total comments posted.
total_likes_given | INTEGER | ML Feature | Total likes given.
total_shares | INTEGER | ML Feature | Total article shares.
social_engagement_score | INTEGER | Derived | (comments×3)+(likes×1)+(shares×2). Composite community score.

Field Name | Data Type | Role | Description
total_affiliate_clicks | INTEGER | ML Feature | Total affiliate link clicks. Commerce engagement volume.
total_transactions | INTEGER | ML Feature | Clicks resulting in purchase.
total_revenue_generated | DECIMAL | ML Feature | Total transaction value USD.
conversion_rate | FLOAT | ML Feature | Purchases / clicks. Defining High Value Shoppers feature.
avg_transaction_value | DECIMAL | ML Feature | Average purchase value per transaction.
unique_advertisers_clicked | INTEGER | ML Feature | Breadth of commerce interest.

Field Name | Data Type | Role | Description
age_score | SMALLINT | ML Feature | Ordinal 1–6 (18–24 through 65+).
income_score | SMALLINT | ML Feature | Ordinal 1–6 (<30k through 150k+).
has_children | BOOLEAN | ML Feature | Household includes children.

Field Name | Data Type | Role | Description
persona_label | VARCHAR(50) | Derived | Human-readable persona name: loyalist, sports_focused, high_value_shopper, social_engager, subscription_focused, occasional_buyer, celebrity_entertainment, casual_reader, low_engager.
cluster_id | SMALLINT | Derived | Numeric cluster assignment. Used for programmatic targeting.
algorithm_used | VARCHAR(50) | Derived | Which algorithm produced this assignment: kmeans, gmm, hdbscan, ensemble. Tracked per run for model governance.
cluster_score | FLOAT | Derived | Confidence / distance score. Lower distance = more prototypical cluster member. Used for confidence-based targeting.
last_updated | TIMESTAMP | Metadata | Timestamp of last pipeline run. Used to detect stale assignments.

Design Principle
The NYPost project used Bisecting K-Means. This blueprint treats algorithm selection as a tunable, client-specific decision. Different publishers have different data densities, different proportions of engaged vs dormant users, and different cluster granularity requirements. A single algorithm locks you into assumptions that may not hold for every client. The recommended approach is an evaluation pipeline that tests multiple algorithms and selects the best-performing one per client deployment.

Algorithm | Mechanism | Strengths | Weaknesses | Use Case
Bisecting K-Means | Divide largest cluster recursively until K clusters reached. | Fast and scalable to 100M+ users. Produces compact, well-separated clusters. Deterministic (reproducible runs). | Assumes spherical clusters. Sensitive to outliers. Requires K to be specified in advance. Struggles if cluster sizes are very unequal (e.g. 50% Low Engagers). | Best for: large publishers (10M+ users) needing fast, reproducible weekly runs.
Standard K-Means | Iteratively assign points to nearest centroid until convergence. | Well-understood, widely supported. Good cluster interpretability. Works well when cluster sizes are roughly equal. | Same spherical cluster assumption as Bisecting variant. Can converge to local minima — run multiple times with different seeds. | Best for: mid-size publishers (1M–10M) with reasonably balanced persona distributions.
Gaussian Mixture Model (GMM) | Probabilistic model — assigns soft membership probabilities to each cluster. | Handles elliptical clusters (not just spherical). Produces confidence scores natively (posterior probabilities). Better captures overlapping personas (e.g. a user who is 70% Sports Focused, 30% Loyalist). | Slower than K-Means. More sensitive to initialisation. Requires careful regularisation to avoid degenerate solutions. | Best for: publishers wanting soft persona scores for nuanced targeting, not hard assignments.
HDBSCAN | Density-based hierarchical clustering. Finds clusters as dense regions separated by sparse regions. | Does NOT require K to be specified — discovers the natural number of clusters. Handles non-spherical clusters. Automatically identifies outliers as noise. | Non-deterministic. Slower on very large datasets. Outlier users (Low Engagers) may be classified as noise rather than a cluster. | Best for: initial exploration on a new client's data to discover natural K before running K-Means.
Ensemble (Consensus Clustering) | Run K-Means, GMM, and HDBSCAN independently. Assign final persona by majority vote. | Most robust. Reduces variance from any single algorithm's weaknesses. Confidence score = proportion of algorithms agreeing. | Computationally expensive (3x cost of single algorithm). Pipeline complexity increases. | Best for: premium client deployments where accuracy > speed, or when algorithms produce conflicting cluster counts.

Implementation
from sklearn.cluster import BisectingKMeans
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(feature_matrix)

inertias = []
for k in range(5, 21):
    model = BisectingKMeans(n_clusters=k, random_state=42, n_init=3)
    model.fit(X_scaled)
    inertias.append({'k': k, 'inertia': model.inertia_})

# Plot inertia vs K — look for elbow point
# Typical finding: elbow at K=8 to K=12 for general publishers

Implementation
from sklearn.metrics import silhouette_score

silhouette_scores = []
for k in range(5, 16):
    labels = BisectingKMeans(n_clusters=k, random_state=42).fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels, sample_size=50000)  # sample for speed
    silhouette_scores.append({'k': k, 'silhouette': score})

best_k = max(silhouette_scores, key=lambda x: x['silhouette'])['k']

Publisher Type | Recommended K | Rationale
Small publisher (< 1M users) | K = 5–7 | Fewer users means less data per cluster. Over-segmenting creates clusters too small to activate meaningfully.
Mid publisher (1M–10M users) | K = 7–9 | Standard range. Matches NYPost's 9-cluster finding for a general-interest publisher.
Large publisher (10M–50M users) | K = 9–12 | Larger user base supports finer-grained segmentation. Sub-cluster Low Engagers (32.9M at NYPost) into 2–3 groups.
Niche/vertical publisher | K = 4–6 | Sports-only or finance-only publishers have less content diversity. Fewer meaningful behavioural archetypes exist.
Multi-brand publisher | K = 12–15 | Publisher operates multiple properties (e.g. news + sports + entertainment). Cross-property behaviours add cluster complexity.

Stage | Description | Output | Tooling
Stage 1: Discovery
(Week 1) | Run HDBSCAN on the client's feature store. Do not specify K. Let the algorithm reveal the natural number of dense behavioural groups in this specific dataset. This gives you a data-driven K estimate before running K-Means. | HDBSCAN output: natural K = 7 (for example). Cluster size distribution. Outlier / noise user rate. | HDBSCAN on full dataset
Stage 2: Evaluation
(Week 1–2) | Run Bisecting K-Means and GMM across K = natural_K ± 3 (e.g. K=5 to K=10 if HDBSCAN found K=7). Score each with silhouette, inertia elbow, and Davies-Bouldin index. Compute business interpretability score for top 3 candidates. | Silhouette scores, inertia curves, Davies-Bouldin index, cluster size distributions for each K. | BisectingKMeans + GaussianMixture in parallel
Stage 3: Selection
(Week 2) | Select the algorithm + K combination with highest combined score across: silhouette score (40% weight), business interpretability (40% weight), cluster stability across 3 runs (20% weight). Document rationale in MLflow. | Final algorithm selection: e.g. BisectingKMeans K=9 with silhouette=0.41. Or GMM K=8 if soft scores needed. | MLflow experiment tracking
Stage 4: Production
(Week 3+) | Run selected algorithm weekly on new data. Monitor silhouette score and persona stability. Re-run Stage 2 evaluation if silhouette drops > 0.05 or stability drops below 80% week-over-week for 3 consecutive weeks. | Weekly silhouette, stability, coverage reports. Automated re-evaluation trigger. | Airflow DAG + Grafana monitoring

Persona | Approx. Size | Defining Characteristics | Primary Activation
loyalist | 738K | High sessions, pageviews, desktop, subscription tenure. Core revenue base. | Renewal campaigns, premium content, loyalty rewards
subscription_focused | 1.8M | High newsletter subscriptions, registration completeness, Sports+ uptake. | Subscription conversion, tier upsell
high_value_shopper | 413K | Highest commerce clicks, conversion rate, avg transaction value. | Premium affiliate placements, retail campaigns
sports_focused | 6.6M | Highest sports ratio, Sports+ subscriptions, high push click rate. | Sports+ upsell, sports brand advertising
social_engager | 5M | Highest comments, likes, shares. Community-first behaviour. | Community features, UGC campaigns
occasional_buyer | 1.9M | Moderate commerce, highest shopping content views. | Retargeting, commerce content promotion
celebrity_entertainment | 6.3M | Highest celebrity/entertainment ratio, high social engagement. | Entertainment brand advertising, Page Six campaigns
casual_reader | 10M | Broad content, moderate sessions, low subscription intent. | Newsletter acquisition, recommendation engine
low_engager | 32.9M | Lowest engagement across all signals. No strong content preference. | Re-engagement flows, win-back sequences

Score | Type | Derivation
subscription_propensity_score | FLOAT 0.0–1.0 | Likelihood of converting to paid subscription within 90 days. Derived from cluster distance to subscription_focused centroid + has_subscription + newsletter_count.
churn_propensity_score | FLOAT 0.0–1.0 | Likelihood of cancellation within 30 days. Derived from days_since_last_visit trend, bounce_rate trajectory, distance from loyalist centroid.
commerce_propensity_score | FLOAT 0.0–1.0 | Likelihood of affiliate click resulting in transaction. Derived from distance to high_value_shopper centroid + historical conversion_rate.
soft_persona_scores (GMM only) | FLOAT[] — 9 values summing to 1.0 | Posterior probability of membership in each cluster. E.g. [0.65 loyalist, 0.25 subscription_focused, 0.10 casual_reader]. Enables nuanced targeting for borderline users.

KPI | Definition | Target | Cadence | Alert Rule
Silhouette Score | How well-separated the clusters are. Higher = better defined personas. | > 0.35 overall
> 0.25 per cluster | Weekly, each run | Alert if drops > 0.05 vs prior week
Persona Stability | % of users with same persona as prior week. Low stability = noisy features or data quality issue. | > 85% week-over-week | Weekly | Re-run Stage 2 evaluation if < 80% for 3 consecutive weeks
Algorithm Consistency | % agreement between Bisecting K-Means and GMM on persona assignments (used as ensemble validation). | > 75% agreement on non-Low-Engager users | Weekly | Trigger ensemble mode if < 70% agreement
Feature Coverage | % of users with data from each source. Drops indicate pipeline failures. | > 95% GA4
> 65% Transunion | Daily | Page-duty alert if GA4 < 90%
Cluster Size Balance | No cluster > 60% or < 0.5% of users. Extreme imbalance suggests K is wrong. | Largest cluster < 60% of total | Weekly | Re-evaluate K if Low Engager > 60%

KPI | Definition | Target | Cadence | Alert Rule
Newsletter CTR by Persona | Click-through rate on personalised newsletters vs control group (non-segmented sends). | + 30–50% CTR lift vs control | Per send / weekly | Flag if lift < 15% for 3 consecutive weeks
Subscription Conversion Rate | % of Subscription-Focused + Loyalist users converting to paid plan within 90 days of persona assignment. | + 15–25% vs non-segmented baseline | Monthly | Alert if conversion rate drops > 5% vs prior month
Ad CPM by Segment | Average CPM for programmatic ads served to each persona vs run-of-site. | + 20–40% premium for Sports Focused and High Value Shoppers | Monthly | Report to revenue team monthly
Revenue Per User (RPU) | Total revenue (subscription + affiliate + ad) per active user per persona cohort. | High Value Shoppers RPU > 5x Low Engager RPU | Monthly | Track cohort RPU trend over 6 months
Churn Rate by Persona | Monthly subscriber cancellation rate per persona segment. | Overall churn - 20% YoY after activation | Monthly | Alert if any persona churn > 5% in a month
Re-engagement Rate | % of Low Engagers who increase sessions by > 50% within 30 days of targeted re-engagement campaign. | 5–10% re-engagement rate | Per campaign | Benchmark each campaign vs prior
Persona Coverage | % of total registered users with an active ML-assigned persona (vs excluded new users). | ≥ 80% of registered users | Weekly | Alert if coverage drops below 75%
Commerce Conversion Rate | % of affiliate clicks converting to purchase for segmented High Value Shoppers vs non-segmented baseline. | + 25% conversion lift vs non-segmented | Monthly | Monthly affiliate performance report

NYPost Benchmark
NYPost Data Labs processed 66 million total users. Their feature store was built from event-level data across 8 source systems. This blueprint uses that as the large-scale benchmark and scales down to smaller deployments.

Table | Volume | Notes | Refresh Pattern
zephr_users | 1M rows | 1 row per user | Registration write + incremental updates
ga4_events | 200M–500M rows | 200–500 events per user per year | Daily BigQuery export, partitioned by date
sailthru_newsletter | 1M rows | 1 aggregate row per user | Weekly refresh or daily delta
braintree_subscriptions | 50K–150K rows | 5–15% are paying subscribers | Event-driven on state change
pushly_subscribers | 300K–400K rows | 30–40% opt into push | Daily delta sync
openweb_engagement | 200K–250K rows | 20–25% engage socially | Daily delta sync
trackonomics_clicks | 5M–15M rows | Multiple clicks per commerce user | Daily SFTP export
transunion_demographics | 700K rows | 70% hashed email match rate | Monthly batch refresh
feature_store | 1M rows | 1 row per registered user | Weekly full rebuild

Tier | Infrastructure | Cadence | Stack
Small
< 1M users | Single machine or small cloud instance. Feature store fits in RAM. K-Means runs in < 30 min. All 5 algorithms evaluatable in < 2 hours. | Monthly clustering cadence acceptable. Weekly if data changes rapidly. | Pandas + scikit-learn. No Spark needed.
Mid
1M–10M users | Cloud VM (32–64GB RAM). Dask for feature engineering. Algorithm evaluation in 2–4 hours. Bisecting K-Means production run in < 1 hour. | Weekly clustering. Daily feature refresh (no re-clustering daily). | Dask + scikit-learn. BigQuery or Redshift for storage.
Large
10M–50M users | Spark cluster (5–10 nodes, 32GB RAM each). Feature engineering in < 2 hours. Full algorithm evaluation in 4–8 hours. Production K-Means run in 2–3 hours. | Weekly clustering. Daily feature refresh. Consider sampling for HDBSCAN discovery phase. | PySpark + Spark MLlib. BigQuery/Redshift. Airflow orchestration.
NYPost Scale
50M–100M users | 20-node Spark cluster. Feature engineering in 3–4 hours. Bisecting K-Means production run in 2–3 hours. HDBSCAN only on 10% sample for discovery. | Weekly clustering. Daily feature updates. HDBSCAN discovery monthly (expensive at this scale). | PySpark + Spark MLlib + BigQuery. Full Airflow DAG with validation gates.

Component | Description
Data Warehouse | Google BigQuery (preferred) or Amazon Redshift. GA4 BigQuery export is native for Google stack. All feature store tables stored here.
Feature Engineering | PySpark for large publishers (> 5M users). Pandas + Dask for small/mid. Runs weekly as Step 3 in Airflow DAG.
Algorithm Evaluation | Scikit-learn: BisectingKMeans, GaussianMixture, silhouette_score, davies_bouldin_score. hdbscan library for discovery phase. Spark MLlib for K-Means at > 10M users.
Model Registry | MLflow: tracks every run — algorithm used, K selected, silhouette score, persona distribution, feature importance, scaler object. Enables full rollback.
Orchestration | Apache Airflow DAG (weekly trigger). 8 sequential steps with validation gates. MWAA (AWS) or Cloud Composer (GCP) for managed deployment.
Persona Serving API | FastAPI microservice: GET /persona/{user_id} returns persona_label, cluster_id, 3 propensity scores, soft_scores (GMM). Reads from Redis cache. < 10ms p99.
Cache Layer | Redis: stores persona_label + propensity scores per user. TTL = 7 days, refreshed by weekly pipeline. Sub-millisecond reads for ad server and CMS integrations.
Monitoring | Grafana dashboard: pipeline runtime, silhouette score trend, persona stability, feature coverage, business KPIs. PagerDuty alerts on critical metric drops.

Step | Description | Trigger / Notes
Step 1: Source Ingestion | Pull delta data from all 8 sources. Validate row counts and schema against expected ranges. Fail pipeline if any source deviates > 20% from prior week. | Daily or weekly trigger depending on source
Step 2: Identity Stitching | Resolve all source IDs to user_id via bridge table (GA4), email match (Sailthru), and hashed email match (Transunion). Log unresolved rates. | Runs after Step 1
Step 3: Feature Engineering | Aggregate GA4 events to user level. Compute ratio_*, bounce_rate, avg_session_duration, mobile_ratio. Join all sources on user_id. Fill nulls with 0. | Runs after Step 2
Step 4: Feature Validation | Check feature distributions for drift vs prior week. Flag if > 20% mean shift on any feature. Abort if > 3 features drift simultaneously — data quality issue. | Runs after Step 3. Gate before Step 5.
Step 5: StandardScaler Fit | Fit StandardScaler on ML feature matrix. Save scaler to MLflow. Apply log1p transformation to heavily skewed features (total_pageviews, total_affiliate_clicks). | Runs after Step 4
Step 6: Algorithm Evaluation | NEW STEP vs NYPost: Run Bisecting K-Means, GMM, and silhouette scoring across K=5 to K=15. Select best algorithm+K by composite score. If same algorithm+K as prior week, skip to Step 7. | Weekly. May be skipped if no significant data change detected.
Step 7: Production Clustering | Run selected algorithm at chosen K on full scaled feature matrix. Compute silhouette score and per-cluster stats. If silhouette < 0.30, alert team and use prior week's assignments. | Core clustering step. Fails safe to prior week.
Step 8: Write-Back | Write persona_label, cluster_id, algorithm_used, cluster_score, last_updated to feature_store. Log persona distribution to MLflow for trend tracking. | Runs after Step 7
Step 9: Cache Refresh + Notify | Push updated records to Redis. Notify downstream systems (Sailthru, ad server, CMS) via webhook that persona refresh is complete. | Final step. Triggers downstream activation.

Architecture Decision
Clustering is BATCH (weekly). Persona serving is REAL-TIME (Redis cache, < 10ms). There is no live ML model called at request time. This is a deliberate decision that balances accuracy, cost, and scalability.

Reason | Explanation
Requires full dataset | K-Means and GMM compute centroids / covariances across all users simultaneously. Single-user real-time clustering is mathematically meaningless.
Behaviour accumulates slowly | Content affinity ratios stabilise only after 10+ sessions. Real-time updates on every page view add noise, not signal.
Business cadence | Newsletters go out weekly. Ad campaigns planned weekly. Upsell sequences run 30–90 days. Weekly persona refresh is sufficient.
Algorithm evaluation | Running HDBSCAN + K-Means + GMM evaluation on 66M users takes 4–8 hours. This can only be batch.
Cost | Weekly Spark clustering at scale costs $200–400/run. Daily = 7x cost with minimal accuracy improvement.

Process | Use Case | Latency
Persona serving API | GET /persona/{user_id} called by newsletter, ad server, CMS at request time. | < 10ms from Redis cache. SLA: 99.9% uptime.
Homepage personalisation | CMS calls persona API on page load to reorder content modules per persona. | < 20ms. Served from Redis.
Ad targeting | Ad server retrieves persona_label per user on each ad impression request. | < 10ms. Sub-millisecond for pre-fetched sessions.
Subscription upsell | subscription_propensity_score retrieved on login / checkout to trigger upsell banner. | < 10ms. Served from Redis.
New user cold-start | Rule-based content serving for users with < 5 sessions (no ML persona yet). | Instantaneous. CMS rule engine, no API call needed.

Sessions | Strategy | Experience | Mechanism
0–1 sessions | new_user persona assigned immediately on registration. | Serve default homepage. No personalisation. | Zephr registration event
2–4 sessions | Rule-based mini-segmentation: if > 50% sports views → sports_cold_start. if > 50% celebrity views → celebrity_cold_start. | Serve content matching dominant category. Still rule-based. | CMS rules engine
5–9 sessions | User included in next weekly batch run. Gets first ML-assigned persona within 3–10 days of registration. | Full ML persona. All propensity scores computed. | Weekly Airflow DAG
10+ sessions | Stable ML persona. Propensity scores reliable. Include in all activation campaigns. | Full personalisation across newsletter, ads, homepage, upsell. | All activation channels

Role | Responsibilities | Frequency | Tools
Data Engineers | Build and maintain Airflow DAGs, source connectors, feature engineering pipeline. Own pipeline reliability, data quality monitoring, and source system integrations. Set up GA4 BigQuery export, Sailthru API, Transunion batch job. | Daily — pipeline alerts, data quality checks, integration maintenance. | Python, Spark/Dask, Airflow, BigQuery, dbt
Data Scientists / ML Engineers | Own the clustering model and algorithm evaluation framework. Tune K, evaluate silhouette scores, run HDBSCAN discovery, name personas. Own MLflow model registry and retraining triggers. Add new features to improve cluster quality. | Weekly — review clustering outputs, evaluate model drift, run experiments. | Python, scikit-learn, hdbscan, MLflow, Spark MLlib, Jupyter
Backend / API Engineers | Build and maintain FastAPI persona serving microservice, Redis cache, and downstream integration webhooks (Sailthru, ad server, CMS). Ensure < 10ms SLA. Build algorithm_used and soft_scores fields into API response. | Sprint-based — integrations, API uptime, cache management. | FastAPI, Redis, Docker, Kubernetes
Analytics / BI Engineers | Build Grafana dashboards for cluster stability, persona distribution, and business KPIs. Build self-serve reporting for business stakeholders. Own A/B test measurement for segmented vs control campaigns. | Weekly — dashboards, ad-hoc analyses, campaign lift measurement. | SQL, Grafana, Looker/Tableau, Python

Role | Responsibilities | Frequency | Tools
Newsletter / Email Team | Use persona labels to segment Sailthru send lists. Configure which content template each persona receives. Review CTR reports. Request persona-specific newsletter products. | Daily — send scheduling, performance review, list segmentation. | Sailthru UI, reporting dashboard
Advertising / Revenue Team | Package persona segments as premium audience inventory. Sports Focused = sports brand CPM premium. High Value Shoppers = retail premium. Build media kit with persona reach statistics. | Weekly — campaign planning, advertiser reporting, rate card management. | Ad server UI (GAM/Xandr), internal dashboard
Subscription / Growth Team | Use subscription_propensity_score to trigger upsell banners and email sequences. Monitor conversion rate by persona. Design win-back flows for cancelled Subscription-Focused users. | Weekly — campaign setup, conversion funnel review, churn analysis. | Zephr UI, Braintree dashboard, email platform
Editorial / Content Team | Use content affinity ratios to understand what drives which segments. Inform commissioning — Sports Focused is 6.6M users, justifying investment in sports coverage. Configure homepage personalisation rules. | Monthly — content strategy reviews, persona briefings. | CMS, analytics dashboard
Product Managers | Own platform roadmap. Prioritise new data sources, new personas, new activation channels. Define new KPIs. Liaise between technical and business teams. | Weekly — roadmap, stakeholder alignment, KPI reviews. | JIRA, Confluence, dashboard

Type | Experience | Scale
Registered readers | Receive personalised newsletters, reordered homepage, calibrated subscription offers. Never interact with platform directly — experience the output. | 66M at NYPost scale. 500K–100M depending on publisher.
Anonymous visitors | Cannot be clustered — no user_id. Receive default content and run-of-site ads. Registration incentive: personalisation only activates after sign-up. | Typically 40–60% of total traffic.
Advertiser clients | Purchase premium audience segments. Sports Focused, High Value Shoppers delivered via ad server targeting. No direct platform interaction. | 100+ advertisers across sports, retail, lifestyle, finance.

Selling to Other Publishers
When deployed as a product to other publishing companies, each client gets an isolated deployment with their own data pipeline, feature store, and persona serving API. The algorithm evaluation framework runs fresh for each client — a sports vertical publisher may land at K=6 with K-Means while a general interest publisher lands at K=10 with GMM. The platform's admin dashboard shows each client's algorithm selection, silhouette scores, persona distribution, and business KPIs without exposing any other client's data.

Client Role | Description
Client Data Team | Connects source systems, monitors pipeline health, reviews persona and algorithm quality each week.
Client Business Team | Configures newsletter templates, ad targeting segments, and upsell flows per persona. Consumes persona API for campaigns.
Platform Support | Onboards new clients, handles integration issues, monitors cross-client infrastructure. Typically 1 data engineer + 1 ML engineer per 10 clients at launch.
Platform Product Team | Manages core product roadmap, shared algorithm evaluation framework improvements, and new feature additions that benefit all clients.
