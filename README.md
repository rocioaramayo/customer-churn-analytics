# Customer Churn Analytics | Retención y valor del cliente

Proyecto de portfolio orientado a detectar pérdida de clientes y traducirla en decisiones de negocio. Esta primera etapa aborda el problema desde **Data Analytics y Business Intelligence** mediante Python, SQL, Power BI y DAX.

El dataset es simulado, reproducible y representa 6.000 clientes de un servicio por suscripción entre enero de 2023 y diciembre de 2025. No contiene información personal real.

## Resumen ejecutivo

| Indicador | Resultado |
|---|---:|
| Clientes analizados | 6.000 |
| Clientes que cancelaron | 1.862 |
| Tasa de churn global | 31,03 % |
| Ingreso anualizado en riesgo | USD 1.441.976,16 |

El objetivo no es mostrar solamente una tasa de churn, sino identificar **qué segmentos se van, cuánto valor económico se pierde y dónde conviene priorizar acciones de retención**.

## Preguntas de negocio

- ¿Cuál es la tasa de churn global y cómo evoluciona mensualmente?
- ¿Qué valor económico se pierde cuando un cliente cancela?
- ¿Qué segmentos presentan mayor riesgo?
- ¿Cómo cambian los resultados según contrato, método de pago, antigüedad, producto y tickets de soporte?

## KPIs

| KPI | Definición |
|---|---|
| Tasa de churn global | Clientes dados de baja / clientes observados |
| Tasa de churn mensual | Bajas del mes / clientes activos al inicio del mes |
| CLV realizado | Cargo mensual × meses activos × (1 − descuento medio) |
| Ingreso anualizado perdido | Suma del cargo mensual de los clientes dados de baja × 12 |

El CLV realizado de los clientes activos está censurado a la fecha de corte: muestra el valor acumulado hasta esa fecha, no todo su valor futuro.

## Entregables

- Base analítica a nivel cliente y evolución mensual de churn.
- Consultas SQL para KPIs y segmentación.
- Libro Excel listo para importar en Power BI, con tablas `Customers` y `MonthlyKPI`.
- Medidas DAX y especificación del dashboard ejecutivo.
- Informe de hallazgos y recomendaciones.

## Estructura principal

```text
customer-churn-analytics/
├── data/
│   ├── raw/
│   └── processed/
├── database/
├── powerbi/
│   ├── Customer_Churn_Etapa1.xlsx
│   ├── dashboard_spec.md
│   └── measures.dax
├── reports/
│   └── insights.md
├── sql/
│   └── analysis.sql
└── src/
    └── generate_stage1.py
```

La raíz conserva además los archivos del primer prototipo relacional (`dim_*`, `fact_*`, `01_schema.sql`, `02_analysis_queries.sql` y `generate_data.py`) para documentar la evolución del proyecto.

## Reproducir el proyecto

```bash
pip install -r requirements.txt
python src/generate_stage1.py
```

El script crea:

- `data/raw/customer_churn_raw.csv`
- `data/processed/customer_churn_analysis.csv`
- `data/processed/monthly_churn_kpis.csv`
- `database/customer_churn.db`
- `reports/insights.md`

## Power BI

La forma más rápida es importar `powerbi/Customer_Churn_Etapa1.xlsx`, que contiene las tablas `Customers` y `MonthlyKPI`. También se pueden importar directamente:

- `data/processed/customer_churn_analysis.csv`
- `data/processed/monthly_churn_kpis.csv`

El archivo `powerbi/measures.dax` contiene las medidas del modelo y `powerbi/dashboard_spec.md` define la página ejecutiva, los filtros y las visualizaciones.

### Diseño del dashboard

- Tarjetas: clientes, bajas, churn global, ingreso anualizado perdido y CLV.
- Línea: evolución mensual de la tasa de churn.
- Barras: churn por contrato y tickets de soporte.
- Barras: ingreso perdido por categoría de servicio.
- Matriz: contrato por método de pago.
- Segmentadores: contrato, método de pago, antigüedad, categoría, segmento y región.

## Próxima etapa: Data Science

La segunda etapa incorporará un modelo predictivo explicable, priorizando **recall** para detectar clientes con riesgo de baja, junto con un score de riesgo y recomendaciones accionables para el equipo de retención.

## Tecnologías

Python · pandas · NumPy · SQL · SQLite · Power BI · DAX
