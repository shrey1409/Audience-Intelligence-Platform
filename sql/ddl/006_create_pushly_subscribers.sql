-- sql/ddl/006_create_pushly_subscribers.sql
-- Source: Pushly (push notification opt-in)
-- Refresh: incremental (daily delta sync)
-- Coverage: ~35% of registered users

CREATE TABLE {schema}.pushly_subscribers (
    subscriber_id   UUID        NOT NULL,
    user_id         UUID        NOT NULL,
    external_id     VARCHAR(100) NOT NULL,
    platform        VARCHAR(20) NOT NULL
                    CONSTRAINT chk_pushly_platform
                    CHECK (platform IN ('web_desktop','web_mobile','ios','android')),
    push_opted_in   BOOLEAN     NOT NULL DEFAULT TRUE,
    push_is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    opted_in_at     TIMESTAMP   NOT NULL,
    opted_out_at    TIMESTAMP,
    last_push_sent_at TIMESTAMP,
    push_open_count INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_pushly_subscribers PRIMARY KEY (subscriber_id),
    CONSTRAINT uq_pushly_external_id UNIQUE (external_id),
    CONSTRAINT fk_pushly_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_pushly_user_id
    ON {schema}.pushly_subscribers(user_id);

CREATE INDEX idx_pushly_platform
    ON {schema}.pushly_subscribers(platform);
