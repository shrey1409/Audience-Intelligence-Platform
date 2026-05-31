-- sql/ddl/004_create_braintree_subscriptions.sql
-- Source: Braintree (payment events)
-- Refresh: incremental (event-driven on state change)
-- Coverage: ~10% of registered users (subscription rate)

CREATE TABLE {schema}.braintree_subscriptions (
    subscription_id       UUID            NOT NULL,
    user_id               UUID            NOT NULL,
    braintree_customer_id VARCHAR(50)     NOT NULL,
    plan_id               VARCHAR(50)     NOT NULL
                          CONSTRAINT chk_braintree_plan_id
                          CHECK (plan_id IN ('sports_plus','home_delivery','digital_all_access')),
    status                VARCHAR(20)     NOT NULL
                          CONSTRAINT chk_braintree_status
                          CHECK (status IN ('active','canceled','past_due')),
    amount                NUMERIC(10,2)   NOT NULL,
    currency              VARCHAR(3)      NOT NULL DEFAULT 'USD',
    billing_cycle_count   INTEGER         NOT NULL DEFAULT 0,
    next_billing_date     DATE,
    started_at            TIMESTAMP       NOT NULL,
    canceled_at           TIMESTAMP,
    payment_method        VARCHAR(20)     CONSTRAINT chk_braintree_payment_method
                                          CHECK (payment_method IN ('credit_card','paypal')),
    created_at            TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_braintree_subscriptions PRIMARY KEY (subscription_id),
    CONSTRAINT uq_braintree_customer_id UNIQUE (braintree_customer_id),
    CONSTRAINT fk_braintree_user_id
        FOREIGN KEY (user_id) REFERENCES {schema}.zephr_users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_braintree_user_id
    ON {schema}.braintree_subscriptions(user_id);

CREATE INDEX idx_braintree_status
    ON {schema}.braintree_subscriptions(status);
