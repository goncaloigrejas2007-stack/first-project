import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

DB_PATH = Path(os.environ.get("FINANCE_DB_PATH", Path(__file__).resolve().parent / "finance_data.db"))
DEFAULT_BUDGETS = {
    "Food & Dining": 500,
    "Transport": 150,
    "Entertainment": 300,
    "Utilities": 200,
    "Health & Fitness": 150,
    "Shopping": 250,
    "Education": 200,
    "Subscriptions": 100,
    "Travel & Holidays": 400,
    "Personal Care": 100,
    "Other": 200,
}


def ensure_column(conn, table_name, column_name, column_sql):
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _init_db(conn)


def _init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL,
            value REAL NOT NULL,
            UNIQUE(user_id, category)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            saved REAL NOT NULL DEFAULT 0,
            description TEXT NOT NULL DEFAULT '',
            UNIQUE(user_id, name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '📦',
            UNIQUE(user_id, name)
        )
        """
    )

    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_budgets_user_category ON budgets(user_id, category)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_categories_user_name ON custom_categories(user_id, name)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_goals_user_name ON savings_goals(user_id, name)")

    ensure_column(conn, "transactions", "user_id", "user_id INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "budgets", "user_id", "user_id INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "savings_goals", "user_id", "user_id INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "custom_categories", "user_id", "user_id INTEGER NOT NULL DEFAULT 0")

    existing_budget_rows = conn.execute(
        "SELECT category FROM budgets WHERE user_id = 0 GROUP BY category"
    ).fetchall()
    existing_budget_categories = {row[0] for row in existing_budget_rows}
    for category, value in DEFAULT_BUDGETS.items():
        if category not in existing_budget_categories:
            conn.execute(
                "INSERT INTO budgets (user_id, category, value) VALUES (?, ?, ?)",
                (0, category, value),
            )

    conn.commit()


def get_transactions_df(user_id=0):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        df = pd.read_sql_query(
            "SELECT id, date, amount, category, description FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC",
            conn,
            params=(int(user_id),),
        )
    if df.empty:
        return pd.DataFrame(columns=["id", "date", "amount", "category", "description"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_budget_df(user_id=0):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        df = pd.read_sql_query(
            "SELECT category, value FROM budgets WHERE user_id = ? ORDER BY category ASC",
            conn,
            params=(int(user_id),),
        )
    return pd.DataFrame(columns=["category", "value"]) if df.empty else df


def get_goals_df(user_id=0):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        df = pd.read_sql_query(
            "SELECT id, name, target, saved, description FROM savings_goals WHERE user_id = ? ORDER BY name ASC",
            conn,
            params=(int(user_id),),
        )
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "target", "saved", "description"])
    return df


def save_transaction(user_id, amount, category, description, date_value):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            INSERT INTO transactions (user_id, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (int(user_id), str(date_value), float(amount), category, description.strip() or "No description"),
        )
        conn.commit()


def update_transaction(user_id, transaction_id, amount, category, description, date_value):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            UPDATE transactions
            SET date = ?, amount = ?, category = ?, description = ?
            WHERE id = ? AND user_id = ?
            """,
            (str(date_value), float(amount), category, description.strip() or "No description", int(transaction_id), int(user_id)),
        )
        conn.commit()


def delete_transaction(user_id, transaction_id):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (int(transaction_id), int(user_id)))
        conn.commit()


def save_budget(user_id, category, value):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            INSERT INTO budgets (user_id, category, value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET value = excluded.value
            """,
            (int(user_id), category, float(value)),
        )
        conn.commit()


def add_custom_category(user_id, name, emoji="📦"):
    name = name.strip()
    if not name or len(name) > 40 or name.casefold() == "income":
        return False
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO custom_categories (user_id, name, emoji) VALUES (?, ?, ?)",
            (int(user_id), name, emoji),
        )
        if cursor.rowcount == 0:
            return False
        conn.commit()
    return True


def get_all_categories(user_id=0):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        budget_categories = [
            row[0] for row in conn.execute(
                "SELECT category FROM budgets WHERE user_id = ? UNION SELECT category FROM budgets WHERE user_id = 0",
                (int(user_id),),
            ).fetchall()
        ]
        custom_categories = [
            row[0] for row in conn.execute(
                "SELECT name FROM custom_categories WHERE user_id = ? UNION SELECT name FROM custom_categories WHERE user_id = 0",
                (int(user_id),),
            ).fetchall()
        ]
    return sorted(set(budget_categories + custom_categories + ["Income"]))


def save_goal(user_id, name, target, description=""):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO savings_goals (user_id, name, target, saved, description) VALUES (?, ?, ?, 0, ?)",
            (int(user_id), name.strip(), float(target), description.strip()),
        )
        conn.commit()


def add_to_goal(user_id, goal_id, amount):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "UPDATE savings_goals SET saved = saved + ? WHERE id = ? AND user_id = ?",
            (float(amount), int(goal_id), int(user_id)),
        )
        conn.commit()


def delete_goal(user_id, goal_id):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?", (int(goal_id), int(user_id)))
        conn.commit()
