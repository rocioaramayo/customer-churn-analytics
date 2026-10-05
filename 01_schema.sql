-- Esquema analítico equivalente a los CSV de entrada.
CREATE TABLE dim_customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name VARCHAR(80) NOT NULL,
    signup_date DATE NOT NULL,
    segment VARCHAR(30) NOT NULL,
    region VARCHAR(30) NOT NULL,
    acquisition_channel VARCHAR(30) NOT NULL
);

CREATE TABLE dim_plans (
    plan_id INTEGER PRIMARY KEY,
    plan_name VARCHAR(30) NOT NULL,
    billing_period VARCHAR(20) NOT NULL,
    monthly_price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE fact_subscriptions (
    subscription_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES dim_customers(customer_id),
    plan_id INTEGER NOT NULL REFERENCES dim_plans(plan_id),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL,
    monthly_revenue DECIMAL(10, 2) NOT NULL,
    churn_reason VARCHAR(40)
);

CREATE TABLE fact_support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES dim_customers(customer_id),
    opened_date DATE NOT NULL,
    category VARCHAR(40) NOT NULL,
    resolution_hours INTEGER NOT NULL,
    satisfaction_score INTEGER NOT NULL
);
