from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from db import get_budget_df


def export_transactions_csv(df: pd.DataFrame) -> bytes:
    if df.empty:
        return pd.DataFrame(columns=["date", "amount", "category", "description"]).to_csv(index=False).encode("utf-8")
    return df[["date", "amount", "category", "description"]].copy().assign(
        date=lambda x: x["date"].dt.strftime("%Y-%m-%d"),
        amount=lambda x: x["amount"].map(lambda val: f"€{val:.2f}"),
    ).to_csv(index=False).encode("utf-8")


def calculate_budget_summary(df: pd.DataFrame, user_id: int = 0) -> pd.DataFrame:
    rows = []
    for _, row in get_budget_df(user_id).iterrows():
        category = row["category"]
        budget_value = float(row["value"])
        actual = 0.0
        if not df.empty:
            actual = df[df["category"] == category]["amount"].sum()
        remaining = budget_value - actual
        used_percent = (actual / budget_value * 100) if budget_value > 0 else 0
        rows.append(
            {
                "category": category,
                "budget": budget_value,
                "actual": actual,
                "remaining": remaining,
                "used_percent": used_percent,
            }
        )
    return pd.DataFrame(rows)


def get_monthly_spending(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "amount"])
    monthly = df[df["category"] != "Income"].copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    return monthly.groupby("month", as_index=False)["amount"].sum().sort_values("month")


def forecast_spending(df: pd.DataFrame, days_ahead: int = 30) -> Optional[float]:
    if df.empty:
        return None
    expense_df = df[df["category"] != "Income"].copy()
    expense_days = expense_df["date"].dt.date.nunique()
    if expense_df.empty or expense_days < 7:
        return None
    daily_avg = expense_df["amount"].sum() / expense_days
    return daily_avg * days_ahead


def get_spending_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return []
    insights = []
    expense_df = df[df["category"] != "Income"].copy()
    if not expense_df.empty:
        top_category = expense_df.groupby("category")["amount"].sum().idxmax()
        top_amount = expense_df.groupby("category")["amount"].sum().max()
        insights.append(f"💡 **Top spending category**: {top_category} (€{top_amount:.2f})")
        avg_transaction = expense_df["amount"].mean()
        max_transaction = expense_df["amount"].max()
        if max_transaction > avg_transaction * 3:
            insights.append(f"⚠️ **Large transaction**: €{max_transaction:.2f} - above average")
        last_30 = df[df["date"] >= (datetime.now() - timedelta(days=30))]
        if len(last_30) > 0:
            avg_30 = last_30[last_30["category"] != "Income"]["amount"].mean() if not last_30[last_30["category"] != "Income"].empty else 0
            if avg_30 > 0:
                insights.append(f"📈 **Average transaction in the last 30 days**: €{avg_30:.2f}")
    return insights
