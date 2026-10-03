"""Genera datos ficticios y reproducibles para el proyecto de churn.

No requiere librerías externas. Ejecutar desde la raíz del proyecto:
python3 scripts/generate_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


RANDOM_SEED = 20261003
CUSTOMER_COUNT = 1800
TODAY = date(2026, 10, 3)
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw"

PLANS = [
    (1, "Basic", "Mensual", 19.0),
    (2, "Standard", "Mensual", 39.0),
    (3, "Premium", "Mensual", 69.0),
    (4, "Business", "Mensual", 119.0),
]
REGIONS = ["AMBA", "Centro", "Cuyo", "NOA", "NEA", "Patagonia"]
SEGMENTS = ["B2C", "Emprendedor", "PyME"]
CHANNELS = ["Orgánico", "Referido", "Paid Social", "Partner", "Evento"]
REASONS = ["Precio", "Bajo uso", "Competencia", "Soporte", "Funcionalidades"]


def weighted_choice(items: list[tuple[str, float]]) -> str:
    labels, weights = zip(*items)
    return random.choices(labels, weights=weights, k=1)[0]


def write_csv(name: str, rows: list[dict]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    random.seed(RANDOM_SEED)
    plans = [
        {"plan_id": plan_id, "plan_name": name, "billing_period": period, "monthly_price": price}
        for plan_id, name, period, price in PLANS
    ]
    customers: list[dict] = []
    subscriptions: list[dict] = []
    tickets: list[dict] = []

    for customer_id in range(1, CUSTOMER_COUNT + 1):
        signup_date = TODAY - timedelta(days=random.randint(20, 1080))
        tenure_months = max(1, (TODAY - signup_date).days // 30)
        segment = weighted_choice([("B2C", 58), ("Emprendedor", 24), ("PyME", 18)])
        region = random.choice(REGIONS)
        acquisition_channel = random.choice(CHANNELS)
        plan_id = random.choices([1, 2, 3, 4], weights=[37, 37, 19, 7], k=1)[0]
        plan = PLANS[plan_id - 1]

        # Riesgo basado en comportamiento plausible: clientes nuevos, B2C y plan Basic
        # tienen una probabilidad ligeramente mayor de cancelar.
        churn_probability = 0.08
        if tenure_months <= 3:
            churn_probability += 0.12
        if segment == "B2C":
            churn_probability += 0.05
        if plan_id == 1:
            churn_probability += 0.04
        if acquisition_channel == "Paid Social":
            churn_probability += 0.03
        churned = random.random() < churn_probability
        churn_date = None
        if churned:
            days_as_customer = (TODAY - signup_date).days
            churn_date = signup_date + timedelta(days=random.randint(15, max(16, days_as_customer)))
            churn_date = min(churn_date, TODAY)

        customer = {
            "customer_id": customer_id,
            "customer_name": f"Cliente {customer_id:04d}",
            "signup_date": signup_date.isoformat(),
            "segment": segment,
            "region": region,
            "acquisition_channel": acquisition_channel,
        }
        customers.append(customer)

        status = "Churned" if churned else "Active"
        subscriptions.append({
            "subscription_id": customer_id,
            "customer_id": customer_id,
            "plan_id": plan_id,
            "start_date": signup_date.isoformat(),
            "end_date": churn_date.isoformat() if churn_date else "",
            "status": status,
            "monthly_revenue": plan[3],
            "churn_reason": random.choice(REASONS) if churned else "",
        })

        # Más tickets y peor satisfacción elevan el riesgo visible para la página de detalle.
        max_tickets = 5 if churned else 3
        ticket_count = random.choices(range(max_tickets + 1), weights=list(range(max_tickets + 1, 0, -1)), k=1)[0]
        for ticket_number in range(ticket_count):
            opened_on = TODAY - timedelta(days=random.randint(1, min(365, (TODAY - signup_date).days)))
            satisfaction = random.choices([1, 2, 3, 4, 5], weights=[16, 21, 30, 23, 10] if churned else [4, 8, 22, 36, 30], k=1)[0]
            tickets.append({
                "ticket_id": f"T-{customer_id:04d}-{ticket_number + 1}",
                "customer_id": customer_id,
                "opened_date": opened_on.isoformat(),
                "category": random.choice(["Facturación", "Soporte técnico", "Onboarding", "Producto"]),
                "resolution_hours": random.randint(2, 96),
                "satisfaction_score": satisfaction,
            })

    write_csv("dim_customers.csv", customers)
    write_csv("dim_plans.csv", plans)
    write_csv("fact_subscriptions.csv", subscriptions)
    write_csv("fact_support_tickets.csv", tickets)
    print(f"Datos generados en {OUTPUT}")
    print(f"Clientes: {len(customers)} | Suscripciones: {len(subscriptions)} | Tickets: {len(tickets)}")


if __name__ == "__main__":
    main()
