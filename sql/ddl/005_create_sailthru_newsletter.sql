-- sql/ddl/005_create_sailthru_newsletter.sql
-- Source: Sailthru (email engagement)
-- Refresh: full_refresh (weekly snapshot — table truncated before each load)
-- Coverage: ~65% of registered users (email-collected users)

CREATE TABLE {schema}.sailthru_newsletter (
    record_id               UUID            PRIMARY KEY,
    user_id                 UUID            NULL,
    email                   VARCHAR(254)    NOT NULL,
    newsletter_count        SMALLINT        NOT NULL DEFAULT 0,
    open_rate               NUMERIC(5,4)    NOT NULL DEFAULT 0,
    click_through_rate      NUMERIC(5,4)    NOT NULL DEFAULT 0,
    email_engagement_score  SMALLINT        NOT NULL DEFAULT 0,
    engagement_tier         VARCHAR(10)     NULL,
    subscribed_newsletters  TEXT            NULL,
    nl_sports_alerts        BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_morning_report       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_page_six_daily       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_celebrity_news       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_evening_update       BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_post_opinion         BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_breaking_news        BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_real_estate          BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_tech_news            BOOLEAN         NOT NULL DEFAULT FALSE,
    nl_lifestyle_weekly     BOOLEAN         NOT NULL DEFAULT FALSE,
    last_synced_at          TIMESTAMP       NULL,
    created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP       NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.sailthru_newsletter
    ADD CONSTRAINT fk_sailthru_newsletter_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE SET NULL;

ALTER TABLE {schema}.sailthru_newsletter
    ADD CONSTRAINT chk_sailthru_engagement_tier
    CHECK (engagement_tier IN ('low','medium','high'));

CREATE INDEX idx_sailthru_user_id
    ON {schema}.sailthru_newsletter(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_sailthru_email
    ON {schema}.sailthru_newsletter(email);
