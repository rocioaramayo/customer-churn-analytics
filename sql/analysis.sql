-- Customer Churn Analytics - Etapa 1
-- Motor: SQLite

-- 1. KPIs globales
SELECT
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS global_churn_rate_pct,
    ROUND(AVG(CASE WHEN churn_flag = 1 THEN clv_realized_usd END), 2) AS avg_clv_churned_usd,
    ROUND(AVG(CASE WHEN churn_flag = 0 THEN clv_realized_usd END), 2) AS avg_clv_active_usd,
    ROUND(SUM(annualized_revenue_lost_usd), 2) AS annualized_revenue_lost_usd
FROM customers;

-- 2. Evolución mensual
SELECT
    month,
    active_start,
    new_customers,
    churned_customers,
    active_end,
    ROUND(100.0 * churn_rate, 2) AS churn_rate_pct,
    annualized_revenue_lost_usd
FROM monthly_churn_kpis
ORDER BY month;

-- 3. Churn por tipo de contrato
SELECT
    contract_type,
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct,
    ROUND(SUM(annualized_revenue_lost_usd), 2) AS annualized_revenue_lost_usd
FROM customers
GROUP BY contract_type
ORDER BY churn_rate_pct DESC;

-- 4. Churn por método de pago
SELECT
    payment_method,
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct
FROM customers
GROUP BY payment_method
ORDER BY churn_rate_pct DESC;

-- 5. Churn por antigüedad
SELECT
    tenure_band,
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct,
    ROUND(AVG(clv_realized_usd), 2) AS avg_clv_realized_usd
FROM customers
GROUP BY tenure_band
ORDER BY churn_rate_pct DESC;

-- 6. Relación entre tickets de soporte y churn
SELECT
    support_tickets_90d,
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct
FROM customers
GROUP BY support_tickets_90d
HAVING COUNT(*) >= 25
ORDER BY support_tickets_90d;

-- 7. Segmentos prioritarios con tamaño suficiente
SELECT
    contract_type,
    payment_method,
    service_category,
    COUNT(*) AS customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct,
    ROUND(SUM(annualized_revenue_lost_usd), 2) AS annualized_revenue_lost_usd
FROM customers
GROUP BY contract_type, payment_method, service_category
HAVING COUNT(*) >= 50
ORDER BY annualized_revenue_lost_usd DESC
LIMIT 15;

-- 8. Cohorte de alto riesgo para revisar
SELECT
    customer_id,
    contract_type,
    payment_method,
    tenure_months,
    support_tickets_90d,
    satisfaction_score,
    monthly_charge_usd,
    status
FROM customers
WHERE contract_type = 'Mes a mes'
  AND support_tickets_90d >= 3
ORDER BY support_tickets_90d DESC, monthly_charge_usd DESC;

