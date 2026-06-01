# Project Vision — Audience Intelligence Platform

**Document Type:** Vision & Goals
**Created:** 2026-05-30
**Last Updated:** 2026-05-31

---

## Why This Platform Exists

Digital publishers own massive reader datasets — web behaviour, email engagement, social interactions, push notifications, and commerce signals — yet they monetise them as if these datasets do not exist. Audience segments are editorial guesses: defined by journalists, not discovered from data.

The Audience Intelligence Platform replaces editorial guesswork with ML-discovered behavioural archetypes. Instead of a sports editor guessing that "sports readers like sports content," the platform discovers that the sports audience contains at least four completely different groups:

1. **Loyalist subscribers** — long-tenure, high engagement, high conversion
2. **Sports-focused casual readers** — high ratio_sports, low subscription signal
3. **Social engagers** — share match content, low direct commerce value
4. **Affiliate commerce users** — click gear links, high transaction value

These are three different activation strategies. Without ML-discovered segments, every monetisation trigger fires indiscriminately at the wrong people at the wrong moment.

---

## Business Goals

### Primary Revenue Goals

| Goal | Mechanism | Target |
|---|---|---|
| Subscription revenue | Identify Subscription-Focused users before they churn; trigger upsell at the right behavioural signal | +15–25% subscription conversion vs unmatched baseline |
| Ad CPM uplift | Serve advertisers verified audience segments (Sports-Focused, 18–34, push opt-in) | +20–40% CPM premium over run-of-site |
| Newsletter CTR | Personalise content per persona archetype | +30–50% CTR improvement |
| Churn reduction | Detect churn signals 30 days before cancellation via churn_propensity_score | −20% annual churn rate |

### Secondary Goals

- Build adaptive segments that evolve automatically as audience behaviour shifts
- Surface micro-segments editorial teams would never define manually
- Provide a single unified reader view joining 8 source systems into one row per user
- Support flexible cluster counts (K=5 for niche publishers, K=12–15 for multi-brand)

---

## The NYPost Validation Benchmark

This platform is directly derived from the New York Post Data Labs initiative, which:
- Segmented 66 million users across 8 source systems
- Used Bisecting K-Means clustering
- Discovered 9 behavioural personas
- Commanded 20–40% CPM premiums on persona-verified inventory

The NYPost scale (50–100M users, 200–500M GA4 events/year) is the large-client design target. Development uses a 100,000-user synthetic dataset that mirrors real-world persona proportions.

---

## Expected Business Outcomes

### Short-term (6–12 months post-launch)
- First paying client deployed on the platform
- Weekly pipeline running reliably (target: 49/52 weeks without manual intervention)
- API serving persona data at p99 < 10ms to downstream consumers
- Silhouette score > 0.35 on real publisher data (validated on synthetic first)

### Medium-term (12–24 months)
- Multi-client deployment — each client gets isolated PostgreSQL schema
- Algorithm evaluation framework selecting optimal K per client
- MLflow model registry with 12 months of run history per client
- Full observability: Grafana dashboards, PagerDuty alerts

### Long-term
- 10+ publisher clients running on the platform
- Persona API called at impression time by ad servers (programmatic targeting)
- Propensity scores triggering automated subscription upsell sequences
- Platform sold as B2B SaaS with per-seat or per-API-call pricing

---

## The Three Core Systems

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA PLATFORM                                                    │
│  8 source connectors → 10 PostgreSQL tables → Feature Store      │
│  Weekly Airflow DAG, 9 steps, validation gates at each step      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ 46-feature matrix
┌───────────────────────▼─────────────────────────────────────────┐
│  ML PLATFORM                                                      │
│  4-stage algorithm evaluation → BisectingKMeans production run   │
│  → 9 persona labels + 3 propensity scores → MLflow tracking      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ persona_label + scores
┌───────────────────────▼─────────────────────────────────────────┐
│  SERVING PLATFORM                                                 │
│  FastAPI microservice → Redis cache (TTL 7 days)                 │
│  → p99 < 10ms single user, p99 < 100ms batch 1000 users         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Business Model

- **B2B SaaS** sold to digital publishers of all sizes
- Each client: isolated PostgreSQL schema, isolated pipeline run, isolated algorithm selection
- **Vendor-agnostic**: no dependency on specific CMS, ad server, or email platform
- Only hard dependency: GA4 BigQuery export (native Google Analytics 4 path)
- Cloud path: MWAA (AWS) or Cloud Composer (GCP) for production deployments

---

## The 9 Persona Labels

These are the behavioural archetypes discovered by the clustering pipeline. Named after the dominant features in each cluster's centroid:

| Label | Key Signals | Business Value |
|---|---|---|
| `loyalist` | High billing_cycles, account_age_days, email engagement | High-value retention target |
| `subscription_focused` | High newsletter_count, open_rate, CTR | Upsell trigger audience |
| `high_value_shopper` | High conversion_rate, avg_transaction_value | Commerce premium inventory |
| `sports_focused` | Dominant ratio_sports, nl_sports_alerts | Sports advertiser premium |
| `social_engager` | High comments, likes, shares | Social sharing amplifier |
| `occasional_buyer` | ratio_shopping dominant, sporadic clicks | Re-engagement commerce |
| `celebrity_entertainment` | ratio_celebrity + ratio_entertainment | Lifestyle advertiser target |
| `casual_reader` | Default / low-signal | Run-of-site baseline |
| `low_engager` | High bounce_rate, high days_since_last_visit | Churn risk, re-engagement |

---

## Design Philosophy

1. **Config-driven over code-driven** — every tunable parameter in `configs/base.yaml`
2. **Schema isolation** — one PostgreSQL schema per client, zero cross-client queries possible
3. **Fail loudly** — pipeline aborts on data quality gates, never silently corrupts
4. **Reproducible ML** — `random_state=42` everywhere, all artifacts in MLflow
5. **Serve from cache** — API reads Redis exclusively; never blocks on DB at request time
6. **Cold-start over 404** — users not in cache get rule-based labels, never errors
