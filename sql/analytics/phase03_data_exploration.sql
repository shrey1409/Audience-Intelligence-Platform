-- ============================================================
-- AUDIENCE INTELLIGENCE PLATFORM
-- Phase 3 Data Exploration Queries
-- Run each block individually in SQLTools (highlight + Cmd+Enter)
-- ============================================================

-- ── 1. ROW COUNTS ALL TABLES ─────────────────────────────────
SELECT
    relname AS table_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- ── 2. ZEPHR_USERS — Identity Hub ────────────────────────────
SELECT
    COUNT(*)                                         AS total_users,
    COUNT(DISTINCT email)                            AS unique_emails,
    ROUND(AVG(account_age_days))                     AS avg_account_age_days,
    MIN(created_at::date)                            AS earliest_signup,
    MAX(created_at::date)                            AS latest_signup,
    SUM(CASE WHEN is_registered THEN 1 ELSE 0 END)  AS registered_users
FROM public.zephr_users;

-- ── 3. GA4_EVENTS — Web Behaviour ────────────────────────────
-- Event type breakdown
SELECT
    event_name,
    COUNT(*)                                AS event_count,
    COUNT(DISTINCT user_pseudo_id)          AS unique_users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.ga4_events
GROUP BY event_name
ORDER BY event_count DESC;

-- Device split
SELECT
    device_category,
    COUNT(*)                                AS events,
    COUNT(DISTINCT user_pseudo_id)          AS unique_users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.ga4_events
GROUP BY device_category
ORDER BY events DESC;

-- Page category split
SELECT
    page_category,
    COUNT(*)                                AS events,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.ga4_events
GROUP BY page_category
ORDER BY events DESC;

-- Events per user distribution
SELECT
    CASE
        WHEN event_count < 50   THEN '0-49'
        WHEN event_count < 100  THEN '50-99'
        WHEN event_count < 200  THEN '100-199'
        WHEN event_count < 500  THEN '200-499'
        ELSE '500+'
    END AS events_bucket,
    COUNT(*) AS user_count
FROM (
    SELECT user_pseudo_id, COUNT(*) AS event_count
    FROM public.ga4_events
    GROUP BY user_pseudo_id
) t
GROUP BY 1
ORDER BY MIN(
    CASE
        WHEN event_count < 50   THEN 1
        WHEN event_count < 100  THEN 2
        WHEN event_count < 200  THEN 3
        WHEN event_count < 500  THEN 4
        ELSE 5
    END
);

-- ── 4. BRAINTREE_SUBSCRIPTIONS — Payment Data ────────────────
SELECT
    status,
    plan_id,
    COUNT(*)                                AS subscriptions,
    ROUND(AVG(amount)::numeric, 2)          AS avg_amount,
    MIN(amount)                             AS min_amount,
    MAX(amount)                             AS max_amount,
    ROUND(AVG(billing_cycle_count))         AS avg_billing_cycles
FROM public.braintree_subscriptions
GROUP BY status, plan_id
ORDER BY subscriptions DESC;

-- Payment method split
SELECT
    payment_method,
    COUNT(*)                                AS count,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.braintree_subscriptions
GROUP BY payment_method
ORDER BY count DESC;

-- ── 5. SAILTHRU_NEWSLETTER — Email Engagement ────────────────
SELECT
    engagement_tier,
    COUNT(*)                                AS users,
    ROUND(AVG(open_rate)::numeric, 3)           AS avg_open_rate,
    ROUND(AVG(click_through_rate)::numeric, 3)  AS avg_click_rate,
    ROUND(AVG(newsletter_count))                AS avg_newsletters_subscribed
FROM public.sailthru_newsletter
GROUP BY engagement_tier
ORDER BY avg_open_rate DESC;

-- Newsletter flag popularity
SELECT
    SUM(CASE WHEN nl_sports_alerts    THEN 1 ELSE 0 END) AS sports_alerts,
    SUM(CASE WHEN nl_morning_report   THEN 1 ELSE 0 END) AS morning_report,
    SUM(CASE WHEN nl_page_six_daily   THEN 1 ELSE 0 END) AS page_six,
    SUM(CASE WHEN nl_celebrity_news   THEN 1 ELSE 0 END) AS celebrity_news,
    SUM(CASE WHEN nl_evening_update   THEN 1 ELSE 0 END) AS evening_update,
    SUM(CASE WHEN nl_post_opinion     THEN 1 ELSE 0 END) AS post_opinion,
    SUM(CASE WHEN nl_breaking_news    THEN 1 ELSE 0 END) AS breaking_news,
    SUM(CASE WHEN nl_real_estate      THEN 1 ELSE 0 END) AS real_estate,
    SUM(CASE WHEN nl_tech_news        THEN 1 ELSE 0 END) AS tech_news,
    SUM(CASE WHEN nl_lifestyle_weekly THEN 1 ELSE 0 END) AS lifestyle_weekly
FROM public.sailthru_newsletter;

-- ── 6. PUSHLY_SUBSCRIBERS — Push Notifications ───────────────
SELECT
    platform,
    COUNT(*)                                AS subscribers,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct,
    SUM(CASE WHEN push_is_active THEN 1 ELSE 0 END) AS active,
    ROUND(AVG(push_open_count)::numeric, 1)          AS avg_push_open_count
FROM public.pushly_subscribers
GROUP BY platform
ORDER BY subscribers DESC;

-- ── 7. OPENWEB_ENGAGEMENT — Social Engagement (event-level) ──
-- Note: event-level table, multiple rows per user
-- Use GROUP BY user_id to get per-user aggregates
SELECT
    event_type,
    COUNT(*)                                AS event_count,
    COUNT(DISTINCT user_id)                 AS unique_users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.openweb_engagement
GROUP BY event_type
ORDER BY event_count DESC;

-- Per-user engagement summary
SELECT
    COUNT(DISTINCT user_id)                 AS openweb_users,
    ROUND(AVG(events_per_user))             AS avg_events_per_user,
    MAX(events_per_user)                    AS max_events_per_user
FROM (
    SELECT user_id, COUNT(*) AS events_per_user
    FROM public.openweb_engagement
    GROUP BY user_id
) t;

-- ── 8. TRACKONOMICS_CLICKS — Commerce (event-level) ──────────
SELECT
    product_category,
    COUNT(*)                                AS clicks,
    COUNT(DISTINCT user_id)                 AS unique_users,
    ROUND(AVG(transaction_amount)::numeric, 2) AS avg_revenue,
    SUM(CASE WHEN converted
        THEN 1 ELSE 0 END)                     AS conversions,
    ROUND(
        SUM(CASE WHEN converted THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*), 1)                 AS conversion_rate_pct
FROM public.trackonomics_clicks
GROUP BY product_category
ORDER BY clicks DESC;

-- ── 9. TRANSUNION_DEMOGRAPHICS — Third-party Data ────────────
SELECT
    age_range,
    COUNT(*)                                AS users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct,
    income_range,
    SUM(CASE WHEN has_children
        THEN 1 ELSE 0 END)                  AS has_children_count
FROM public.transunion_demographics
GROUP BY age_range, income_range
ORDER BY users DESC;

-- Match confidence distribution
SELECT
    CASE
        WHEN match_confidence >= 0.90 THEN '0.90-1.00 (high)'
        WHEN match_confidence >= 0.70 THEN '0.70-0.89 (above threshold)'
        ELSE 'below 0.70 (excluded from ML)'
    END AS confidence_bucket,
    COUNT(*) AS records,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1) AS pct
FROM public.transunion_demographics
GROUP BY 1
ORDER BY 1;

-- ── 10. FEATURE_STORE — ML-Ready Output ──────────────────────
-- Persona distribution (populated after Phase 6)
SELECT
    COALESCE(persona_label, 'NULL — awaiting Phase 6 ML') AS persona_label,
    COUNT(*)                                AS users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.feature_store
GROUP BY persona_label
ORDER BY users DESC;

-- Feature coverage (% non-zero per source block)
SELECT
    ROUND(AVG(CASE WHEN total_sessions         > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS ga4_pct,
    ROUND(AVG(CASE WHEN has_subscription       = true THEN 1.0 ELSE 0 END) * 100, 1) AS braintree_pct,
    ROUND(AVG(CASE WHEN open_rate              > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS sailthru_pct,
    ROUND(AVG(CASE WHEN total_comments         > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS openweb_pct,
    ROUND(AVG(CASE WHEN total_affiliate_clicks > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS trackonomics_pct,
    ROUND(AVG(CASE WHEN age_score              > 0    THEN 1.0 ELSE 0 END) * 100, 1) AS transunion_pct
FROM public.feature_store;

-- Bounce rate distribution by bucket
SELECT
    CASE
        WHEN bounce_rate = 0.0              THEN '0.00 (no bounce)'
        WHEN bounce_rate < 0.20             THEN '0.01-0.19 (low)'
        WHEN bounce_rate < 0.40             THEN '0.20-0.39 (moderate)'
        WHEN bounce_rate < 0.60             THEN '0.40-0.59 (average)'
        WHEN bounce_rate < 0.80             THEN '0.60-0.79 (high)'
        ELSE                                     '0.80-1.00 (very high)'
    END AS bounce_bucket,
    COUNT(*)                                AS users,
    ROUND(COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 1)           AS pct
FROM public.feature_store
GROUP BY 1
ORDER BY MIN(bounce_rate);

-- Propensity scores summary (all NULL until Phase 7 inference writes them)
SELECT
    ROUND(MIN(subscription_propensity_score)::numeric, 3)  AS sub_min,
    ROUND(AVG(subscription_propensity_score)::numeric, 3)  AS sub_avg,
    ROUND(MAX(subscription_propensity_score)::numeric, 3)  AS sub_max,
    ROUND(MIN(churn_propensity_score)::numeric, 3)         AS churn_min,
    ROUND(AVG(churn_propensity_score)::numeric, 3)         AS churn_avg,
    ROUND(MAX(churn_propensity_score)::numeric, 3)         AS churn_max,
    ROUND(MIN(commerce_propensity_score)::numeric, 3)      AS commerce_min,
    ROUND(AVG(commerce_propensity_score)::numeric, 3)      AS commerce_avg,
    ROUND(MAX(commerce_propensity_score)::numeric, 3)      AS commerce_max
FROM public.feature_store;

-- Top content affinity ratios
SELECT
    ROUND(AVG(ratio_sports)::numeric, 3)        AS avg_sports,
    ROUND(AVG(ratio_entertainment)::numeric, 3) AS avg_entertainment,
    ROUND(AVG(ratio_celebrity)::numeric, 3)     AS avg_celebrity,
    ROUND(AVG(ratio_shopping)::numeric, 3)      AS avg_shopping,
    ROUND(AVG(ratio_opinion)::numeric, 3)       AS avg_opinion,
    ROUND(AVG(ratio_world_news)::numeric, 3)    AS avg_world_news,
    ROUND(AVG(ratio_business)::numeric, 3)      AS avg_business,
    ROUND(AVG(ratio_lifestyle)::numeric, 3)     AS avg_lifestyle
FROM public.feature_store;

-- ── 11. CROSS-TABLE INTEGRITY CHECKS ─────────────────────────
-- FK integrity: every staging table user_id exists in zephr_users
SELECT 'braintree' AS source,
    COUNT(*) AS orphan_rows
FROM public.braintree_subscriptions b
WHERE NOT EXISTS (
    SELECT 1 FROM public.zephr_users z WHERE z.user_id = b.user_id
)
UNION ALL
SELECT 'sailthru',   COUNT(*) FROM public.sailthru_newsletter s
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = s.user_id)
UNION ALL
SELECT 'pushly',     COUNT(*) FROM public.pushly_subscribers p
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = p.user_id)
UNION ALL
SELECT 'openweb',    COUNT(*) FROM public.openweb_engagement o
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = o.user_id)
UNION ALL
SELECT 'trackonomics', COUNT(*) FROM public.trackonomics_clicks t
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = t.user_id)
UNION ALL
SELECT 'transunion', COUNT(*) FROM public.transunion_demographics td
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = td.user_id)
UNION ALL
SELECT 'feature_store', COUNT(*) FROM public.feature_store fs
WHERE NOT EXISTS (SELECT 1 FROM public.zephr_users z WHERE z.user_id = fs.user_id);
-- Expected: all sources return 0 orphan rows
