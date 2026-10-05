# Especificación del dashboard

## Página 1: Retención ejecutiva

### KPIs

- Tasa de churn global
- Clientes dados de baja
- CLV realizado promedio de bajas
- CLV realizado promedio de activos
- Ingreso anualizado perdido

### Visualizaciones

1. Línea: tasa de churn mensual por mes.
2. Barras: tasa de churn por tipo de contrato.
3. Barras: ingreso anualizado perdido por categoría de servicio.
4. Matriz: contrato × método de pago con clientes, bajas y churn.
5. Barras: churn según tickets de soporte en los últimos 90 días.

### Filtros

- Fecha
- Tipo de contrato
- Método de pago
- Antigüedad
- Categoría de servicio
- Segmento de cliente
- Región

## Modelo

- `Customers`: una fila por cliente.
- `MonthlyKPI`: una fila por mes.
- Crear una tabla calendario y relacionarla con `MonthlyKPI[month]`.
- No relacionar directamente ambas tablas de hechos; utilizar dimensiones compartidas si se amplía el modelo.

## Formatos

- Churn: porcentaje con un decimal.
- CLV e ingreso perdido: USD sin decimales.
- Conteos: entero con separador de miles.

