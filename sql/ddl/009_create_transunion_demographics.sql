-- sql/ddl/009_create_transunion_demographics.sql
-- Source: Transunion TruAudience API (monthly batch)
-- Refresh: full_refresh (monthly)
-- Coverage: ~70% match rate; records with match_confidence < etl.transunion_min_confidence are excluded

CREATE TABLE {schema}.transunion_demographics (
    demo_id          UUID            NOT NULL,
    user_id          UUID            UNIQUE,
    hashed_email     VARCHAR(64)     NOT NULL,
    match_confidence NUMERIC(4,3)    NOT NULL,
    excluded         BOOLEAN         NOT NULL DEFAULT FALSE,
    age_range        VARCHAR(20)     CONSTRAINT chk_transunion_age_range
                                     CHECK (age_range IN ('age_18_24','age_25_34','age_35_44',
                                                          'age_45_54','age_55_64','age_65_plus')),
    gender           VARCHAR(10)     CONSTRAINT chk_transunion_gender
                                     CHECK (gender IN ('m','f','non_binary','unknown')),
    income_range     VARCHAR(20)     CONSTRAINT chk_transunion_income_range
                                     CHECK (income_range IN ('lt_30k','range_30_50k','range_50_75k',
                                                             'range_75_100k','range_100_150k','gt_150k')),
    has_children     BOOLEAN,
    home_ownership   VARCHAR(10)     CONSTRAINT chk_transunion_home_ownership
                                     CHECK (home_ownership IN ('owner','renter','unknown')),
    education        VARCHAR(20)     CONSTRAINT chk_transunion_education
                                     CHECK (education IN ('high_school','some_college',
                                                          'bachelors','graduate')),
    address_state    VARCHAR(2),
    address_zip      VARCHAR(10),
    match_date       DATE            NOT NULL,
    created_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_transunion_demographics PRIMARY KEY (demo_id),
    CONSTRAINT fk_transunion_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_transunion_hashed_email
    ON {schema}.transunion_demographics(hashed_email);

CREATE INDEX idx_transunion_match_confidence
    ON {schema}.transunion_demographics(match_confidence);

CREATE INDEX idx_transunion_excluded
    ON {schema}.transunion_demographics(excluded)
    WHERE excluded = FALSE;
