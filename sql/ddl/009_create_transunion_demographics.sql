-- sql/ddl/009_create_transunion_demographics.sql
-- Source: Transunion TruAudience API (monthly batch refresh)
-- Refresh: full_refresh (monthly batch)
-- Coverage: ~70% match rate; records below 0.70 confidence flagged excluded=TRUE

CREATE TABLE {schema}.transunion_demographics (
    demo_id             UUID            PRIMARY KEY,
    user_id             UUID            NULL UNIQUE,
    hashed_email        VARCHAR(64)     NOT NULL,
    match_confidence    NUMERIC(4,3)    NOT NULL,
    excluded            BOOLEAN         NOT NULL DEFAULT FALSE,
    age_range           VARCHAR(20)     NULL,
    gender              VARCHAR(10)     NULL,
    income_range        VARCHAR(20)     NULL,
    has_children        BOOLEAN         NULL,
    home_ownership      VARCHAR(10)     NULL,
    education           VARCHAR(20)     NULL,
    address_state       VARCHAR(2)      NULL,
    address_zip         VARCHAR(10)     NULL,
    match_date          DATE            NOT NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT fk_transunion_demographics_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE;

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT chk_transunion_age_range
    CHECK (age_range IN ('age_18_24','age_25_34','age_35_44','age_45_54','age_55_64','age_65_plus'));

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT chk_transunion_gender
    CHECK (gender IN ('m','f','non_binary','unknown'));

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT chk_transunion_income_range
    CHECK (income_range IN ('lt_30k','range_30_50k','range_50_75k','range_75_100k','range_100_150k','gt_150k'));

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT chk_transunion_home_ownership
    CHECK (home_ownership IN ('owner','renter','unknown'));

ALTER TABLE {schema}.transunion_demographics
    ADD CONSTRAINT chk_transunion_education
    CHECK (education IN ('high_school','some_college','bachelors','graduate'));

CREATE UNIQUE INDEX idx_transunion_user_id
    ON {schema}.transunion_demographics(user_id)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_transunion_hashed_email
    ON {schema}.transunion_demographics(hashed_email);

CREATE INDEX idx_transunion_match_confidence
    ON {schema}.transunion_demographics(match_confidence);

CREATE INDEX idx_transunion_excluded
    ON {schema}.transunion_demographics(excluded)
    WHERE excluded = FALSE;
