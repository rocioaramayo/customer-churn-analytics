from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
N_CUSTOMERS = 8_000
N_PRODUCTS = 120
CUTOFF_DATE = pd.Timestamp("2025-12-31")
CHURN_DAYS = 120
RISK_DAYS = 60
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def date_key(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values).dt.strftime("%Y%m%d").astype(int)


def build_dimensions(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customer_ids = [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
    signup_dates = pd.Series(
        rng.choice(pd.date_range("2023-01-01", "2025-11-30", freq="D"), N_CUSTOMERS)
    )
    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "signup_date": signup_dates,
            "region": rng.choice(["AMBA", "Centro", "Cuyo", "Litoral", "Patagonia", "NOA"], N_CUSTOMERS),
            "customer_segment": rng.choice(["Consumo", "Premium", "PyME"], N_CUSTOMERS, p=[0.72, 0.18, 0.10]),
            "acquisition_channel": rng.choice(
                ["Orgánico", "Paid Social", "Email", "Referidos", "Marketplace"],
                N_CUSTOMERS,
                p=[0.30, 0.25, 0.14, 0.16, 0.15],
            ),
        }
    ).sort_values("customer_id")
    customers["signup_date_key"] = date_key(customers["signup_date"])

    categories = ["Tecnología", "Hogar", "Moda", "Belleza", "Deportes"]
    category_base = {"Tecnología": 185, "Hogar": 92, "Moda": 58, "Belleza": 42, "Deportes": 76}
    product_categories = np.resize(categories, N_PRODUCTS)
    rng.shuffle(product_categories)
    products = pd.DataFrame(
        {
            "product_id": [f"P{i:04d}" for i in range(1, N_PRODUCTS + 1)],
            "product_name": [f"Producto {i:03d}" for i in range(1, N_PRODUCTS + 1)],
            "category": product_categories,
        }
    )
    products["list_price_usd"] = [
        round(max(8, rng.lognormal(np.log(category_base[cat]), 0.38)), 2)
        for cat in products["category"]
    ]
    products["unit_cost_usd"] = (
        products["list_price_usd"] * rng.uniform(0.48, 0.72, N_PRODUCTS)
    ).round(2)

    channels = pd.DataFrame(
        {
            "channel_id": [1, 2, 3],
            "channel": ["Web", "App móvil", "Marketplace"],
            "device_group": ["Desktop / mobile web", "Mobile", "Third party"],
        }
    )

    dates = pd.DataFrame({"date": pd.date_range("2023-01-01", CUTOFF_DATE, freq="D")})
    dates["date_key"] = date_key(dates["date"])
    dates["year"] = dates["date"].dt.year
    dates["quarter"] = "T" + dates["date"].dt.quarter.astype(str)
    dates["month_number"] = dates["date"].dt.month
    dates["month_name"] = dates["date"].dt.month_name(locale="English")
    dates["year_month"] = dates["date"].dt.strftime("%Y-%m")
    dates["month_start"] = dates["date"].dt.to_period("M").dt.to_timestamp()
    return customers.reset_index(drop=True), products, channels, dates


def generate_commerce_facts(
    rng: np.random.Generator,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    order_rows: list[dict[str, object]] = []
    item_rows: list[dict[str, object]] = []
    return_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []
    order_number = item_number = return_number = ticket_number = 0

    category_products = {
        category: frame.reset_index(drop=True)
        for category, frame in products.groupby("category", observed=True)
    }
    payment_methods = ["Tarjeta", "Billetera digital", "Transferencia", "Efectivo"]

    for customer in customers.itertuples(index=False):
        signup = pd.Timestamp(customer.signup_date)
        max_age = max(1, (CUTOFF_DATE - signup).days)
        status_target = rng.choice(["Activo", "En riesgo", "Churn"], p=[0.49, 0.18, 0.33])
        if status_target == "Activo":
            recency = int(rng.integers(0, min(RISK_DAYS, max_age) + 1))
        elif status_target == "En riesgo" and max_age > RISK_DAYS:
            recency = int(rng.integers(RISK_DAYS + 1, min(CHURN_DAYS, max_age) + 1))
        elif max_age > CHURN_DAYS:
            recency = int(rng.integers(CHURN_DAYS + 1, min(620, max_age) + 1))
        else:
            recency = int(rng.integers(0, min(RISK_DAYS, max_age) + 1))

        last_order = CUTOFF_DATE - pd.Timedelta(days=recency)
        if last_order < signup:
            last_order = signup

        tenure_months = max(1, (last_order.to_period("M") - signup.to_period("M")).n + 1)
        segment_boost = {"Consumo": 0.0, "Premium": 0.5, "PyME": 1.0}[customer.customer_segment]
        order_count = int(max(1, rng.poisson(0.55 + tenure_months / 12.0 + segment_boost)))
        if order_count == 1 or last_order == signup:
            order_dates = [last_order]
        else:
            offsets = np.sort(rng.integers(0, (last_order - signup).days + 1, order_count - 1))
            order_dates = [signup + pd.Timedelta(days=int(value)) for value in offsets] + [last_order]

        preferred_category = rng.choice(list(category_products))
        customer_return_propensity = rng.beta(1.2, 24)
        customer_support_propensity = rng.beta(1.4, 20)

        for order_date in sorted(order_dates):
            order_number += 1
            order_id = f"O{order_number:07d}"
            channel_id = int(rng.choice([1, 2, 3], p=[0.48, 0.37, 0.15]))
            payment_method = rng.choice(payment_methods, p=[0.46, 0.28, 0.17, 0.09])
            n_items = int(np.clip(1 + rng.poisson(1.15), 1, 6))
            gross = discount = cost = 0.0
            returned_units = 0

            for _ in range(n_items):
                item_number += 1
                category = preferred_category if rng.random() < 0.56 else rng.choice(list(category_products))
                product = category_products[category].iloc[int(rng.integers(0, len(category_products[category])))]
                quantity = int(rng.choice([1, 2, 3], p=[0.78, 0.18, 0.04]))
                unit_price = float(product["list_price_usd"] * rng.uniform(0.96, 1.04))
                discount_pct = float(np.clip(rng.beta(1.8, 10) * 0.45, 0, 0.35))
                line_gross = unit_price * quantity
                line_discount = line_gross * discount_pct
                line_net = line_gross - line_discount
                line_cost = float(product["unit_cost_usd"] * quantity)
                is_returned = rng.random() < (0.025 + customer_return_propensity + (category == "Moda") * 0.035)
                returned_qty = quantity if is_returned else 0
                returned_units += returned_qty
                gross += line_gross
                discount += line_discount
                cost += line_cost
                item_rows.append(
                    {
                        "order_item_id": f"OI{item_number:08d}",
                        "order_id": order_id,
                        "product_id": product["product_id"],
                        "quantity": quantity,
                        "unit_price_usd": round(unit_price, 2),
                        "discount_pct": round(discount_pct, 4),
                        "net_sales_usd": round(line_net, 2),
                        "unit_cost_total_usd": round(line_cost, 2),
                        "gross_margin_usd": round(line_net - line_cost, 2),
                        "returned_quantity": returned_qty,
                    }
                )
                if is_returned:
                    return_number += 1
                    return_date = min(order_date + pd.Timedelta(days=int(rng.integers(2, 25))), CUTOFF_DATE)
                    return_rows.append(
                        {
                            "return_id": f"R{return_number:07d}",
                            "order_item_id": f"OI{item_number:08d}",
                            "customer_id": customer.customer_id,
                            "return_date": return_date,
                            "return_date_key": int(return_date.strftime("%Y%m%d")),
                            "return_reason": rng.choice(
                                ["Talle / compatibilidad", "Producto defectuoso", "No era lo esperado", "Entrega tardía"],
                                p=[0.31, 0.22, 0.31, 0.16],
                            ),
                            "refund_usd": round(line_net, 2),
                        }
                    )

            shipping_fee = 0.0 if gross - discount >= 80 else round(float(rng.uniform(4.5, 9.5)), 2)
            net_revenue = round(gross - discount + shipping_fee, 2)
            order_rows.append(
                {
                    "order_id": order_id,
                    "customer_id": customer.customer_id,
                    "order_date": order_date,
                    "order_date_key": int(order_date.strftime("%Y%m%d")),
                    "channel_id": channel_id,
                    "payment_method": payment_method,
                    "order_status": "Con devolución" if returned_units else "Completado",
                    "gross_sales_usd": round(gross, 2),
                    "discount_usd": round(discount, 2),
                    "shipping_fee_usd": shipping_fee,
                    "net_revenue_usd": net_revenue,
                    "cost_usd": round(cost, 2),
                    "gross_margin_usd": round(net_revenue - cost, 2),
                }
            )

            ticket_probability = min(0.70, 0.025 + customer_support_propensity + 0.16 * (returned_units > 0))
            if rng.random() < ticket_probability:
                ticket_number += 1
                ticket_date = min(order_date + pd.Timedelta(days=int(rng.integers(0, 18))), CUTOFF_DATE)
                support_rows.append(
                    {
                        "ticket_id": f"T{ticket_number:07d}",
                        "customer_id": customer.customer_id,
                        "order_id": order_id,
                        "ticket_date": ticket_date,
                        "ticket_date_key": int(ticket_date.strftime("%Y%m%d")),
                        "ticket_category": rng.choice(
                            ["Entrega", "Pago", "Producto", "Devolución", "Cuenta"],
                            p=[0.30, 0.13, 0.25, 0.22, 0.10],
                        ),
                        "resolution_hours": round(float(np.clip(rng.lognormal(2.5, 0.7), 1, 120)), 1),
                        "satisfaction_score": int(rng.choice([1, 2, 3, 4, 5], p=[0.07, 0.11, 0.21, 0.34, 0.27])),
                    }
                )

    return (
        pd.DataFrame(order_rows),
        pd.DataFrame(item_rows),
        pd.DataFrame(return_rows),
        pd.DataFrame(support_rows),
    )


def build_customer_snapshot(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    returns: pd.DataFrame,
    support: pd.DataFrame,
) -> pd.DataFrame:
    order_summary = orders.groupby("customer_id").agg(
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
        orders=("order_id", "nunique"),
        net_revenue_usd=("net_revenue_usd", "sum"),
        gross_margin_usd=("gross_margin_usd", "sum"),
        avg_order_value_usd=("net_revenue_usd", "mean"),
    )
    item_customer = items.merge(orders[["order_id", "customer_id"]], on="order_id", how="left")
    item_summary = item_customer.groupby("customer_id").agg(items=("quantity", "sum"))
    return_summary = returns.groupby("customer_id").agg(
        returns=("return_id", "nunique"), refunds_usd=("refund_usd", "sum")
    ) if not returns.empty else pd.DataFrame()
    support_summary = support.groupby("customer_id").agg(
        support_tickets=("ticket_id", "nunique"),
        avg_satisfaction=("satisfaction_score", "mean"),
    ) if not support.empty else pd.DataFrame()

    snapshot = customers[["customer_id"]].merge(order_summary, on="customer_id", how="left").merge(
        item_summary, on="customer_id", how="left"
    )
    snapshot = snapshot.merge(return_summary, on="customer_id", how="left").merge(
        support_summary, on="customer_id", how="left"
    )
    snapshot[["returns", "refunds_usd", "support_tickets"]] = snapshot[
        ["returns", "refunds_usd", "support_tickets"]
    ].fillna(0)
    snapshot["avg_satisfaction"] = snapshot["avg_satisfaction"].fillna(5)
    snapshot["days_since_last_order"] = (CUTOFF_DATE - snapshot["last_order_date"]).dt.days
    snapshot["customer_status"] = np.select(
        [snapshot["days_since_last_order"] > CHURN_DAYS, snapshot["days_since_last_order"] > RISK_DAYS],
        ["Churn", "En riesgo"],
        default="Activo",
    )
    snapshot["churn_flag"] = (snapshot["customer_status"] == "Churn").astype(int)
    snapshot["at_risk_flag"] = (snapshot["customer_status"] == "En riesgo").astype(int)
    snapshot["repeat_customer_flag"] = (snapshot["orders"] >= 2).astype(int)
    snapshot["return_rate"] = (snapshot["returns"] / snapshot["orders"]).clip(0, 1).round(4)
    snapshot["purchase_frequency_per_year"] = (
        snapshot["orders"] / ((snapshot["last_order_date"] - snapshot["first_order_date"]).dt.days.add(30) / 365)
    ).round(2)
    monthly_value = snapshot["net_revenue_usd"] / (
        ((snapshot["last_order_date"] - snapshot["first_order_date"]).dt.days / 30).clip(lower=1)
    )
    snapshot["annual_revenue_at_risk_usd"] = np.where(
        snapshot["customer_status"].isin(["Churn", "En riesgo"]), monthly_value * 12, 0
    ).round(2)
    snapshot["snapshot_date"] = CUTOFF_DATE
    snapshot["snapshot_date_key"] = int(CUTOFF_DATE.strftime("%Y%m%d"))

    snapshot["recency_score"] = pd.qcut(
        snapshot["days_since_last_order"].rank(method="first", ascending=False), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    snapshot["frequency_score"] = pd.qcut(
        snapshot["orders"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    snapshot["monetary_score"] = pd.qcut(
        snapshot["net_revenue_usd"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    snapshot["rfm_segment"] = np.select(
        [
            (snapshot["recency_score"] >= 4) & (snapshot["frequency_score"] >= 4),
            (snapshot["recency_score"] <= 2) & (snapshot["frequency_score"] >= 3),
            snapshot["recency_score"] <= 2,
            snapshot["frequency_score"] <= 2,
        ],
        ["Champions", "Leales en riesgo", "Dormidos", "Ocasionales"],
        default="Potenciales leales",
    )
    return snapshot


def build_monthly_kpis(orders: pd.DataFrame, snapshot: pd.DataFrame) -> pd.DataFrame:
    monthly_orders = orders.assign(month=orders["order_date"].dt.to_period("M").dt.to_timestamp()).groupby("month").agg(
        orders=("order_id", "nunique"),
        active_customers=("customer_id", "nunique"),
        net_revenue_usd=("net_revenue_usd", "sum"),
        gross_margin_usd=("gross_margin_usd", "sum"),
        avg_order_value_usd=("net_revenue_usd", "mean"),
    ).reset_index()
    first_orders = snapshot.groupby(snapshot["first_order_date"].dt.to_period("M").dt.to_timestamp()).size().rename("new_customers")
    churn_events = snapshot.loc[snapshot["churn_flag"].eq(1)].copy()
    churn_events["churn_effective_month"] = (
        churn_events["last_order_date"] + pd.Timedelta(days=CHURN_DAYS + 1)
    ).dt.to_period("M").dt.to_timestamp()
    churn_counts = churn_events.groupby("churn_effective_month").size().rename("churned_customers")

    result = monthly_orders.merge(first_orders, left_on="month", right_index=True, how="left").merge(
        churn_counts, left_on="month", right_index=True, how="left"
    )
    result[["new_customers", "churned_customers"]] = result[["new_customers", "churned_customers"]].fillna(0).astype(int)
    result["churn_rate"] = (result["churned_customers"] / result["active_customers"].shift(1)).fillna(0).round(4)
    result["month_key"] = date_key(result["month"])
    return result


def save_outputs(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    channels: pd.DataFrame,
    dates: pd.DataFrame,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    returns: pd.DataFrame,
    support: pd.DataFrame,
    snapshot: pd.DataFrame,
    monthly: pd.DataFrame,
) -> None:
    processed = PROJECT_ROOT / "data" / "processed"
    raw = PROJECT_ROOT / "data" / "raw"
    database = PROJECT_ROOT / "database"
    reports = PROJECT_ROOT / "reports"
    for directory in (processed, raw, database, reports):
        directory.mkdir(parents=True, exist_ok=True)

    customers.to_csv(processed / "dim_customers.csv", index=False, date_format="%Y-%m-%d")
    products.to_csv(processed / "dim_products.csv", index=False)
    channels.to_csv(processed / "dim_channels.csv", index=False)
    dates.to_csv(processed / "dim_date.csv", index=False, date_format="%Y-%m-%d")
    orders.to_csv(processed / "fact_orders.csv", index=False, date_format="%Y-%m-%d")
    items.to_csv(processed / "fact_order_items.csv", index=False)
    returns.to_csv(processed / "fact_returns.csv", index=False, date_format="%Y-%m-%d")
    support.to_csv(processed / "fact_support.csv", index=False, date_format="%Y-%m-%d")
    snapshot.to_csv(processed / "fact_customer_snapshot.csv", index=False, date_format="%Y-%m-%d")
    monthly.to_csv(processed / "fact_monthly_kpis.csv", index=False, date_format="%Y-%m-%d")
    orders.to_csv(raw / "orders_raw.csv", index=False, date_format="%Y-%m-%d")

    tables = {
        "dim_customers": customers,
        "dim_products": products,
        "dim_channels": channels,
        "dim_date": dates,
        "fact_orders": orders,
        "fact_order_items": items,
        "fact_returns": returns,
        "fact_support": support,
        "fact_customer_snapshot": snapshot,
        "fact_monthly_kpis": monthly,
    }
    with sqlite3.connect(database / "ecommerce_churn.db") as connection:
        for name, frame in tables.items():
            frame.to_sql(name, connection, if_exists="replace", index=False)

    summary = {
        "cutoff_date": str(CUTOFF_DATE.date()),
        "churn_definition_days": CHURN_DAYS,
        "customers": int(len(customers)),
        "orders": int(len(orders)),
        "order_items": int(len(items)),
        "churned_customers": int(snapshot["churn_flag"].sum()),
        "global_churn_rate": round(float(snapshot["churn_flag"].mean()), 4),
        "repeat_purchase_rate": round(float(snapshot["repeat_customer_flag"].mean()), 4),
        "net_revenue_usd": round(float(orders["net_revenue_usd"].sum()), 2),
        "annual_revenue_at_risk_usd": round(float(snapshot["annual_revenue_at_risk_usd"].sum()), 2),
    }
    (processed / "project_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    insights = f"""# Hallazgos ejecutivos\n\nDatos simulados de e-commerce. Fecha de corte: {CUTOFF_DATE.date()}.\n\n- **{len(customers):,} clientes** y **{len(orders):,} pedidos** analizados.\n- Churn definido como más de **{CHURN_DAYS} días sin comprar**.\n- Tasa de churn global: **{snapshot['churn_flag'].mean():.1%}**.\n- Tasa de recompra: **{snapshot['repeat_customer_flag'].mean():.1%}**.\n- Ingreso neto observado: **USD {orders['net_revenue_usd'].sum():,.0f}**.\n- Ingreso anual estimado en riesgo: **USD {snapshot['annual_revenue_at_risk_usd'].sum():,.0f}**.\n\nLa segmentación RFM permite distinguir champions, potenciales leales, clientes ocasionales, dormidos y leales en riesgo.\n"""
    (reports / "insights.md").write_text(insights, encoding="utf-8")


def main() -> None:
    rng = np.random.default_rng(SEED)
    customers, products, channels, dates = build_dimensions(rng)
    orders, items, returns, support = generate_commerce_facts(rng, customers, products)
    for frame, columns in [
        (orders, ["order_date"]),
        (returns, ["return_date"]),
        (support, ["ticket_date"]),
    ]:
        for column in columns:
            frame[column] = pd.to_datetime(frame[column])
    snapshot = build_customer_snapshot(customers, orders, items, returns, support)
    monthly = build_monthly_kpis(orders, snapshot)
    save_outputs(customers, products, channels, dates, orders, items, returns, support, snapshot, monthly)
    print(
        f"Generated {len(customers):,} customers, {len(orders):,} orders and {len(items):,} items | "
        f"churn {snapshot['churn_flag'].mean():.1%}"
    )


if __name__ == "__main__":
    main()
