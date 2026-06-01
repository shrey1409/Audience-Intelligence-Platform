# ML Context — Audience Intelligence Platform

## Personas (9 total, K=5-15 for Phase 6 KMeans)

**Activation targets by size:**
1. High-Value Loyalists (18%) — Frequent visitors, high CAC, retention focus
2. At-Risk Champions (12%) — Historic power users, declining engagement, reactivation
3. Casual Browsers (25%) — Low frequency, high bounce, conversion focus
4. Deal Seekers (16%) — Price-sensitive, seasonal activity, discount offers
5. Mobile-First Engaged (15%) — Mobile-primary, content-heavy, native ads
6. Cart Abandoners (8%) — Strong purchase intent, checkout friction, recovery
7. New Explorers (4%) — <30 days, high-intent, onboarding/education
8. Lookalike Prospects (2%) — Similarity to high-value segment, acquisition focus
9. Inactive Segment (<1%) — No activity >1 year, potential reactivation

## Features (46 total, grouped by source)

**GA4 (F-01 to F-12):** session_count, event_count, avg_session_duration, bounce_rate, pages_per_session, last_event_days_ago, event_diversity, purchase_events, add_to_cart_events, view_promotion_events, conversion_rate, session_recency_score

**Transunion Demographics (F-13 to F-20):** age_score, income_score, household_size, has_children, marital_status, education_level, occupation_type, income_range

**First-Party CRM (F-21 to F-30):** customer_lifetime_value, lifecycle_stage, customer_tenure_days, email_engagement_rate, sms_engagement_rate, customer_tier, loyalty_points, purchase_frequency, avg_order_value, repeat_purchase_rate

**Behavioral RFM (F-31 to F-38):** recency_days, frequency_count, monetary_value, recency_score, frequency_score, monetary_score, rfm_segment, churn_risk_score

**Lookalike Expansion (F-39 to F-42):** lookalike_similarity, seed_segment_match, expansion_tier, similarity_confidence

**Survey Intent (F-43 to F-46):** product_interest_score, purchase_intent_score, sentiment_score, nps_score

## Feature Engineering Rules

**Log1p Transform (for F-07, F-14, F-32):**
- log_session_count = log1p(session_count)
- log_income = log1p(income_score)
- log_frequency = log1p(frequency_count)

**Zero-Fill Imputation (Phase 4 & 7):**
- Demographics (F-13 to F-20): 0 for missing
- Behavioral (F-31 to F-38): 0 for new users, 0.5 for churn_risk (cold-start)
- Lookalike (F-39 to F-42): 0 if user not in seed audience

**Scaling:** StandardScaler fit once in Phase 6 training, frozen for inference (Phase 7+)

## Training & Inference (Phase 6)

**Algorithm:** KMeans clustering, k=5-15 (silhouette score ≥ 0.30 for quality gate)

**Propensity Score Formulas:**
- Purchase_Propensity = 0.3×(conversion_rate) + 0.3×(purchase_intent_score) + 0.4×(rfm_score)
- Churn_Propensity = 0.4×(recency_days / 365) + 0.3×(churn_risk_score) + 0.3×(engagement_decline)
- Reactivation_Propensity = 0.5×(1 - churn_propensity) + 0.3×(lookalike_similarity) + 0.2×(persona_match)

**Model Versioning:** MLflow (Phase 6), tag by phase + date, alias=production after validation

**Inference Latency:** <100ms p99 (Redis cache, TTL=86400s)

## Cold-Start Handling (Phase 7 Inference)

**5 Rules for new users (0-30 days GA4 data):**
1. Use demographic defaults if available from transunion/first-party
2. Assign lookalike persona if email in seed audience
3. Set all behavioral features to population mean (impute from training data)
4. Reduce confidence scores by 40% (confidence_multiplier=0.6)
5. Re-evaluate persona assignment after 30 days / 100 events threshold

## Quality Gates
- **Silhouette Score:** ≥0.30 for cluster separation (must-pass before production)
- **Feature Completeness:** ≥95% of training rows have ≥60% non-null features
- **Data Drift:** Monthly comparison of inference feature distributions vs. training
- **Persona Stability:** KL-divergence between monthly cohorts <0.10 (alert if higher)
