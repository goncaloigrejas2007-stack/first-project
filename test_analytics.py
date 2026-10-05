import pandas as pd
import pytest

import db
from analytics import calculate_budget_summary, forecast_spending, get_monthly_spending


@pytest.fixture
def finance_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCE_DB_PATH", str(tmp_path / "finance.db"))
    db.init_db()
    db.save_budget(7, "Food", 100)
    return db


def transactions():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-04",
                    "2025-01-05",
                    "2025-01-06",
                    "2025-01-07",
                    "2025-01-07",
                ]
            ),
            "amount": [10, 10, 10, 10, 10, 10, 10, 500],
            "category": ["Food"] * 7 + ["Income"],
        }
    )


def test_forecast_requires_seven_expense_days():
    data = transactions()

    assert forecast_spending(data, days_ahead=30) == pytest.approx(300)
    assert forecast_spending(data.iloc[:6], days_ahead=30) is None
    assert forecast_spending(pd.DataFrame(), days_ahead=30) is None


def test_budget_summary_uses_user_budget_and_excludes_other_users(finance_db):
    summary = calculate_budget_summary(transactions(), user_id=7)

    food = summary.set_index("category").loc["Food"]
    assert food["budget"] == 100
    assert food["actual"] == 70
    assert food["remaining"] == 30
    assert food["used_percent"] == 70


def test_monthly_spending_groups_expenses_and_excludes_income():
    summary = get_monthly_spending(transactions())

    assert summary.to_dict("records") == [{"month": "2025-01", "amount": 70}]


def test_monthly_spending_handles_empty_dataframe():
    summary = get_monthly_spending(pd.DataFrame())

    assert list(summary.columns) == ["month", "amount"]
    assert summary.empty
