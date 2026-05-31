-- sql/ddl/008_create_trackonomics_clicks.sql
-- Source: Trackonomics (affiliate click SFTP export)
-- Refresh: incremental (daily)
-- Coverage: ~16% user coverage (anonymous clicks excluded at ETL validate step)

CREATE TABLE {schema}.trackonomics_clicks (
    click_id           UUID            NOT NULL,
    user_id            UUID            NOT NULL,
    advertiser_id      VARCHAR(100)    NOT NULL,
    product_category   VARCHAR(30)     CONSTRAINT chk_trackonomics_product_category
                                       CHECK (product_category IN (
                                           'electronics','fashion','home','beauty',
                                           'sports_gear','books','travel')),
    click_timestamp    TIMESTAMP       NOT NULL,
    converted          BOOLEAN         NOT NULL DEFAULT FALSE,
    transaction_id     VARCHAR(100),
    transaction_amount NUMERIC(10,2),
    created_at         TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_trackonomics_clicks PRIMARY KEY (click_id),
    CONSTRAINT fk_trackonomics_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_trackonomics_user_id
    ON {schema}.trackonomics_clicks(user_id);

CREATE INDEX idx_trackonomics_user_converted
    ON {schema}.trackonomics_clicks(user_id, converted);

CREATE INDEX idx_trackonomics_advertiser_id
    ON {schema}.trackonomics_clicks(advertiser_id);
