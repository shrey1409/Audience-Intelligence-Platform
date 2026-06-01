# Data Context — Audience Intelligence Platform

## Database Tables (10 total)

### Source Staging Tables (8)
- **ga4_events** (user_pseudo_id) — 64% coverage, identity via ga4_identity_bridge
- **ga4_identity_bridge** (user_pseudo_id → user_id) — 100% coverage, login events only
- **transunion_demographics** (email) — 70% coverage (match_confidence ≥ 0.70)
- **first_party_attributes** (email) — 95% coverage, customer CRM data
- **behavioral_segments** (email) — 80% coverage, RFM + engagement signals
- **lookalike_model_scores** (email) — 60% coverage, seed audience expansion
- **survey_responses** (email) — 45% coverage, opt-in survey data
- **device_graph** (device_id) — 75% coverage, device-to-user resolution

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
