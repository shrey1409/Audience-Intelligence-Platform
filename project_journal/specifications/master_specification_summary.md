# Master Specification Summary

**Full Document:** `.claude/specs/master-specification.md` (2,094 lines)
**Version:** 1.0
**Status:** APPROVED — all 7 open questions resolved
**Date:** 2026-05-30

---

## What It Covers

The master specification is the authoritative requirements document for all 15 engineering phases. It was created using Ultra Planning Mode from two source documents:
- `spec-source.md` (Spec v3.0)
- The original blueprint (Blueprint v2.0)

## Key Numbers

| Item | Count |
|---|---|
| Total F-XX requirements | 37 (F-01 through F-33, F-18 split into a/b/c) |
| Phases | 15 (CLAUDE.md currently tracks 9 of these) |
| Database tables | 9 canonical + 1 bridge = 10 |
| ML features | 46 (immutable — defined in configs/base.yaml) |
| Persona labels | 9 |
| Propensity score types | 3 (subscription, churn, commerce) |
| Cold-start rules | 5 (in priority order) |
| Architectural decisions made | 11 |
| Risks identified | 14 |

## Critical Resolved Decisions (Section 15)

| ID | Decision |
|---|---|
| Q2 | feature_store DDL: 46 ML + 4 metadata nl_* + 10 ML output + 4 audit = 64 columns |
| Q3 | CLAUDE.md updated with canonical table names (spec-source.md names win) |
| Q4 | Airflow in `requirements/airflow.txt` (not base.txt — dependency conflict) |
| Q5 | MLflow local filesystem for dev (not MinIO/S3) |
| Q6 | Physical table names follow spec-source.md (e.g., `zephr_users` not `user_profiles`) |
| Q7 | 6 nl_* flags in ML matrix; 4 additional as metadata-only (stored but not fed to clustering) |

## The 46 ML Features (exact list)

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

## The 9 Persona Labels (exact strings)

```
loyalist, subscription_focused, high_value_shopper, sports_focused,
social_engager, occasional_buyer, celebrity_entertainment, casual_reader, low_engager
```

## Propensity Weight Formulas

All weights from `configs/base.yaml ml.propensity.*`. Must sum to 1.0 each.

```
subscription: newsletter_count_scaled(0.30) + open_rate_scaled(0.25) +
              days_since_last_visit_scaled_inverted(0.25) + dist_to_subscription_focused_inverted(0.20) = 1.00

churn: days_since_last_visit_scaled(0.40) + bounce_rate_scaled(0.30) +
       total_billing_cycles_scaled_inverted(0.30) = 1.00

commerce: ratio_shopping_scaled(0.35) + total_affiliate_clicks_scaled(0.30) +
          dist_to_high_value_shopper_inverted(0.35) = 1.00
```

## Key Non-Functional Requirements

- API p99 < 10ms (single user)
- API p99 < 100ms (batch 1000 users)
- 10,000 req/sec throughput
- 99.9% API uptime
- Pipeline: ≥ 49/52 successful runs per year
- Test coverage: ≥ 80% on ETL, feature engineering, API code
