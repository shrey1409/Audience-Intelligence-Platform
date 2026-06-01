# ETL Data Sources Reference

## The 8 Source Systems

All source systems feed into one of nine PostgreSQL staging tables. Identity resolution stitches these sources together via `user_id` (universal identifier).

### 1. **Zephr** (User Profiles)
- **Table:** `zephr_users`
- **Mode:** Incremental (delta)
- **Cadence:** Daily (ingested weekly to AIP)
- **Key Data:** user_id (PK), email, account_age_days, subscription state
- **Coverage:** 100% (primary key source)
- **Identity Key:** user_id (source of truth)
- **Failure Impact:** Critical — no fallback. If Zephr is unavailable, pipeline aborts.

### 2. **GA4/BigQuery** (Behavioural Analytics)
- **Table:** `ga4_events` (event-level; aggregated to user-level in Feature Engineering)
- **Mode:** Incremental (daily event dump to BigQuery, ingested to AIP weekly)
- **Cadence:** Daily event collection; weekly pipeline ingestion
- **Key Data:** user_pseudo_id (GA4 native ID), session metrics, pageviews per section, bounce_rate, mobile/desktop ratio
- **Coverage:** 95%+ (some users may be anonymous)
- **Identity Key:** user_pseudo_id → user_id (via login bridge table)
- **Aggregates:** total_sessions, total_pageviews, avg_session_duration, bounce_rate, ratio_sports, ratio_entertainment, ratio_celebrity, ratio_shopping, ratio_opinion, ratio_world_news, ratio_business, ratio_lifestyle
- **Failure Impact:** Major. Features: total_sessions, pageviews, bounce_rate, all ratio_* features unavailable. Cold-start path can recover for users with < 5 sessions.

### 3. **Braintree** (Subscription/Payments)
- **Table:** `braintree_subscriptions`
- **Mode:** Incremental (state changes)
- **Cadence:** Real-time events pushed to AIP; ingested weekly
- **Key Data:** customer_id (= user_id), subscription state, amount, billing_cycles, next_renewal_date
- **Coverage:** 8–12% (subscription holders only)
- **Identity Key:** customer_id = user_id (direct FK, no resolution required)
- **Features:** has_subscription, subscription_amount, total_billing_cycles, days_until_renewal
- **Failure Impact:** Moderate. Subscription signal lost; propensity_subscription scoring degrades but pipeline continues (F-08 zero-imputation).

### 4. **Sailthru** (Email Engagement)
- **Table:** `sailthru_newsletter`
- **Mode:** Full refresh (snapshot of current subscriptions and engagement)
- **Cadence:** Weekly snapshot from Sailthru API
- **Key Data:** email (identity), newsletter subscriptions (pipe-delimited text), open_rate, click_through_rate
- **Coverage:** 60–70% (email-collected users)
- **Identity Key:** email → user_id (via Zephr email column)
- **Features:** 6 binary newsletter flags (nl_sports_alerts, nl_morning_report, nl_page_six_daily, nl_celebrity_news, nl_evening_update, nl_post_opinion), open_rate, click_through_rate, email_engagement_score (ordinal)
- **Newsletter Handling:** Additional newsletters (nl_breaking_news, nl_real_estate, nl_tech_news, nl_lifestyle_weekly) stored in feature_store as metadata but not included in the 46-feature ML matrix.
- **Failure Impact:** Moderate-High. Newsletter subscription signal lost; email_engagement_score and propensity_subscription degrade.

### 5. **Pushly** (Push Notification Engagement)
- **Table:** `pushly_subscribers`
- **Mode:** Incremental (subscription changes)
- **Cadence:** Weekly
- **Key Data:** external_id (= user_id at push opt-in), push engagement metrics, subscription status
- **Coverage:** 35–40%
- **Identity Key:** external_id = user_id (direct equality; no resolution needed)
- **Features:** Push engagement score (if available; otherwise zero-imputed)
- **Failure Impact:** Low-Moderate. Push signal lost; no direct propensity impact but reduces engagement completeness.

### 6. **OpenWeb** (Social Engagement & Comments)
- **Table:** `openweb_engagement`
- **Mode:** Incremental (new comments, likes, shares)
- **Cadence:** Weekly
- **Key Data:** user_id (direct FK, SSO linkage), comments, likes given, shares
- **Coverage:** 23–30%
- **Identity Key:** user_id (direct FK; no resolution required)
- **Features:** total_comments, total_likes_given, total_shares, social_engagement_score (weighted: 3× comments + 1× likes + 2× shares)
- **Failure Impact:** Low-Moderate. Social Engager persona signal weakens; overall persona quality degrades slightly.

### 7. **Trackonomics** (Commerce & Affiliate)
- **Table:** `trackonomics_clicks`
- **Mode:** Incremental (new clicks and transactions)
- **Cadence:** Weekly
- **Key Data:** user_id, affiliate link clicks, transaction data, revenue
- **Coverage:** 16–20%
- **Identity Key:** user_id (passed as URL parameter; direct FK)
- **Features:** total_affiliate_clicks, total_transactions, total_revenue_generated, conversion_rate, avg_transaction_value, unique_advertisers_clicked
- **Failure Impact:** Moderate. Commerce signal lost; High-Value Shopper and Occasional Buyer personas degrade; propensity_commerce unavailable.

### 8. **Transunion** (Demographic Enrichment)
- **Table:** `transunion_demographics`
- **Mode:** Full refresh (periodic demographic snapshot)
- **Cadence:** Monthly or quarterly (less frequent than weekly pipeline)
- **Key Data:** hashed_email (identity), age_score, income_score, has_children, match_confidence
- **Coverage:** ~70% of users; only 0.70+ match_confidence included in ML features (F-05)
- **Identity Key:** hashed_email → user_id (via Zephr hashed_email column)
- **Match Confidence Filter:** Records with match_confidence < 0.70 excluded from ML matrix; age_score, income_score, has_children set to 0 for excluded users
- **Features:** age_score, income_score, has_children
- **Failure Impact:** Low. Demographic signal lost; persona quality impacts minimal (only 3 features affected).

## Identity Resolution Summary

| Source | Identity Key | Resolution Method | Unresolved Handling |
|--------|--------------|------------------|-------------------|
| Zephr | user_id | Primary key — no resolution | N/A (source of truth) |
| GA4 | user_pseudo_id | GA4 → user_id bridge table (login events) | Anonymous users dropped |
| Braintree | customer_id | Mapped at subscription creation = user_id | Users without subscriptions skipped |
| Sailthru | email | Sailthru email → Zephr email → user_id | Unmatched emails skipped |
| Pushly | external_id | Set at push opt-in = user_id | Non-opted users skipped |
| OpenWeb | user_id | Direct FK (SSO integrated) | No resolution required |
| Trackonomics | user_id | Direct FK (URL parameter) | No resolution required |
| Transunion | hashed_email | Transunion hashed_email → Zephr hashed_email → user_id | Unmatched users zero-imputed (F-08) |

## Pipeline Ingestion Step (Step 1)

1. Query each of the 8 sources sequentially
2. Log `rows_ingested`, `start_time`, `end_time`, `mode` for each source
3. Calculate row count deviation % vs prior week
4. If any source deviates > 20%, abort entire pipeline (F-03)
5. Validate schema expectations (column presence, type compatibility)

## Feature Coverage by Source

| Feature | Source | Optional? | Zero-Imputation |
|---------|--------|-----------|-----------------|
| total_sessions, total_pageviews, avg_session_duration, bounce_rate, ratio_* | GA4 | No | N/A (required) |
| has_subscription, subscription_amount, total_billing_cycles | Braintree | Yes (8–12%) | Yes, 0.0 |
| newsletter_count, nl_* flags, open_rate, email_engagement_score | Sailthru | Yes (60–70%) | Yes, 0.0 |
| social_engagement_score, total_comments, total_likes, total_shares | OpenWeb | Yes (23–30%) | Yes, 0.0 |
| total_affiliate_clicks, total_transactions, conversion_rate | Trackonomics | Yes (16–20%) | Yes, 0.0 |
| age_score, income_score, has_children | Transunion | Yes (70%, then 0.70+ confidence) | Yes, 0.0 |

## Data Freshness SLA

| Source | Expected Freshness | Pipeline Window | Stale Threshold |
|--------|-------------------|-----------------|-----------------|
| Zephr | ≤ 24 hours | Daily | > 48 hours = alert |
| GA4 | ≤ 24 hours | Daily; aggregated weekly | > 24 hours = alert |
| Braintree | Real-time | Daily | > 24 hours = alert |
| Sailthru | ≤ 1 week | Weekly | > 8 days = alert |
| Pushly | ≤ 24 hours | Daily; aggregated weekly | > 24 hours = alert |
| OpenWeb | ≤ 24 hours | Daily; aggregated weekly | > 24 hours = alert |
| Trackonomics | ≤ 24 hours | Daily; aggregated weekly | > 24 hours = alert |
| Transunion | ≤ 1 month | Monthly/quarterly | > 45 days = alert |
