# Customer Churn & Retention Analytics

Proyecto de Business Intelligence orientado a identificar clientes con riesgo de baja, medir el ingreso expuesto y priorizar acciones de retención. Los datos son simulados y fueron creados únicamente con fines de portfolio.

## Pregunta de negocio

¿Qué segmentos concentran más bajas y cuánto ingreso mensual está en riesgo para poder actuar antes de que el cliente se vaya?

## Stack

- **Python:** generación de datos reproducibles.
- **SQL:** consultas analíticas y validaciones.
- **Power BI:** modelo estrella, medidas DAX y dashboard interactivo.

## Estructura

En GitHub, los archivos se muestran en la raíz para facilitar la carga desde el navegador. Localmente se encuentran organizados en `data/raw`, `sql`, `powerbi` y `scripts`.

## Modelo de datos

| Tabla | Tipo | Descripción |
|---|---|---|
| `dim_customers` | Dimensión | Perfil, segmento, región y antigüedad de clientes. |
| `dim_plans` | Dimensión | Plan contratado y precio mensual. |
| `fact_subscriptions` | Hechos | Estado, fechas, pago mensual y motivo de baja. |
| `fact_support_tickets` | Hechos | Tickets y satisfacción de soporte. |

Relaciones recomendadas en Power BI:

```text
dim_customers (1) ─── (*) fact_subscriptions (*) ─── (1) dim_plans
dim_customers (1) ─── (*) fact_support_tickets
```

## Cómo ejecutarlo

1. Desde la carpeta del proyecto, ejecutar `python3 scripts/generate_data.py`.
2. En Power BI Desktop, obtener datos desde `data/raw` e importar los cuatro CSV.
3. Configurar `customer_id` y `plan_id` como números enteros; las columnas de fecha como fecha.
4. Crear las relaciones del diagrama anterior y luego copiar las medidas de `powerbi/measures.dax`.
5. Seguir el layout de `powerbi/dashboard-guide.md`.

## Hallazgos esperados

El set está diseñado para que aparezcan patrones accionables: mayor riesgo en clientes con tickets recientes, satisfacción baja, baja antigüedad y planes de menor precio. El análisis debe confirmar los patrones con filtros, no asumirlos.

## Capturas sugeridas para LinkedIn o GitHub

1. Página ejecutiva: KPIs, evolución de churn e ingreso en riesgo.
2. Segmentación: churn por región, segmento, plan y antigüedad.
3. Clientes en riesgo: tabla priorizada con señales de riesgo y acción sugerida.
