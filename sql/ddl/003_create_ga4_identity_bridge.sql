-- sql/ddl/003_create_ga4_identity_bridge.sql
-- Source: Derived from GA4 login events + Zephr user_id
-- Refresh: incremental (appended by identity stitcher on each login event)
-- Coverage: ~60% of GA4 user_pseudo_ids resolve to a user_id

CREATE TABLE {schema}.ga4_identity_bridge (
    bridge_id       UUID        NOT NULL,
    user_pseudo_id  VARCHAR(64) NOT NULL,
    user_id         UUID        NOT NULL,
    first_seen_at   TIMESTAMP   NOT NULL,
    last_seen_at    TIMESTAMP   NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_ga4_identity_bridge PRIMARY KEY (bridge_id),
    CONSTRAINT uq_ga4_bridge_user_pseudo_id UNIQUE (user_pseudo_id),
    CONSTRAINT fk_ga4_bridge_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_ga4_bridge_user_id
    ON {schema}.ga4_identity_bridge(user_id);
