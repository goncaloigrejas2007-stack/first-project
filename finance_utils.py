import html

import pandas as pd

TRANSACTION_COLUMNS = ["id", "date", "amount", "category", "description"]


def filter_month(df, year, month):
    """Return rows whose date falls in the given year AND month."""
    if df.empty:
        return df.copy()
    return df[(df["date"].dt.year == year) & (df["date"].dt.month == month)].copy()


def escape_html(value) -> str:
    return html.escape(str(value), quote=True)


def validate_positive(value, label="Value"):
    """Return an error message if value is not a finite number > 0, else None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{label} must be a number."
    if number != number or number in (float("inf"), float("-inf")):
        return f"{label} must be a finite number."
    if number <= 0:
        return f"{label} must be greater than zero."
    return None


def validate_category_name(name, max_length=50):
    name = (name or "").strip()
    if not name:
        return "Category name is required."
    if len(name) > max_length:
        return f"Category name must be at most {max_length} characters."
    if name.lower() == "income":
        return "'Income' is a reserved category."
    return None
