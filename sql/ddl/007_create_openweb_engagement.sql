-- sql/ddl/007_create_openweb_engagement.sql
-- Source: OpenWeb (comments, likes, shares via SSO)
-- Refresh: incremental (daily delta sync)
-- Coverage: ~23% of registered users

CREATE TABLE {schema}.openweb_engagement (
    engagement_id    UUID        NOT NULL,
    user_id          UUID        NOT NULL,
    event_type       VARCHAR(20) NOT NULL
                     CONSTRAINT chk_openweb_event_type
                     CHECK (event_type IN ('comment','like','share')),
    content_id       VARCHAR(100),
    content_category VARCHAR(50),
    engaged_at       TIMESTAMP   NOT NULL,
    created_at       TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_openweb_engagement PRIMARY KEY (engagement_id),
    CONSTRAINT fk_openweb_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_openweb_user_id
    ON {schema}.openweb_engagement(user_id);

CREATE INDEX idx_openweb_user_event_type
    ON {schema}.openweb_engagement(user_id, event_type);
