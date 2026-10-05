from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
N_CUSTOMERS = 6000
OBSERVATION_END = pd.Timestamp("2025-12-31")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sigmoid(value: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-value))


def month_difference(later: pd.Series, earlier: pd.Series) -> pd.Series:
    return (
        (later.dt.year - earlier.dt.year) * 12
        + later.dt.month
        - earlier.dt.month
        + 1
    ).clip(lower=1)


def generate_customers() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    signup_pool = pd.date_range("2022-01-01", "2025-11-30", freq="D")
    signup_date = pd.Series(rng.choice(signup_pool, N_CUSTOMERS)).sort_values().reset_index(drop=True)

    contract_type = rng.choice(
        ["Mes a mes", "Anual", "Dos años"], N_CUSTOMERS, p=[0.57, 0.27, 0.16]
    )
    payment_method = rng.choice(
        ["Tarjeta automática", "Débito automático", "Transferencia", "Cheque electrónico"],
        N_CUSTOMERS,
        p=[0.31, 0.28, 0.19, 0.22],
    )
    service_category = rng.choice(
        ["Internet fibra", "Internet estándar", "Streaming", "Telefonía móvil"],
        N_CUSTOMERS,
        p=[0.31, 0.27, 0.18, 0.24],
    )
    region = rng.choice(["AMBA", "Centro", "Cuyo", "Litoral", "Patagonia", "NOA"], N_CUSTOMERS)
    customer_segment = rng.choice(["Hogar", "Profesional", "PyME"], N_CUSTOMERS, p=[0.66, 0.21, 0.13])
    auto_pay = np.isin(payment_method, ["Tarjeta automática", "Débito automático"])

    base_charge = pd.Series(service_category).map(
        {
            "Internet fibra": 78,
            "Internet estándar": 49,
            "Streaming": 29,
            "Telefonía móvil": 42,
        }
    ).to_numpy()
    segment_addon = pd.Series(customer_segment).map({"Hogar": 0, "Profesional": 18, "PyME": 55}).to_numpy()
    monthly_charge = np.maximum(18, rng.normal(base_charge + segment_addon, 11)).round(2)
    avg_discount_pct = np.clip(rng.beta(2, 10, N_CUSTOMERS) * 0.35, 0, 0.25).round(4)

    service_friction = rng.choice([0, 1], N_CUSTOMERS, p=[0.76, 0.24])
    support_tickets_90d = np.clip(rng.poisson(0.65 + 1.9 * service_friction), 0, 8)
    late_payments_12m = np.clip(
        rng.poisson(0.35 + 0.85 * (payment_method == "Cheque electrónico")), 0, 7
    )
    satisfaction_score = np.clip(
        np.rint(rng.normal(4.35 - 0.55 * support_tickets_90d - 0.25 * late_payments_12m, 0.85)),
        1,
        5,
    ).astype(int)

    hazard_score = (
        -5.35
        + 1.18 * (contract_type == "Mes a mes")
        - 0.42 * (contract_type == "Anual")
        - 0.92 * (contract_type == "Dos años")
        + 0.52 * (payment_method == "Cheque electrónico")
        + 0.29 * support_tickets_90d
        + 0.20 * late_payments_12m
        + 0.45 * (satisfaction_score <= 2)
        - 0.24 * auto_pay
        + 0.13 * (monthly_charge > 90)
    )
    monthly_hazard = np.clip(sigmoid(hazard_score), 0.003, 0.28)
    months_until_event = rng.geometric(monthly_hazard)

    possible_tenure = (
        (OBSERVATION_END.year - signup_date.dt.year) * 12
        + OBSERVATION_END.month
        - signup_date.dt.month
        + 1
    )
    churn_flag = months_until_event <= possible_tenure

    signup_month_start = signup_date.dt.to_period("M").dt.to_timestamp()
    churn_month_start = pd.Series(
        [
            start + pd.DateOffset(months=int(months - 1))
            for start, months in zip(signup_month_start, months_until_event, strict=True)
        ]
    )
    churn_day = pd.to_timedelta(rng.integers(0, 27, N_CUSTOMERS), unit="D")
    churn_date = (churn_month_start + churn_day).where(churn_flag, pd.NaT)
    churn_date = churn_date.where(churn_date <= OBSERVATION_END, pd.NaT)
    churn_flag = churn_date.notna().to_numpy()

    end_date = churn_date.fillna(OBSERVATION_END)
    tenure_months = month_difference(end_date, signup_date)
    clv_realized = (monthly_charge * tenure_months * (1 - avg_discount_pct)).round(2)
    annualized_revenue_lost = np.where(churn_flag, monthly_charge * 12, 0).round(2)

    df = pd.DataFrame(
        {
            "customer_id": [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
            "signup_date": signup_date,
            "churn_date": churn_date,
            "snapshot_date": OBSERVATION_END,
            "churn_flag": churn_flag.astype(int),
            "status": np.where(churn_flag, "Baja", "Activo"),
            "tenure_months": tenure_months.astype(int),
            "tenure_band": pd.cut(
                tenure_months,
                bins=[0, 3, 6, 12, 24, 999],
                labels=["0-3 meses", "4-6 meses", "7-12 meses", "13-24 meses", "25+ meses"],
            ).astype(str),
            "contract_type": contract_type,
            "payment_method": payment_method,
            "service_category": service_category,
            "region": region,
            "customer_segment": customer_segment,
            "monthly_charge_usd": monthly_charge,
            "avg_discount_pct": avg_discount_pct,
            "support_tickets_90d": support_tickets_90d,
            "late_payments_12m": late_payments_12m,
            "auto_pay": np.where(auto_pay, "Sí", "No"),
            "satisfaction_score": satisfaction_score,
            "clv_realized_usd": clv_realized,
            "annualized_revenue_lost_usd": annualized_revenue_lost,
        }
    )
    return df.sort_values("customer_id").reset_index(drop=True)


def build_monthly_kpis(customers: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for month_start in pd.date_range("2023-01-01", "2025-12-01", freq="MS"):
        month_end = month_start + pd.offsets.MonthEnd(0)
        active_start_mask = (customers["signup_date"] < month_start) & (
            customers["churn_date"].isna() | (customers["churn_date"] >= month_start)
        )
        new_mask = customers["signup_date"].between(month_start, month_end)
        churn_mask = customers["churn_date"].between(month_start, month_end)

        active_start = int(active_start_mask.sum())
        new_customers = int(new_mask.sum())
        churned_customers = int(churn_mask.sum())
        active_end = active_start + new_customers - churned_customers
        churn_rate = churned_customers / active_start if active_start else np.nan
        monthly_revenue_lost = float(customers.loc[churn_mask, "monthly_charge_usd"].sum())

        rows.append(
            {
                "month": month_start,
                "active_start": active_start,
                "new_customers": new_customers,
                "churned_customers": churned_customers,
                "active_end": active_end,
                "churn_rate": round(churn_rate, 6),
                "monthly_recurring_revenue_lost_usd": round(monthly_revenue_lost, 2),
                "annualized_revenue_lost_usd": round(monthly_revenue_lost * 12, 2),
            }
        )
    return pd.DataFrame(rows)


def summarize_by(customers: pd.DataFrame, column: str) -> pd.DataFrame:
    return (
        customers.groupby(column, observed=True)
        .agg(
            customers=("customer_id", "count"),
            churned_customers=("churn_flag", "sum"),
            churn_rate=("churn_flag", "mean"),
            avg_monthly_charge_usd=("monthly_charge_usd", "mean"),
            avg_clv_realized_usd=("clv_realized_usd", "mean"),
            annualized_revenue_lost_usd=("annualized_revenue_lost_usd", "sum"),
        )
        .reset_index()
        .sort_values("churn_rate", ascending=False)
    )


def write_insights(customers: pd.DataFrame, monthly: pd.DataFrame) -> None:
    churn_rate = customers["churn_flag"].mean()
    lost_arr = customers["annualized_revenue_lost_usd"].sum()
    clv_by_status = customers.groupby("status")["clv_realized_usd"].mean()
    contract = summarize_by(customers, "contract_type").iloc[0]
    payment = summarize_by(customers, "payment_method").iloc[0]
    tickets_table = summarize_by(customers, "support_tickets_90d")
    tickets = tickets_table.loc[tickets_table["customers"] >= 25].iloc[0]
    peak_month = monthly.loc[monthly["churn_rate"].idxmax()]

    report = f"""# Hallazgos iniciales

Datos simulados. Fecha de corte: {OBSERVATION_END.date()}.

## Resumen ejecutivo

- La tasa de churn global es **{churn_rate:.1%}**.
- El ingreso anualizado perdido por las bajas observadas es **USD {lost_arr:,.0f}**.
- El CLV realizado promedio es **USD {clv_by_status.get('Baja', 0):,.0f}** para clientes dados de baja y **USD {clv_by_status.get('Activo', 0):,.0f}** para clientes activos.
- El tipo de contrato con mayor churn es **{contract['contract_type']}** ({contract['churn_rate']:.1%}).
- El método de pago con mayor churn es **{payment['payment_method']}** ({payment['churn_rate']:.1%}).
- La mayor tasa mensual se observa en **{peak_month['month']:%Y-%m}** ({peak_month['churn_rate']:.1%}).

## Lectura de soporte

El grupo con **{int(tickets['support_tickets_90d'])} tickets en los últimos 90 días** registra una tasa de churn de **{tickets['churn_rate']:.1%}**. La relación completa debe mostrarse en el dashboard para evitar conclusiones basadas en un único grupo pequeño.

## Limitación

El CLV realizado de clientes activos está censurado en la fecha de corte. En la segunda etapa se puede incorporar un CLV proyectado y un score de riesgo.
"""
    (PROJECT_ROOT / "reports" / "insights.md").write_text(report, encoding="utf-8")


def save_outputs(customers: pd.DataFrame, monthly: pd.DataFrame) -> None:
    raw_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    db_dir = PROJECT_ROOT / "database"
    report_dir = PROJECT_ROOT / "reports"
    for directory in (raw_dir, processed_dir, db_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    raw_columns = [
        "customer_id",
        "signup_date",
        "churn_date",
        "contract_type",
        "payment_method",
        "service_category",
        "region",
        "customer_segment",
        "monthly_charge_usd",
        "avg_discount_pct",
        "support_tickets_90d",
        "late_payments_12m",
        "auto_pay",
        "satisfaction_score",
    ]
    customers[raw_columns].to_csv(raw_dir / "customer_churn_raw.csv", index=False, date_format="%Y-%m-%d")
    customers.to_csv(processed_dir / "customer_churn_analysis.csv", index=False, date_format="%Y-%m-%d")
    monthly.to_csv(processed_dir / "monthly_churn_kpis.csv", index=False, date_format="%Y-%m-%d")

    with sqlite3.connect(db_dir / "customer_churn.db") as connection:
        customers.to_sql("customers", connection, if_exists="replace", index=False)
        monthly.to_sql("monthly_churn_kpis", connection, if_exists="replace", index=False)
        for dimension in ["contract_type", "payment_method", "tenure_band", "service_category", "customer_segment"]:
            summarize_by(customers, dimension).to_sql(
                f"churn_by_{dimension}", connection, if_exists="replace", index=False
            )

    summary = {
        "customers": int(len(customers)),
        "churned_customers": int(customers["churn_flag"].sum()),
        "global_churn_rate": round(float(customers["churn_flag"].mean()), 6),
        "annualized_revenue_lost_usd": round(float(customers["annualized_revenue_lost_usd"].sum()), 2),
    }
    (processed_dir / "stage1_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> None:
    customers = generate_customers()
    monthly = build_monthly_kpis(customers)
    save_outputs(customers, monthly)
    write_insights(customers, monthly)
    print(
        f"Generated {len(customers):,} customers | "
        f"global churn {customers['churn_flag'].mean():.1%} | "
        f"{len(monthly)} monthly periods"
    )


if __name__ == "__main__":
    main()
