-- sql/ddl/002_create_ga4_events.sql
-- Source: GA4 BigQuery event export
-- Refresh: incremental (daily BigQuery dump, partitioned by event_date)
-- Coverage: ~95% of users (anonymous sessions resolved via ga4_identity_bridge)

CREATE TABLE {schema}.ga4_events (
    event_id            UUID        PRIMARY KEY,
    user_id             UUID        NULL,
    user_pseudo_id      VARCHAR(64) NOT NULL,
    event_name          VARCHAR(100) NOT NULL,
    event_date          DATE        NOT NULL,
    event_timestamp     TIMESTAMP   NOT NULL,
    session_id          VARCHAR(64) NULL,
    device_category     VARCHAR(50) NULL,
    page_category       VARCHAR(50) NULL,
    page_path           TEXT        NULL,
    engagement_time_msec INTEGER    NOT NULL DEFAULT 0,
    is_bounce           BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.ga4_events
    ADD CONSTRAINT fk_ga4_events_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE SET NULL;

ALTER TABLE {schema}.ga4_events
    ADD CONSTRAINT chk_ga4_events_device_category
    CHECK (device_category IN ('desktop','mobile','tablet'));

ALTER TABLE {schema}.ga4_events
    ADD CONSTRAINT chk_ga4_events_page_category
    CHECK (page_category IN (
        'sports','entertainment','celebrity','business',
        'lifestyle','world_news','opinion','shopping','us_news','page_six'
    ));

CREATE INDEX idx_ga4_events_user_id
    ON {schema}.ga4_events(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_ga4_events_user_pseudo_id
    ON {schema}.ga4_events(user_pseudo_id);

CREATE INDEX idx_ga4_events_event_date
    ON {schema}.ga4_events(event_date);

CREATE INDEX idx_ga4_events_pseudo_id_date
    ON {schema}.ga4_events(user_pseudo_id, event_date);
