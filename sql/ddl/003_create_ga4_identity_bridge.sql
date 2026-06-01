-- sql/ddl/003_create_ga4_identity_bridge.sql
-- Source: Derived from GA4 login events + Zephr user_id
-- Refresh: incremental (appended on each login event during identity stitching)
-- Coverage: ~95% of GA4 user_pseudo_ids resolve to a user_id

CREATE TABLE {schema}.ga4_identity_bridge (
    bridge_id       UUID        PRIMARY KEY,
    user_pseudo_id  VARCHAR(64) NOT NULL,
    user_id         UUID        NOT NULL,
    first_seen_at   TIMESTAMP   NOT NULL,
    last_seen_at    TIMESTAMP   NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.ga4_identity_bridge
    ADD CONSTRAINT uq_ga4_bridge_user_pseudo_id UNIQUE (user_pseudo_id);

ALTER TABLE {schema}.ga4_identity_bridge
    ADD CONSTRAINT fk_ga4_bridge_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE;

CREATE UNIQUE INDEX idx_ga4_bridge_user_pseudo_id
    ON {schema}.ga4_identity_bridge(user_pseudo_id);

CREATE INDEX idx_ga4_bridge_user_id
    ON {schema}.ga4_identity_bridge(user_id);
