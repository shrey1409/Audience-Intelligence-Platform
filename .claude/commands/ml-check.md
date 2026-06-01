---
description: Validate ML config integrity — 46 features, persona labels, propensity weights, cold start rules, feature store coverage
argument-hint: (no arguments)
allowed-tools: Read, Glob, Bash(python3:*)
---

<!-- CONTEXT BUDGET: ~50K tokens max. Load only files listed below. -->

You have .claude/CLAUDE.md context. You will read configs/base.yaml in full below.

## Step 1 — Load configs/base.yaml
Read `configs/base.yaml` in full. All checks below are derived from this file.

## Step 2 — Feature matrix count (must be exactly 46)
Extract `ml.features.matrix` list from base.yaml.
Count the items. If the count is not exactly 46, list:
- Which features are present (numbered)
- How many are present vs expected
- FAIL if not 46

Expected features (for reference — all must appear):
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

## Step 3 — log1p_features are a subset of the feature matrix
Extract `ml.features.log1p_features`. Verify each name in this list also appears in `ml.features.matrix`.
Expected: `total_sessions`, `total_pageviews`, `total_affiliate_clicks`, `total_comments`.
Any name in log1p_features that is NOT in the matrix is a FAIL.

## Step 4 — feature_store DDL coverage
If `sql/ddl/feature_store.sql` exists, read it.
Verify every feature in `ml.features.matrix` appears as a column name in the DDL.
Report missing columns.

If `sql/ddl/feature_store.sql` does not yet exist, note it as PENDING (Phase 2 deliverable).

## Step 5 — Propensity score weight sums
For each propensity type (`subscription`, `churn`, `commerce`) in `ml.propensity`:
Extract the `weights` dict and sum the values.
Each sum must equal exactly 1.00 (tolerance: ±0.001).

Show the breakdown:
```
subscription: 0.30 + 0.25 + 0.25 + 0.20 = 1.00 ✓
churn:        0.40 + 0.30 + 0.30 = 1.00 ✓
commerce:     0.35 + 0.30 + 0.35 = 1.00 ✓
```

If any weight references a feature name (the key before `_scaled`), verify that feature exists in `ml.features.matrix`.

## Step 6 — Persona labels count and names
Extract `personas.labels` list. Must contain exactly 9 labels.
Expected labels:
```
loyalist, subscription_focused, high_value_shopper, sports_focused,
social_engager, occasional_buyer, celebrity_entertainment, casual_reader, low_engager
```
Report any label that is missing or has an unexpected name.

## Step 7 — Persona naming rules coverage
Extract `personas.naming_rules`. Verify:
- There is exactly one rule with `top_feature: "default"` (catch-all)
- Every unique `label` in naming_rules appears in `personas.labels`
- Every `top_feature` and `supporting` feature name exists in `ml.features.matrix`
- Count rules: should cover all 9 persona labels (one rule per label)

## Step 8 — Cold start rules coverage
Extract `cold_start.rules`. Verify:
- There is exactly one rule with `condition: "default"` as the last priority
- Priority numbers are sequential starting from 1 with no gaps
- Any feature names referenced in conditions (ratio_sports, ratio_celebrity, etc.) exist in `ml.features.matrix`
- `min_sessions_for_ml` is defined (currently 5)

## Step 9 — Clustering config sanity
Extract `ml.clustering`. Verify:
- `k_min < k_max` (currently 5 < 15 ✓)
- `silhouette_threshold > 0` and `< 1`
- `stability_threshold > 0` and `< 1`
- `selection_weights` (silhouette + interpretability + stability) sum to 1.0
- `min_cluster_size_pct > 0` (protection against degenerate clusters)

## Step 10 — Check ML code files (if they exist)
If `ml/feature_store/` contains Python files, read them and verify:
- They import the feature list from config, not from a hardcoded list in code
- They use `settings.ml.features.matrix` or equivalent — not a local constant

If `ml/training/` contains Python files, read them and verify:
- Clustering k_min/k_max come from config, not hardcoded integers
- Silhouette threshold comes from config

## Step 11 — Report
```
═══════════════════════════════════════════════
ML Configuration Integrity Report
═══════════════════════════════════════════════

FEATURE MATRIX
  Count:    46/46 ✓
  log1p:    4 features, all in matrix ✓

FEATURE STORE DDL
  ✗ sql/ddl/feature_store.sql — not yet created (Phase 2 pending)

PROPENSITY WEIGHTS
  subscription: 0.30 + 0.25 + 0.25 + 0.20 = 1.00 ✓
  churn:        0.40 + 0.30 + 0.30 = 1.00 ✓
  commerce:     0.35 + 0.30 + 0.35 = 1.00 ✓

PERSONA LABELS
  Count:    9/9 ✓
  All expected labels present ✓

PERSONA NAMING RULES
  Rules: 9 (one per label) ✓
  Default catch-all: present ✓
  All referenced features in matrix ✓

COLD START RULES
  Rules: 5 ✓
  Default rule present ✓
  Priority sequence: 1,2,3,4,5 ✓

CLUSTERING CONFIG
  k_min(5) < k_max(15) ✓
  selection_weights sum: 1.00 ✓

═══════════════════════════════════════════════
RESULT: 1 PENDING (feature_store DDL not yet created)
        0 FAILURES
═══════════════════════════════════════════════
```
