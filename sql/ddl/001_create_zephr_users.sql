-- sql/ddl/001_create_zephr_users.sql
-- Source: Zephr (user registration and subscription state)
-- Refresh: incremental (delta on registration writes + state updates)
-- Coverage: 100% — primary key table; all other tables FK here

CREATE TABLE {schema}.zephr_users (
    user_id         UUID            PRIMARY KEY,
    email           VARCHAR(254)    NOT NULL,
    hashed_email    VARCHAR(64)     NULL,
    first_name      VARCHAR(100)    NULL,
    last_name       VARCHAR(100)    NULL,
    account_age_days INTEGER        NOT NULL DEFAULT 0,
    is_registered   BOOLEAN         NOT NULL DEFAULT TRUE,
    registration_date TIMESTAMP     NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.zephr_users
    ADD CONSTRAINT uq_zephr_users_email UNIQUE (email);

CREATE INDEX idx_zephr_users_email
    ON {schema}.zephr_users(email);

CREATE INDEX idx_zephr_users_hashed_email
    ON {schema}.zephr_users(hashed_email)
    WHERE hashed_email IS NOT NULL;

CREATE INDEX idx_zephr_users_registration_date
    ON {schema}.zephr_users(registration_date);
