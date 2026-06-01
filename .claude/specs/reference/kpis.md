# AIP KPIs Reference

## ML Quality KPIs (Platform Health)

| KPI | Metric | Target | Alert Threshold | Measurement |
|-----|--------|--------|-----------------|-------------|
| **Cluster Quality** | Silhouette score | ≥ 0.35 | < 0.30 (abort gate) | Overall silhouette after clustering |
| **Stability** | % users same persona WoW | ≥ 85% | < 80% for 3 consecutive weeks triggers re-eval | `len(same_label) / total_users` |
| **Coverage** | % users with ML persona | ≥ 95% | < 90% (investigate) | `1 - (new_users / total_users)` |
| **Feature Completeness** | Feature matrix rows | ≥ 95% of prior week | < 80% (abort pipeline) | Row count per feature engineering step |

## Propensity Score KPIs (Engagement Impact)

| Score Type | Formula Weight | Business Target |
|------------|-----------------|-----------------|
| **subscription_propensity** | newsletter_count(30%) + open_rate(25%) + recency_inverted(25%) + centroid_distance(20%) | Identify 2.8% of users for upsell |
| **churn_propensity** | days_since_last_visit(40%) + bounce_rate(30%) + billing_cycles_inverted(30%) | Identify at-risk subscribers ≥ 30 days early |
| **commerce_propensity** | ratio_shopping(35%) + affiliate_clicks(30%) + centroid_distance(35%) | Surface high-intent commerce readers |

## Data Source Coverage (ETL Health)

| Source | Expected Coverage | Alert Threshold (P1) | Alert Threshold (P2) | Failure Mode |
|--------|-------------------|----------------------|----------------------|--------------|
| Zephr (users) | 100% | — | — | Primary key; no fallback |
| GA4 (events) | ≥ 95% | < 90% | < 93% | Session/pageview features unavailable |
| Braintree (subscriptions) | 8–12% | — | < 5% | Subscription signal lost |
| Sailthru (newsletter) | 60–70% | — | < 55% | Newsletter engagement signal weak |
| Pushly (push) | 35–40% | — | < 30% | Push engagement signal weak |
| OpenWeb (social) | 23–30% | — | < 15% | Social engagement signal lost |
| Trackonomics (commerce) | 16–20% | — | < 10% | Commerce signal unavailable |
| Transunion (demographics) | 70% matched | < 65% | < 68% | Demographic signal degraded |

## Pipeline SLA KPIs

| Metric | Target | Failure Threshold | Recovery |
|--------|--------|-------------------|----------|
| **Weekly pipeline runtime** | ≤ 4 hours | > 2× rolling 4-week median | Manual trigger + investigation |
| **Step 1 runtime deviation** | ±20% WoW | > 20% = P2 alert | Scale resources or investigate source |
| **Row count deviation** | ±20% WoW | > 20% = Abort (F-03) | Investigate source system |
| **Silhouette alert delta** | ≤ 0.05 | > 0.05 drop = P2 | Investigate data quality or feature drift |
| **Persona distribution drift** | ≤ 30% relative per persona | > 30% = P2 per persona | Investigate and re-evaluate if 3+ weeks |

## Business KPIs (Activation Outcomes)

| Goal | Metric | Target | Baseline |
|------|--------|--------|----------|
| **Subscription Revenue** | Conversion rate (upsell to Subscription-Focused) | +15–25% vs control | Run-of-site conversion rate |
| **Ad Revenue (CPM Premium)** | CPM multiplier (persona-verified vs run-of-site) | 1.4–2.5× | $3–5 run-of-site CPM |
| **Newsletter Engagement** | CTR improvement (persona-segmented vs control) | +30–50% | Unsegmented control CTR |
| **Churn Reduction** | Annual churn rate (targeted retention vs control) | −20% on identified at-risk | Overall churn baseline |

## Configuration Thresholds (configs/base.yaml)

```yaml
etl:
  row_count_deviation_threshold: 0.20  # ±20%
  transunion_min_confidence: 0.70
  new_user_session_threshold: 4

ml:
  clustering:
    silhouette_threshold: 0.30  # Gate abort threshold
    silhouette_alert_delta: 0.05  # P2 alert if drops > 0.05
    stability_threshold: 0.80  # 80% users same persona WoW
    min_cluster_size_pct: 0.005  # ≥ 0.5% of total users
    random_state: 42
    selection_weights:
      silhouette: 0.40
      interpretability: 0.40
      stability: 0.20

  features:
    log1p_features: [total_sessions, total_pageviews, total_affiliate_clicks, total_comments]
    matrix: [46 feature names — see CLAUDE.md]

  propensity:
    subscription:
      weights: {newsletter_count: 0.30, open_rate: 0.25, days_since_last_visit_inv: 0.25, centroid_dist_inv: 0.20}
    churn:
      weights: {days_since_last_visit: 0.40, bounce_rate: 0.30, billing_cycles_inv: 0.30}
    commerce:
      weights: {ratio_shopping: 0.35, affiliate_clicks: 0.30, centroid_dist_inv: 0.35}

monitoring:
  ga4_coverage_alert_threshold: 0.90  # P1 if < 90%
  transunion_coverage_alert_threshold: 0.60  # P2 if < 60%
  pipeline_runtime_multiplier: 2.0  # P2 alert if step > 2× median
  persona_distribution_drift_threshold: 0.30  # P2 alert if > 30% relative change

api:
  batch_max_size: 1000
  p99_latency_target_single: 10  # ms
  p99_latency_target_batch: 100  # ms
  redis_ttl_days: 7
```
