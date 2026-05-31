-- sql/ddl/002_create_ga4_events.sql
-- Source: GA4 BigQuery daily export
-- Refresh: incremental (daily)
-- Coverage: ~60% of registered users (anonymous sessions excluded)
-- Note: user_id is nullable — populated by identity stitching (Step 2)
-- Note: No table partitioning at Phase 2; add PARTITION BY RANGE(event_date) at mid-publisher scale

CREATE TABLE {schema}.ga4_events (
    event_id              UUID            NOT NULL,
    user_id               UUID,
    user_pseudo_id        VARCHAR(64)     NOT NULL,
    event_name            VARCHAR(100)    NOT NULL,
    event_date            DATE            NOT NULL,
    event_timestamp       TIMESTAMP       NOT NULL,
    session_id            VARCHAR(64),
    device_category       VARCHAR(50)     CONSTRAINT chk_ga4_device_category
                                          CHECK (device_category IN ('desktop','mobile','tablet')),
    page_category         VARCHAR(50)     CONSTRAINT chk_ga4_page_category
                                          CHECK (page_category IN ('sports','entertainment','celebrity',
                                                 'business','lifestyle','world_news','opinion',
                                                 'shopping','us_news','page_six')),
    page_path             TEXT,
    engagement_time_msec  INTEGER         NOT NULL DEFAULT 0,
    is_bounce             BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_ga4_events PRIMARY KEY (event_id),
    CONSTRAINT fk_ga4_events_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE SET NULL
);

CREATE INDEX idx_ga4_events_user_id
    ON {schema}.ga4_events(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_ga4_events_user_pseudo_id
    ON {schema}.ga4_events(user_pseudo_id);

CREATE INDEX idx_ga4_events_event_date
    ON {schema}.ga4_events(event_date);

CREATE INDEX idx_ga4_events_pseudo_id_date
    ON {schema}.ga4_events(user_pseudo_id, event_date);
