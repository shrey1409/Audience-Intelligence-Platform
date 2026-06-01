-- sql/ddl/004_create_braintree_subscriptions.sql
-- Source: Braintree (payment events — real-time, ingested weekly)
-- Refresh: incremental (event-driven on state change)
-- Coverage: ~10% of registered users (subscription holders only)

CREATE TABLE {schema}.braintree_subscriptions (
    subscription_id         UUID            PRIMARY KEY,
    user_id                 UUID            NOT NULL,
    braintree_customer_id   VARCHAR(50)     NOT NULL,
    plan_id                 VARCHAR(50)     NOT NULL,
    status                  VARCHAR(20)     NOT NULL,
    amount                  NUMERIC(10,2)   NOT NULL,
    currency                VARCHAR(3)      NOT NULL DEFAULT 'USD',
    billing_cycle_count     INTEGER         NOT NULL DEFAULT 0,
    next_billing_date       DATE            NULL,
    started_at              TIMESTAMP       NOT NULL,
    canceled_at             TIMESTAMP       NULL,
    payment_method          VARCHAR(20)     NULL,
    created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP       NOT NULL DEFAULT NOW()
);

ALTER TABLE {schema}.braintree_subscriptions
    ADD CONSTRAINT uq_braintree_customer_id UNIQUE (braintree_customer_id);

ALTER TABLE {schema}.braintree_subscriptions
    ADD CONSTRAINT fk_braintree_subscriptions_user_id
    FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id)
    ON DELETE CASCADE;

ALTER TABLE {schema}.braintree_subscriptions
    ADD CONSTRAINT chk_braintree_plan_id
    CHECK (plan_id IN ('sports_plus','home_delivery','digital_all_access'));

ALTER TABLE {schema}.braintree_subscriptions
    ADD CONSTRAINT chk_braintree_status
    CHECK (status IN ('active','canceled','past_due'));

ALTER TABLE {schema}.braintree_subscriptions
    ADD CONSTRAINT chk_braintree_payment_method
    CHECK (payment_method IN ('credit_card','paypal'));

CREATE INDEX idx_braintree_user_id
    ON {schema}.braintree_subscriptions(user_id);

CREATE INDEX idx_braintree_status
    ON {schema}.braintree_subscriptions(status);
