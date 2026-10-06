# Guía para construir el dashboard en Power BI

## 1. Importar los CSV

Desde **Obtener datos → Texto/CSV**, importar desde `data/processed/`:

- `dim_customers.csv` → `DimCustomers`
- `dim_products.csv` → `DimProducts`
- `dim_channels.csv` → `DimChannels`
- `dim_date.csv` → `DimDate`
- `fact_orders.csv` → `FactOrders`
- `fact_order_items.csv` → `FactOrderItems`
- `fact_returns.csv` → `FactReturns`
- `fact_support.csv` → `FactSupport`
- `fact_customer_snapshot.csv` → `FactCustomerSnapshot`
- `fact_monthly_kpis.csv` → `FactMonthlyKPI`

## 2. Revisar tipos

- Claves terminadas en `_key`: número entero.
- Fechas: tipo Fecha.
- Importes y porcentajes: número decimal.
- Identificadores: texto.

## 3. Crear las relaciones

Todas deben ser **1 a muchos**, con filtro en una sola dirección desde la dimensión:

| Desde (1) | Hacia (*) |
|---|---|
| `DimCustomers[customer_id]` | `FactOrders[customer_id]` |
| `DimCustomers[customer_id]` | `FactCustomerSnapshot[customer_id]` |
| `DimCustomers[customer_id]` | `FactReturns[customer_id]` |
| `DimCustomers[customer_id]` | `FactSupport[customer_id]` |
| `DimChannels[channel_id]` | `FactOrders[channel_id]` |
| `DimDate[date_key]` | `FactOrders[order_date_key]` |
| `DimDate[date_key]` | `FactReturns[return_date_key]` |
| `DimDate[date_key]` | `FactSupport[ticket_date_key]` |
| `DimDate[date_key]` | `FactMonthlyKPI[month_key]` |
| `FactOrders[order_id]` | `FactOrderItems[order_id]` |
| `DimProducts[product_id]` | `FactOrderItems[product_id]` |

No relaciones directamente las tablas de hechos entre sí, salvo `FactOrders` → `FactOrderItems`.

## 4. Medidas

Crear una tabla vacía llamada `_Medidas` y copiar las medidas de `powerbi/measures.dax`.

- Tasas y variaciones: porcentaje con un decimal.
- Moneda: USD con cero o dos decimales.
- Clientes, pedidos y unidades: entero.

## 5. Dashboard recomendado

### Página 1 — Resumen ejecutivo

Tarjetas: facturación neta, margen bruto, pedidos, ticket promedio, tasa de recompra, tasa de churn e ingreso anual en riesgo.

Visuales:

- Línea: facturación neta por `DimDate[year_month]`.
- Columnas: clientes por `customer_status`.
- Barras: ingreso anual en riesgo por `rfm_segment`.
- Barras: facturación y margen por categoría.
- Segmentadores: año, región, canal, segmento y categoría.

### Página 2 — Retención y RFM

- Matriz: `rfm_segment` con clientes, churn, CLV e ingreso en riesgo.
- Dispersión: frecuencia de compra vs. facturación por cliente.
- Barras: churn por canal de adquisición.
- Tabla operativa: clientes en riesgo ordenados por ingreso en riesgo.

### Página 3 — Experiencia del cliente

- Tasa de devolución por categoría.
- Churn según cantidad de devoluciones.
- Churn según tickets de soporte.
- Satisfacción promedio por categoría de ticket.

## 6. Definición de negocio

- **Activo:** compró en los últimos 60 días.
- **En riesgo:** lleva entre 61 y 120 días sin comprar.
- **Churn:** lleva más de 120 días sin comprar.

La fecha de corte es 2025-12-31. Esta definición configurable debe aparecer en el reporte.
