-- sql/ddl/005_create_sailthru_newsletter.sql
-- Source: Sailthru (email engagement)
-- Refresh: full_refresh (weekly)
-- Coverage: ~100% of registered users with email
-- Note: 6 nl_* columns are ML features; 4 are metadata-only (not in ML matrix)

CREATE TABLE {schema}.sailthru_newsletter (
    record_id              UUID            NOT NULL,
    user_id                UUID,
    email                  VARCHAR(254)    NOT NULL,
    newsletter_count       SMALLINT        NOT NULL DEFAULT 0,
    open_rate              NUMERIC(5,4)    NOT NULL DEFAULT 0,
    click_through_rate     NUMERIC(5,4)    NOT NULL DEFAULT 0,
    email_engagement_score SMALLINT        NOT NULL DEFAULT 0,
    engagement_tier        VARCHAR(10)     CONSTRAINT chk_sailthru_engagement_tier
                                           CHECK (engagement_tier IN ('low','medium','high')),
    subscribed_newsletters TEXT,
    nl_sports_alerts       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_morning_report      BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_page_six_daily      BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_celebrity_news      BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_evening_update      BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_post_opinion        BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_breaking_news       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_real_estate         BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_tech_news           BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_lifestyle_weekly    BOOLEAN         NOT NULL DEFAULT FALSE,
    last_synced_at         TIMESTAMP,
    created_at             TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_sailthru_newsletter PRIMARY KEY (record_id),
    CONSTRAINT fk_sailthru_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_sailthru_user_id
    ON {schema}.sailthru_newsletter(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_sailthru_email
    ON {schema}.sailthru_newsletter(email);
