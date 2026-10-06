# Diccionario de datos

## DimCustomers

| Campo | Descripción |
|---|---|
| `customer_id` | Identificador único del cliente. |
| `signup_date` | Fecha de alta en el e-commerce. |
| `signup_date_key` | Clave `YYYYMMDD` para el calendario. |
| `region` | Región comercial. |
| `customer_segment` | Segmento Consumo, Premium o PyME. |
| `acquisition_channel` | Canal que originó la relación con el cliente. |

## DimProducts

| Campo | Descripción |
|---|---|
| `product_id` | Identificador único del producto. |
| `product_name` | Nombre simulado. |
| `category` | Tecnología, Hogar, Moda, Belleza o Deportes. |
| `list_price_usd` | Precio de lista. |
| `unit_cost_usd` | Costo unitario estimado. |

## FactOrders

Una fila por pedido. Contiene fecha, cliente, canal, método de pago, ventas brutas, descuento, envío, facturación neta, costo y margen.

## FactOrderItems

Una fila por producto dentro de un pedido. Permite analizar unidades, precio, descuento, venta neta, costo, margen y devoluciones por categoría.

## FactReturns

Una fila por ítem devuelto. Registra cliente, fecha, motivo y reintegro.

## FactSupport

Una fila por ticket. Registra categoría, horas de resolución y satisfacción.

## FactCustomerSnapshot

Una fila por cliente a la fecha de corte.

| Campo | Descripción |
|---|---|
| `days_since_last_order` | Recencia en días. |
| `customer_status` | Activo, En riesgo o Churn. |
| `churn_flag` | 1 cuando supera 120 días sin comprar. |
| `repeat_customer_flag` | 1 cuando realizó al menos dos pedidos. |
| `orders` | Pedidos históricos. |
| `avg_order_value_usd` | Ticket histórico medio. |
| `net_revenue_usd` | Ingreso neto acumulado del cliente. |
| `gross_margin_usd` | Margen bruto acumulado. |
| `annual_revenue_at_risk_usd` | Valor anual estimado en riesgo. |
| `return_rate` | Devoluciones sobre pedidos. |
| `purchase_frequency_per_year` | Pedidos anualizados. |
| `recency_score` | Puntaje RFM de recencia, de 1 a 5. |
| `frequency_score` | Puntaje RFM de frecuencia, de 1 a 5. |
| `monetary_score` | Puntaje RFM monetario, de 1 a 5. |
| `rfm_segment` | Segmento comercial derivado de los puntajes RFM. |

## FactMonthlyKPI

Una fila por mes con clientes activos, altas, churn, pedidos, facturación, margen y ticket promedio.
