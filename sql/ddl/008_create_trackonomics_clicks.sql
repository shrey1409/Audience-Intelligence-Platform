-- sql/ddl/008_create_trackonomics_clicks.sql
-- Source: Trackonomics (affiliate click tracking SFTP export)
-- Refresh: incremental (daily SFTP export)
-- Coverage: ~18% user coverage; multiple click rows per commerce user

CREATE TABLE {schema}.trackonomics_clicks (
    click_id            UUID            PRIMARY KEY,
    user_id             UUID            NOT NULL,
    advertiser_id       VARCHAR(100)    NOT NULL,
    product_category    VARCHAR(30)     NULL,
    click_timestamp     TIMESTAMP       NOT NULL,
    converted           BOOLEAN         NOT NULL DEFAULT FALSE,
    transaction_id      VARCHAR(100)    NULL,
    transaction_amount  NUMERIC(10,2)   NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.trackonomics_clicks
    ADD CONSTRAINT fk_trackonomics_clicks_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE;

ALTER TABLE {schema}.trackonomics_clicks
    ADD CONSTRAINT chk_trackonomics_product_category
    CHECK (product_category IN (
        'electronics','fashion','home','beauty','sports_gear','books','travel'
    ));

CREATE INDEX idx_trackonomics_user_id
    ON {schema}.trackonomics_clicks(user_id);

CREATE INDEX idx_trackonomics_user_converted
    ON {schema}.trackonomics_clicks(user_id, converted);

CREATE INDEX idx_trackonomics_advertiser_id
    ON {schema}.trackonomics_clicks(advertiser_id);
