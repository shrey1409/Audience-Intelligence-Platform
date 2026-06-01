# AIP Personas Reference

## The 9 Persona Labels

The ML clustering pipeline assigns one of nine human-readable persona labels to each registered user.

### 1. **Loyalist**
- Long-tenure subscriber with high billing cycles
- High email engagement and click-through rates
- Premium reader — disproportionate revenue per user
- Retention strategy: renewal incentives, exclusive content

### 2. **Subscription-Focused**
- High newsletter subscription count
- Strong open and click-through rates
- Propensity signal: newsletter_count, open_rate, days_since_last_visit
- Activation: timed upsell sequences, re-engagement campaigns

### 3. **High-Value Shopper**
- High conversion rate and average transaction value
- Frequent affiliate link clicks
- Commerce signal dominant in feature matrix
- Activation: commerce promotions, affiliate content partnerships

### 4. **Sports-Focused**
- Dominant ratio_sports (pageviews on sports content ≥ 50%)
- Sports newsletter subscription (nl_sports_alerts)
- Content-driven segment, stable week-to-week
- Activation: sports-vertical campaigns, sports advertiser targeting

### 5. **Social Engager**
- High comment count, likes given, shares
- Social engagement score elevated
- Community-driven reader
- Activation: discussion-based content, community features

### 6. **Occasional Buyer**
- ratio_shopping dominant but sporadic affiliate clicks
- Inconsistent commerce behaviour
- Latent commerce potential
- Activation: triggered product recommendations, seasonal sales

### 7. **Celebrity-Entertainment**
- Dominant ratio_celebrity + ratio_entertainment (≥ 50% combined)
- Distinct from Sports-Focused
- Entertainment-vertical readers
- Activation: celebrity/entertainment advertiser targeting

### 8. **Casual Reader**
- Default / low-signal cluster
- Mixed behaviour, no dominant affinity
- Moderate engagement
- Activation: baseline re-engagement, content discovery

### 9. **Low Engager**
- High bounce_rate
- days_since_last_visit dominant signal
- High churn propensity
- Retention strategy: early re-engagement, win-back campaigns

## Cold-Start Labels (for users with insufficient ML signal)

- **sports_cold_start** — ratio_sports > 0.50
- **celebrity_cold_start** — (ratio_celebrity + ratio_entertainment) > 0.50
- **subscription_cold_start** — has_subscription = True
- **newsletter_cold_start** — newsletter_count > 0
- **new_user** — default for users with ≤ 4 sessions

## Feature Importance per Persona

Feature importance is computed as: `abs(centroid[cluster][feature] − global_mean) / global_std`

Top-5 defining features per persona are logged to MLflow after each run and drive the persona naming/labelling logic.

### Persona Naming Rules

The `configs/base.yaml` file contains `personas.naming_rules` lookup table mapping cluster feature signatures to human-readable labels. This lookup is applied in `ml/training/evaluation/interpretability.py` during the naming phase.

If a cluster's top-5 features don't match any rule, the cluster is flagged as ambiguous and requires manual review before deploying to production.
