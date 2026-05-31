-- sql/ddl/001_create_zephr_users.sql
-- Source: Zephr (user registration and subscription state)
-- Refresh: incremental (registration writes + state updates)
-- Coverage: 100% of registered users
-- Build order: 001 — PK table; all other tables FK here

CREATE TABLE {schema}.zephr_users (
    user_id          UUID            NOT NULL,
    email            VARCHAR(254)    NOT NULL,
    hashed_email     VARCHAR(64),
    first_name       VARCHAR(100),
    last_name        VARCHAR(100),
    account_age_days INTEGER         NOT NULL DEFAULT 0,
    is_registered    BOOLEAN         NOT NULL DEFAULT TRUE,
    registration_date TIMESTAMP      NOT NULL,
    created_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_zephr_users PRIMARY KEY (user_id),
    CONSTRAINT uq_zephr_users_email UNIQUE (email)
);

CREATE INDEX idx_zephr_users_hashed_email
    ON {schema}.zephr_users(hashed_email)
    WHERE hashed_email IS NOT NULL;

CREATE INDEX idx_zephr_users_registration_date
    ON {schema}.zephr_users(registration_date);
