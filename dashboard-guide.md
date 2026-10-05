# Guía de dashboard en Power BI

## Página 1 — Resumen ejecutivo

- Tarjetas: **Clientes Activos**, **Tasa de Churn**, **MRR Activo**, **MRR Perdido** y **Clientes Riesgo Alto**.
- Gráfico de columnas: tasa de churn por segmento.
- Barras: MRR perdido por plan.
- Dona: clientes activos vs. churned.
- Segmentadores: región, segmento, canal de adquisición y plan.

## Página 2 — Segmentación y causas

- Barras horizontales: churn por región.
- Matriz: segmento × plan con total clientes, churn y MRR perdido.
- Barras: churn por motivo de baja.
- Dispersión: satisfacción promedio vs. cantidad de tickets, usando el tamaño para MRR.

## Página 3 — Clientes en riesgo

Crear una tabla con cliente, plan, MRR, cantidad de tickets y satisfacción. Agregar una columna calculada para señal de riesgo:

```DAX
Nivel de Riesgo =
VAR Tickets = CALCULATE(COUNTROWS(fact_support_tickets))
VAR Satisfaccion = CALCULATE(AVERAGE(fact_support_tickets[satisfaction_score]))
RETURN
    SWITCH(
        TRUE(),
        fact_subscriptions[status] <> "Active", "Sin acción",
        Tickets >= 3 && Satisfaccion <= 2.5, "Alto",
        Tickets >= 2 || Satisfaccion <= 3, "Medio",
        "Bajo"
    )
```

Aplicar formato condicional: rojo para Alto, ámbar para Medio y verde para Bajo. La acción sugerida para los casos de riesgo alto es contacto proactivo, revisión de tickets abiertos y propuesta de acompañamiento u oferta de retención.

## Diseño recomendado

Usar fondo claro, azul oscuro para encabezados, turquesa para métricas positivas y rojo suave solo para churn/riesgo. Mantener tres a cinco KPI por página y títulos que respondan una pregunta de negocio.
