# Data Context — Audience Intelligence Platform

## Database Tables (10 total)

### Source Staging Tables (8) — actual tables as of Phase 3

**Event-level tables (multiple rows per user — aggregated in feature_store_builder via GROUP BY user_id):**
- **ga4_events** — 95% user coverage, ~148 events/user, 14.1M rows. PK=engagement_id. Aggregated to sessions, pageviews, bounce_rate, page ratios.
- **openweb_engagement** — 23% user coverage, ~13 events/user per type, 296K rows. PK=engagement_id. ⚠️ NOT one row per user. Event types: comment/like/share. Aggregated to total_comments, total_likes_given, total_shares. social_engager persona has Poisson(40) events; others Poisson(5).
- **trackonomics_clicks** — 16% user coverage, multiple click rows per user, 104K rows. PK=click_id. Aggregated to total_transactions, total_revenue_generated, conversion_rate.

**One-row-per-user tables:**
- **ga4_identity_bridge** — 95% coverage, 1 row per GA4 user. Maps user_pseudo_id → user_id via login events.
- **zephr_users** — 100% coverage, 100K rows. Identity hub. UNIQUE(user_id).
- **braintree_subscriptions** — 10% coverage, 10K rows. 1 active/cancelled/past_due record per subscriber.
- **sailthru_newsletter** — 100% coverage, 100K rows. 1 row per user with 10 newsletter flag columns.
- **pushly_subscribers** — 35% coverage, 35K rows. 1 row per opted-in user.
- **transunion_demographics** — 70% coverage, 70K rows. 85% have match_confidence ≥ 0.70.

### Core Tables (2)
- **user_profiles** (user_id PK) — 100% coverage, identity hub, 1M+ rows
- **feature_store** (user_id PK, 64 columns) — updated daily, 1M+ rows, UNIQUE(user_id)

### Legacy (no longer used)
- ~~persona_assignments~~ — Replaced by feature_store (persona_scores columns)

## Identity Resolution
- **GA4 pseudo_id → user_id:** ga4_identity_bridge (login events)
- **Email → user_id:** first_party_attributes (primary), transunion_demographics (fallback)
- **Device → user_id:** device_graph (device_id joins)

## Feature Store Schema
- **64 columns:** 46 ML features + 9 persona_scores + user_id + updated_at + created_at
- **46 ML features grouped by source:**
  - GA4: F-01 through F-12 (session count, event patterns, recency)
  - Transunion: F-13 through F-20 (age, income, household, children)
  - First-party: F-21 through F-30 (lifecycle stage, customer value, tenure)
  - Behavioral: F-31 through F-38 (RFM, engagement, churn risk)
  - Lookalike: F-39 through F-42 (similarity scores, seed flags)
  - Survey: F-43 through F-46 (sentiment, product interest, intent)

## Seeding Order (for Phase 4)
1. user_profiles (email from first_party_attributes)
2. ga4_identity_bridge (from GA4 login events)
3. ga4_events (aggregate after identity resolution)
4. transunion_demographics
5. first_party_attributes
6. behavioral_segments
7. lookalike_model_scores
8. survey_responses
9. device_graph
10. feature_store (computed from above)

## Cold-Start Strategy (Phase 7)
When no historical data exists:
- Zero-fill demographic features (F-13 to F-20)
- Use behavioral defaults: RFM = (0, 0, 0), churn_risk = 0.5
- Apply lookalike scoring if email in seed audience
- Mask persona assignment until 30 days of GA4 events

## Key Constraints
- **ON CONFLICT upserts** require UNIQUE constraints (feature_store, user_profiles)
- **CASCADE deletes** on user_profiles → ga4_events, user_sessions
- **No SELECT *:** Always name columns explicitly
- **Schema placeholder:** All DDL uses `{schema}` (never hardcode "public")
