-- sql/ddl/007_create_openweb_engagement.sql
-- Source: OpenWeb (SSO-authenticated social engagement)
-- Refresh: incremental (new comments, likes, shares)
-- Coverage: ~26% of registered users

CREATE TABLE {schema}.openweb_engagement (
    engagement_id   UUID        PRIMARY KEY,
    user_id         UUID        NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
    content_id      VARCHAR(100) NULL,
    content_category VARCHAR(50) NULL,
    engaged_at      TIMESTAMP   NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.openweb_engagement
    ADD CONSTRAINT fk_openweb_engagement_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE;

ALTER TABLE {schema}.openweb_engagement
    ADD CONSTRAINT chk_openweb_event_type
    CHECK (event_type IN ('comment','like','share'));

CREATE INDEX idx_openweb_user_id
    ON {schema}.openweb_engagement(user_id);

CREATE INDEX idx_openweb_user_event_type
    ON {schema}.openweb_engagement(user_id, event_type);
