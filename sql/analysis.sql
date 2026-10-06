-- E-commerce Customer Retention Analytics
-- SQLite | Corte: 2025-12-31 | Churn: más de 120 días sin comprar

-- 1. KPIs ejecutivos
SELECT COUNT(*) AS customers,
       SUM(churn_flag) AS churned_customers,
       ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct,
       ROUND(100.0 * AVG(repeat_customer_flag), 2) AS repeat_purchase_rate_pct,
       ROUND(AVG(avg_order_value_usd), 2) AS avg_order_value_usd,
       ROUND(SUM(net_revenue_usd), 2) AS customer_lifetime_revenue_usd,
       ROUND(SUM(annual_revenue_at_risk_usd), 2) AS annual_revenue_at_risk_usd
FROM fact_customer_snapshot;

-- 2. Evolución mensual
SELECT month, orders, active_customers, new_customers, churned_customers,
       ROUND(100.0 * churn_rate, 2) AS churn_rate_pct,
       ROUND(net_revenue_usd, 2) AS net_revenue_usd,
       ROUND(avg_order_value_usd, 2) AS avg_order_value_usd
FROM fact_monthly_kpis
ORDER BY month;

-- 3. Estado de la cartera
SELECT customer_status, COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS customer_share_pct,
       ROUND(AVG(days_since_last_order), 1) AS avg_recency_days,
       ROUND(AVG(orders), 2) AS avg_orders,
       ROUND(AVG(net_revenue_usd), 2) AS avg_lifetime_revenue_usd,
       ROUND(SUM(annual_revenue_at_risk_usd), 2) AS annual_revenue_at_risk_usd
FROM fact_customer_snapshot
GROUP BY customer_status
ORDER BY customers DESC;

-- 4. Segmentación RFM
SELECT rfm_segment, COUNT(*) AS customers,
       ROUND(AVG(days_since_last_order), 1) AS avg_recency_days,
       ROUND(AVG(orders), 2) AS avg_orders,
       ROUND(AVG(net_revenue_usd), 2) AS avg_lifetime_revenue_usd,
       ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct
FROM fact_customer_snapshot
GROUP BY rfm_segment
ORDER BY avg_lifetime_revenue_usd DESC;

-- 5. Churn por segmento y canal de adquisición
SELECT c.customer_segment, c.acquisition_channel,
       COUNT(*) AS customers, SUM(s.churn_flag) AS churned_customers,
       ROUND(100.0 * AVG(s.churn_flag), 2) AS churn_rate_pct,
       ROUND(SUM(s.annual_revenue_at_risk_usd), 2) AS revenue_at_risk_usd
FROM fact_customer_snapshot s
JOIN dim_customers c USING (customer_id)
GROUP BY c.customer_segment, c.acquisition_channel
HAVING COUNT(*) >= 50
ORDER BY revenue_at_risk_usd DESC;

-- 6. Rendimiento por categoría
SELECT p.category, COUNT(DISTINCT i.order_id) AS orders,
       SUM(i.quantity) AS units,
       ROUND(SUM(i.net_sales_usd), 2) AS net_sales_usd,
       ROUND(SUM(i.gross_margin_usd), 2) AS gross_margin_usd,
       ROUND(100.0 * SUM(i.returned_quantity) / NULLIF(SUM(i.quantity), 0), 2) AS return_rate_pct
FROM fact_order_items i
JOIN dim_products p USING (product_id)
GROUP BY p.category
ORDER BY net_sales_usd DESC;

-- 7. Impacto de devoluciones y soporte en churn
SELECT CASE WHEN returns = 0 THEN 'Sin devoluciones'
            WHEN returns = 1 THEN '1 devolución' ELSE '2+ devoluciones' END AS return_group,
       CASE WHEN support_tickets = 0 THEN 'Sin tickets'
            WHEN support_tickets = 1 THEN '1 ticket' ELSE '2+ tickets' END AS support_group,
       COUNT(*) AS customers,
       ROUND(100.0 * AVG(churn_flag), 2) AS churn_rate_pct,
       ROUND(AVG(avg_satisfaction), 2) AS avg_satisfaction
FROM fact_customer_snapshot
GROUP BY return_group, support_group
ORDER BY churn_rate_pct DESC;

-- 8. Clientes prioritarios para recuperación
SELECT s.customer_id, c.customer_segment, c.region, s.rfm_segment,
       s.customer_status, s.days_since_last_order, s.orders,
       ROUND(s.net_revenue_usd, 2) AS lifetime_revenue_usd,
       ROUND(s.annual_revenue_at_risk_usd, 2) AS annual_revenue_at_risk_usd,
       s.support_tickets, ROUND(s.return_rate * 100, 2) AS return_rate_pct
FROM fact_customer_snapshot s
JOIN dim_customers c USING (customer_id)
WHERE s.customer_status IN ('En riesgo', 'Churn')
ORDER BY s.annual_revenue_at_risk_usd DESC
LIMIT 100;
