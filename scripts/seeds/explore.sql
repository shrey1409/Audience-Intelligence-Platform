-- ── ROW COUNTS ──────────────────────────────────────────────────────────────
SELECT
    relname AS table_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- ── PERSONA DISTRIBUTION ────────────────────────────────────────────────────
SELECT
    persona_label,
    COUNT(*) AS users,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM public.feature_store
GROUP BY persona_label
ORDER BY users DESC;

-- ── FEATURE COVERAGE ────────────────────────────────────────────────────────
SELECT
    ROUND(AVG(CASE WHEN total_sessions   > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS ga4_pct,
    ROUND(AVG(CASE WHEN has_subscription = true THEN 1.0 ELSE 0 END) * 100, 1) AS braintree_pct,
    ROUND(AVG(CASE WHEN open_rate        > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS sailthru_pct,
    ROUND(AVG(CASE WHEN age_score        > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS transunion_pct,
    ROUND(AVG(CASE WHEN total_comments   > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS openweb_pct,
    ROUND(AVG(CASE WHEN total_affiliate_clicks > 0 THEN 1.0 ELSE 0 END) * 100, 1) AS trackonomics_pct
FROM public.feature_store;

-- ── PROPENSITY SCORES BY PERSONA ────────────────────────────────────────────
SELECT
    persona_label,
    COUNT(*) AS users,
    ROUND(AVG(subscription_propensity_score)::numeric, 3) AS avg_sub,
    ROUND(AVG(churn_propensity_score)::numeric, 3)        AS avg_churn,
    ROUND(AVG(commerce_propensity_score)::numeric, 3)     AS avg_commerce
FROM public.feature_store
GROUP BY persona_label
ORDER BY avg_sub DESC;

-- ── SAMPLE LOYALISTS ────────────────────────────────────────────────────────
SELECT
    user_id,
    total_sessions,
    open_rate,
    total_billing_cycles,
    subscription_propensity_score,
    persona_label
FROM public.feature_store
WHERE persona_label = 'loyalist'
ORDER BY total_sessions DESC
LIMIT 10;

-- ── TOP FEATURES PER PERSONA (spot check) ───────────────────────────────────
SELECT
    persona_label,
    ROUND(AVG(ratio_sports)::numeric, 3)          AS avg_ratio_sports,
    ROUND(AVG(ratio_celebrity)::numeric, 3)        AS avg_ratio_celebrity,
    ROUND(AVG(total_comments)::numeric, 1)         AS avg_comments,
    ROUND(AVG(conversion_rate)::numeric, 3)        AS avg_conversion,
    ROUND(AVG(bounce_rate)::numeric, 3)            AS avg_bounce
FROM public.feature_store
GROUP BY persona_label
ORDER BY persona_label;

-- ── GA4 EVENTS SAMPLE ───────────────────────────────────────────────────────
SELECT
    event_name,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_pseudo_id) AS unique_users
FROM public.ga4_events
GROUP BY event_name
ORDER BY event_count DESC
LIMIT 10;
