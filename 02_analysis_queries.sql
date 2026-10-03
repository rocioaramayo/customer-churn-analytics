-- 1. Churn e ingreso mensual en riesgo por segmento.
SELECT
    c.segment,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN s.status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(100.0 * SUM(CASE WHEN s.status = 'Churned' THEN 1 ELSE 0 END) / COUNT(*), 2) AS churn_rate_pct,
    SUM(CASE WHEN s.status = 'Churned' THEN s.monthly_revenue ELSE 0 END) AS monthly_revenue_lost
FROM fact_subscriptions s
JOIN dim_customers c ON c.customer_id = s.customer_id
GROUP BY c.segment
ORDER BY churn_rate_pct DESC;

-- 2. Clientes activos con señales de riesgo: tickets y satisfacción baja.
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    p.plan_name,
    s.monthly_revenue,
    COUNT(t.ticket_id) AS tickets,
    ROUND(AVG(t.satisfaction_score), 2) AS avg_satisfaction,
    CASE
        WHEN COUNT(t.ticket_id) >= 3 AND AVG(t.satisfaction_score) <= 2.5 THEN 'High'
        WHEN COUNT(t.ticket_id) >= 2 OR AVG(t.satisfaction_score) <= 3 THEN 'Medium'
        ELSE 'Low'
    END AS risk_level
FROM fact_subscriptions s
JOIN dim_customers c ON c.customer_id = s.customer_id
JOIN dim_plans p ON p.plan_id = s.plan_id
LEFT JOIN fact_support_tickets t ON t.customer_id = c.customer_id
WHERE s.status = 'Active'
GROUP BY c.customer_id, c.customer_name, c.segment, p.plan_name, s.monthly_revenue
ORDER BY risk_level, tickets DESC, avg_satisfaction;
