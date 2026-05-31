-- sql/ddl/010_create_feature_store.sql
-- Source: Computed (pipeline Steps 3+8 output)
-- Refresh: weekly upsert (INSERT ... ON CONFLICT (user_id) DO UPDATE)
-- Coverage: 100% of registered users (new users get is_new_user=TRUE)
-- Total columns: 64 (4 identity + 46 ML features + 4 metadata flags + 10 ML output)
-- Authoritative: Alembic migrations. This DDL file is human-readable reference documentation.

CREATE TABLE {schema}.feature_store (
    -- Identity (4)
    user_id                           UUID            NOT NULL,
    created_at                        TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at                        TIMESTAMP       NOT NULL DEFAULT NOW(),
    is_new_user                       BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Web behaviour features: ML features #1-#11
    total_sessions                    INTEGER         NOT NULL DEFAULT 0,
    total_pageviews                   INTEGER         NOT NULL DEFAULT 0,
    active_days                       INTEGER         NOT NULL DEFAULT 0,
    avg_session_duration              NUMERIC(10,2)   NOT NULL DEFAULT 0,
    avg_pages_per_session             NUMERIC(8,4)    NOT NULL DEFAULT 0,
    bounce_rate                       NUMERIC(5,4)    NOT NULL DEFAULT 0,
    mobile_ratio                      NUMERIC(5,4)    NOT NULL DEFAULT 0,
    desktop_ratio                     NUMERIC(5,4)    NOT NULL DEFAULT 0,
    pageviews_per_session             NUMERIC(8,4)    NOT NULL DEFAULT 0,
    days_since_last_visit             INTEGER         NOT NULL DEFAULT 0,
    account_age_days                  INTEGER         NOT NULL DEFAULT 0,

    -- Content affinity features: ML features #12-#19
    ratio_sports                      NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_entertainment               NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_celebrity                   NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_shopping                    NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_opinion                     NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_world_news                  NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_business                    NUMERIC(5,4)    NOT NULL DEFAULT 0,
    ratio_lifestyle                   NUMERIC(5,4)    NOT NULL DEFAULT 0,

    -- Subscription features: ML features #20-#23
    has_subscription                  BOOLEAN         NOT NULL DEFAULT FALSE,
    subscription_amount               NUMERIC(10,2)   NOT NULL DEFAULT 0,
    total_billing_cycles              INTEGER         NOT NULL DEFAULT 0,
    days_until_renewal                INTEGER         NOT NULL DEFAULT 0,

    -- Email ML features: ML features #24-#33
    newsletter_count                  SMALLINT        NOT NULL DEFAULT 0,
    open_rate                         NUMERIC(5,4)    NOT NULL DEFAULT 0,
    click_through_rate                NUMERIC(5,4)    NOT NULL DEFAULT 0,
    email_engagement_score            SMALLINT        NOT NULL DEFAULT 0,
    nl_sports_alerts                  BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_morning_report                 BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_page_six_daily                 BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_celebrity_news                 BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_evening_update                 BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_post_opinion                   BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Email metadata flags (NOT in ML matrix — spec Section 15 Q7)
    nl_breaking_news                  BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_real_estate                    BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_tech_news                      BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_lifestyle_weekly               BOOLEAN         NOT NULL DEFAULT FALSE,

    -- Social features: ML features #34-#37
    total_comments                    INTEGER         NOT NULL DEFAULT 0,
    total_likes_given                 INTEGER         NOT NULL DEFAULT 0,
    total_shares                      INTEGER         NOT NULL DEFAULT 0,
    social_engagement_score           INTEGER         NOT NULL DEFAULT 0,

    -- Commerce features: ML features #38-#43
    total_affiliate_clicks            INTEGER         NOT NULL DEFAULT 0,
    total_transactions                INTEGER         NOT NULL DEFAULT 0,
    total_revenue_generated           NUMERIC(12,2)   NOT NULL DEFAULT 0,
    conversion_rate                   NUMERIC(5,4)    NOT NULL DEFAULT 0,
    avg_transaction_value             NUMERIC(10,2)   NOT NULL DEFAULT 0,
    unique_advertisers_clicked        INTEGER         NOT NULL DEFAULT 0,

    -- Demographic features: ML features #44-#46
    age_score                         SMALLINT        NOT NULL DEFAULT 0,
    income_score                      SMALLINT        NOT NULL DEFAULT 0,
    has_children                      BOOLEAN         NOT NULL DEFAULT FALSE,

    -- ML output columns (written by Step 8 — pipeline write-back)
    persona_label                     VARCHAR(50),
    cluster_id                        SMALLINT,
    algorithm_used                    VARCHAR(50)     CONSTRAINT chk_fs_algorithm_used
                                                      CHECK (algorithm_used IN (
                                                          'kmeans','bisecting_kmeans',
                                                          'gmm','hdbscan','ensemble')),
    cluster_score                     NUMERIC(6,4),
    last_updated                      TIMESTAMP,
    subscription_propensity_score     NUMERIC(6,4),
    churn_propensity_score            NUMERIC(6,4),
    commerce_propensity_score         NUMERIC(6,4),
    soft_persona_scores               TEXT,
    cluster_top_features              TEXT,

    CONSTRAINT pk_feature_store PRIMARY KEY (user_id)
);

-- ON CONFLICT (user_id) DO UPDATE uses the PK implicit unique index — no extra UNIQUE needed

CREATE INDEX idx_feature_store_persona_label
    ON {schema}.feature_store(persona_label)
    WHERE persona_label IS NOT NULL;

CREATE INDEX idx_feature_store_cluster_id
    ON {schema}.feature_store(cluster_id)
    WHERE cluster_id IS NOT NULL;

CREATE INDEX idx_feature_store_persona_cluster
    ON {schema}.feature_store(persona_label, cluster_id);

CREATE INDEX idx_feature_store_last_updated
    ON {schema}.feature_store(last_updated)
    WHERE last_updated IS NOT NULL;

CREATE INDEX idx_feature_store_is_new_user
    ON {schema}.feature_store(is_new_user)
    WHERE is_new_user = TRUE;
