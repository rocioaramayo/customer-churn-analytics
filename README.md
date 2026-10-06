# E-commerce Customer Retention Analytics

Proyecto de portfolio que analiza la retención y pérdida de clientes de un e-commerce mediante **Python, SQL, modelado estrella, Power BI y DAX**.

El dataset es simulado y reproducible. Representa clientes, pedidos, productos, devoluciones y contactos con soporte entre enero de 2023 y diciembre de 2025. No contiene información personal real.

## Problema de negocio

En e-commerce no existe una cancelación explícita. Para este caso se utiliza una regla observable y configurable:

- **Activo:** compró en los últimos 60 días.
- **En riesgo:** lleva entre 61 y 120 días sin comprar.
- **Churn:** lleva más de 120 días sin comprar.

La fecha de corte es **2025-12-31**. El objetivo es detectar clientes que dejan de comprar, cuantificar el ingreso en riesgo y priorizar campañas de recuperación.

## Resumen ejecutivo

| Indicador | Resultado |
|---|---:|
| Clientes | 8.000 |
| Pedidos | 17.620 |
| Ítems vendidos | 37.851 |
| Clientes churn | 2.425 |
| Tasa de churn | 30,3 % |
| Tasa de recompra | 55,4 % |
| Facturación neta observada | USD 4.554.220 |
| Ingreso anual estimado en riesgo | USD 9.761.234 |

## Preguntas respondidas

- ¿Cuál es la tasa de churn y de recompra?
- ¿Cuánto ingreso anual se encuentra en riesgo?
- ¿Qué segmentos RFM necesitan una campaña de recuperación?
- ¿Qué categorías, canales y regiones generan más valor?
- ¿Existe relación entre devoluciones, soporte y churn?
- ¿Qué clientes conviene priorizar según valor e inactividad?

## Modelo de datos

El proyecto utiliza un modelo estrella con varias tablas de hechos:

```text
DimCustomers ─────┬── FactOrders ─── FactOrderItems ─── DimProducts
DimChannels ──────┤        │
DimDate ──────────┘        ├── FactReturns
                           └── FactSupport

DimCustomers ───────── FactCustomerSnapshot
DimDate ─────────────── FactMonthlyKPI
```

### Dimensiones

- `dim_customers`: región, segmento y canal de adquisición.
- `dim_products`: producto, categoría, precio y costo.
- `dim_channels`: web, aplicación móvil y marketplace.
- `dim_date`: calendario completo para inteligencia de tiempo.

### Hechos

- `fact_orders`: cabecera de pedidos, facturación, descuentos, costos y margen.
- `fact_order_items`: productos y cantidades de cada pedido.
- `fact_returns`: devoluciones, motivos y reembolsos.
- `fact_support`: tickets, resolución y satisfacción.
- `fact_customer_snapshot`: estado de retención, RFM, CLV observado e ingreso en riesgo.
- `fact_monthly_kpis`: evolución mensual del negocio y del churn.

## KPIs principales

- Clientes activos, en riesgo y churn.
- Tasa de churn y tasa de recompra.
- Facturación neta, margen bruto y ticket promedio.
- CLV realizado.
- Ingreso anual estimado en riesgo.
- Días desde la última compra.
- Frecuencia de compra y segmentación RFM.
- Tasa de devoluciones y volumen de soporte.

## Estructura

```text
customer-churn-analytics/
├── data/
│   ├── raw/
│   └── processed/
├── database/
│   └── ecommerce_churn.db
├── docs/
│   └── data_dictionary.md
├── powerbi/
│   ├── dashboard_spec.md
│   └── measures.dax
├── reports/
│   └── insights.md
├── sql/
│   └── analysis.sql
├── src/
│   └── generate_ecommerce.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Reproducir el proyecto

```bash
pip install -r requirements.txt
python src/generate_ecommerce.py
```

Los archivos listos para Power BI se generan en `data/processed/`. La base SQLite se genera en `database/ecommerce_churn.db`.

## Construir el Power BI

Seguir [`powerbi/dashboard_spec.md`](powerbi/dashboard_spec.md). Allí están:

1. Los CSV que se deben importar.
2. Los nombres recomendados para las tablas.
3. Todas las relaciones del modelo.
4. Las páginas y visualizaciones sugeridas.
5. El formato de las medidas.

Las medidas listas para copiar están en [`powerbi/measures.dax`](powerbi/measures.dax).

El detalle de tablas y campos está en [`docs/data_dictionary.md`](docs/data_dictionary.md).

## SQL

[`sql/analysis.sql`](sql/analysis.sql) incluye consultas para KPIs ejecutivos, evolución mensual, RFM, categorías, devoluciones, soporte y una lista priorizada de clientes para recuperación.

## Tecnologías

Python · pandas · NumPy · SQL · SQLite · Power BI · DAX · Modelado estrella · RFM

## Próxima etapa

Entrenar un modelo predictivo explicable que asigne un score de riesgo de churn y priorice clientes según probabilidad de abandono y valor económico.
