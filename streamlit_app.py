import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from auth_manager import (
    get_user_settings,
    init_auth_db,
    login_user,
    register_user,
    update_user_settings,
)

DB_PATH = Path(__file__).resolve().parent / "finance_data.db"
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
DEFAULT_GOALS = {
    "Emergency Fund": 3000,
    "Travel": 2000,
    "New Laptop": 1500,
}
CATEGORY_EMOJIS = {
    "Food & Dining": "🍔",
    "Transport": "🚗",
    "Entertainment": "🎬",
    "Utilities": "💡",
    "Health & Fitness": "🏃",
    "Shopping": "🛍️",
    "Education": "📚",
    "Subscriptions": "📺",
    "Travel & Holidays": "✈️",
    "Personal Care": "💅",
    "Income": "💰",
    "Other": "📦",
}


def ensure_column(conn, table_name, column_name, column_sql):
    columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()


def get_active_user_id():
    return st.session_state.get("user_id")


def get_transactions_df(user_id=None):
    user_id = user_id if user_id is not None else get_active_user_id()
    conn = sqlite3.connect(DB_PATH)
    if user_id is None:
        df = pd.read_sql_query(
            "SELECT id, date, amount, category, description FROM transactions WHERE user_id = 0 ORDER BY date DESC, id DESC",
            conn,
        )
    else:
        df = pd.read_sql_query(
            "SELECT id, date, amount, category, description FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC",
            conn,
            params=(user_id,),
        )
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id", "date", "amount", "category", "description"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_budget_df(user_id=None):
    user_id = user_id if user_id is not None else get_active_user_id()
    conn = sqlite3.connect(DB_PATH)
    if user_id is None:
        df = pd.read_sql_query(
            "SELECT category, value FROM budgets WHERE user_id = 0 ORDER BY category ASC",
            conn,
        )
    else:
        df = pd.read_sql_query(
            "SELECT category, value FROM budgets WHERE user_id = ? ORDER BY category ASC",
            conn,
            params=(user_id,),
        )
    conn.close()
    return pd.DataFrame(columns=["category", "value"]) if df.empty else df


def get_goals_df(user_id=None):
    user_id = user_id if user_id is not None else get_active_user_id()
    conn = sqlite3.connect(DB_PATH)
    if user_id is None:
        df = pd.read_sql_query(
            "SELECT id, name, target, saved, description FROM savings_goals WHERE user_id = 0 ORDER BY name ASC",
            conn,
        )
    else:
        df = pd.read_sql_query(
            "SELECT id, name, target, saved, description FROM savings_goals WHERE user_id = ? ORDER BY name ASC",
            conn,
            params=(user_id,),
        )
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["id", "name", "target", "saved", "description"])
    return df


def save_transaction(user_id, amount, category, description, date_value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO transactions (user_id, date, amount, category, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(user_id), str(date_value), float(amount), category, description.strip() or "No description"),
    )
    conn.commit()
    conn.close()


def update_transaction(user_id, transaction_id, amount, category, description, date_value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        UPDATE transactions
        SET date = ?, amount = ?, category = ?, description = ?
        WHERE id = ? AND user_id = ?
        """,
        (str(date_value), float(amount), category, description.strip() or "No description", int(transaction_id), int(user_id)),
    )
    conn.commit()
    conn.close()


def delete_transaction(user_id, transaction_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (int(transaction_id), int(user_id)))
    conn.commit()
    conn.close()


def save_budget(user_id, category, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO budgets (user_id, category, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET value = excluded.value
        """,
        (int(user_id), category, float(value)),
    )
    conn.commit()
    conn.close()


def add_custom_category(user_id, name, emoji="📦"):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO custom_categories (user_id, name, emoji) VALUES (?, ?, ?)",
            (int(user_id), name.strip(), emoji),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_all_categories(user_id=None):
    user_id = user_id if user_id is not None else get_active_user_id()
    conn = sqlite3.connect(DB_PATH)
    budget_categories = [
        row[0] for row in conn.execute(
            "SELECT category FROM budgets WHERE user_id = ? UNION SELECT category FROM budgets WHERE user_id = 0",
            (int(user_id),) if user_id is not None else (0,),
        ).fetchall()
    ]
    custom_categories = [
        row[0] for row in conn.execute(
            "SELECT name FROM custom_categories WHERE user_id = ? UNION SELECT name FROM custom_categories WHERE user_id = 0",
            (int(user_id),) if user_id is not None else (0,),
        ).fetchall()
    ]
    conn.close()
    all_categories = list(set(budget_categories + custom_categories + ["Income"]))
    return sorted(all_categories)


def save_goal(user_id, name, target, description=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO savings_goals (user_id, name, target, saved, description) VALUES (?, ?, ?, 0, ?)",
        (int(user_id), name.strip(), float(target), description.strip()),
    )
    conn.commit()
    conn.close()


def add_to_goal(user_id, goal_id, amount):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE savings_goals SET saved = saved + ? WHERE id = ? AND user_id = ?",
        (float(amount), int(goal_id), int(user_id)),
    )
    conn.commit()
    conn.close()


def delete_goal(user_id, goal_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?", (int(goal_id), int(user_id)))
    conn.commit()
    conn.close()


def export_transactions_csv(df):
    if df.empty:
        return pd.DataFrame(columns=["date", "amount", "category", "description"]).to_csv(index=False).encode("utf-8")
    return df[["date", "amount", "category", "description"]].copy().assign(
        date=lambda x: x["date"].dt.strftime("%Y-%m-%d"),
        amount=lambda x: x["amount"].map(lambda val: f"€{val:.2f}"),
    ).to_csv(index=False).encode("utf-8")


def calculate_budget_summary(df, user_id=None):
    user_id = user_id if user_id is not None else get_active_user_id()
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


def get_monthly_spending(df):
    if df.empty:
        return pd.DataFrame(columns=["month", "amount"])
    monthly = df[df["category"] != "Income"].copy()
    monthly["month"] = monthly["date"].dt.to_period("M").astype(str)
    return monthly.groupby("month", as_index=False)["amount"].sum().sort_values("month")


def forecast_spending(df, days_ahead=30):
    if df.empty or len(df["date"].unique()) < 7:
        return None
    expense_df = df[df["category"] != "Income"].copy()
    if expense_df.empty:
        return None
    daily_avg = expense_df["amount"].sum() / len(df["date"].unique())
    return daily_avg * days_ahead


def get_spending_insights(df):
    if df.empty:
        return []
    insights = []
    expense_df = df[df["category"] != "Income"].copy()
    if not expense_df.empty:
        top_category = expense_df.groupby("category")["amount"].sum().idxmax()
        top_amount = expense_df.groupby("category")["amount"].sum().max()
        insights.append(f"💡 **Maior gasto**: {top_category} (€{top_amount:.2f})")
        avg_transaction = expense_df["amount"].mean()
        max_transaction = expense_df["amount"].max()
        if max_transaction > avg_transaction * 3:
            insights.append(f"⚠️ **Transação grande**: €{max_transaction:.2f} - acima da média")
        last_30 = df[df["date"] >= (datetime.now() - timedelta(days=30))]
        if len(last_30) > 0:
            avg_30 = last_30[last_30["category"] != "Income"]["amount"].mean() if not last_30[last_30["category"] != "Income"].empty else 0
            if avg_30 > 0:
                insights.append(f"📈 **Média dos últimos 30 dias**: €{avg_30:.2f}")
    return insights


st.set_page_config(page_title="Finance Dashboard Pro", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    [data-testid="stMetric"] { background: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.35); border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: var(--text-color); opacity: 1; }
    .insight-box { color: #212529; background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; border-radius: 5px; margin: 10px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

init_auth_db()
init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def show_auth_page():
    st.title("💰 Finance Dashboard Pro")
    st.write("Login to access your private financial dashboard.")
    auth_tab, register_tab = st.tabs(["Login", "Register"])

    with auth_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                result = login_user(username, password)
                if result["success"]:
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

    with register_tab:
        with st.form("register_form"):
            reg_username = st.text_input("Choose username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")
            if submitted:
                if reg_password != confirm_password:
                    st.error("Passwords do not match.")
                elif not reg_username.strip() or not reg_email.strip():
                    st.warning("Username and email are required.")
                else:
                    result = register_user(reg_username.strip(), reg_email.strip(), reg_password)
                    if result["success"]:
                        st.success("Account created. Please login.")
                    else:
                        st.error(result["message"])


if st.session_state.user_id is None:
    show_auth_page()
    st.stop()

user_id = st.session_state.user_id
username = st.session_state.username

with st.sidebar:
    st.title(f"👋 {username}")
    st.caption("Private finance dashboard")

    settings = get_user_settings(user_id)
    st.subheader("Settings")
    theme = st.selectbox("Theme", ["light", "dark"], index=["light", "dark"].index(settings.get("theme", "light")))
    notifications_enabled = st.checkbox("Enable notifications", value=bool(settings.get("notifications_enabled", 1)))
    if st.button("Save settings"):
        update_user_settings(user_id, {"theme": theme, "notifications_enabled": int(notifications_enabled)})
        st.success("Settings saved")

    st.divider()
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.chat_history = []
        st.rerun()

st.title("💰 Personal Finance Dashboard Pro")
transactions_df = get_transactions_df(user_id)
expense_df = transactions_df[transactions_df["category"] != "Income"].copy() if not transactions_df.empty else pd.DataFrame(columns=["id", "date", "amount", "category", "description"])

if transactions_df.empty:
    total_spending = 0.0
    total_income = 0.0
    net_balance = 0.0
    avg_transaction = 0.0
    month_spending = 0.0
    month_income = 0.0
else:
    total_spending = expense_df["amount"].sum() if not expense_df.empty else 0.0
    total_income = transactions_df[transactions_df["category"] == "Income"]["amount"].sum()
    net_balance = total_income - total_spending
    avg_transaction = expense_df["amount"].mean() if not expense_df.empty else 0.0
    current_month = transactions_df[transactions_df["date"].dt.month == datetime.now().month]
    month_spending = current_month[current_month["category"] != "Income"]["amount"].sum()
    month_income = current_month[current_month["category"] == "Income"]["amount"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💸 Total spending", f"€{total_spending:.2f}")
with col2:
    st.metric("💵 Total income", f"€{total_income:.2f}")
with col3:
    st.metric("💳 Net balance", f"€{net_balance:.2f}")
with col4:
    st.metric("📊 Avg transaction", f"€{avg_transaction:.2f}")
with col5:
    forecast = forecast_spending(transactions_df, 30)
    st.metric("📈 30-day forecast", f"€{forecast:.2f}" if forecast is not None else "€0.00")

if not transactions_df.empty:
    st.divider()
    st.subheader("🔍 Smart insights")
    for insight in get_spending_insights(transactions_df):
        st.markdown(f"<div class='insight-box'>{insight}</div>", unsafe_allow_html=True)

st.divider()
overview_tab, analytics_tab, budget_tab, savings_tab, transactions_tab = st.tabs(["Overview", "Analytics", "Budget", "Savings", "Transactions"])

with overview_tab:
    st.subheader("📝 Recent transactions")
    if transactions_df.empty:
        st.info("Add your first transaction from the sidebar to start tracking your finances.")
    else:
        recent = transactions_df.sort_values("date", ascending=False).head(10).copy()
        recent["date"] = recent["date"].dt.strftime("%d/%m/%Y")
        recent["amount"] = recent["amount"].apply(lambda x: f"€{x:.2f}")
        st.dataframe(recent, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.metric("📅 This month spending", f"€{month_spending:.2f}")
    with c2:
        st.metric("📥 This month income", f"€{month_income:.2f}")

    if not transactions_df.empty:
        st.subheader("📈 Monthly spending trend")
        monthly_spending_df = get_monthly_spending(transactions_df)
        if not monthly_spending_df.empty:
            trend_chart = alt.Chart(monthly_spending_df).mark_line(point=True, size=3).encode(
                x=alt.X("month:N", title="Month"),
                y=alt.Y("amount:Q", title="Amount (€)"),
                tooltip=["month", "amount"],
                color=alt.value("#4f46e5"),
            ).interactive()
            st.altair_chart(trend_chart, use_container_width=True)

with analytics_tab:
    if transactions_df.empty:
        st.info("Add expense transactions to see analytics.")
    else:
        if not expense_df.empty:
            category_summary = expense_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💹 Spending by category")
                chart = alt.Chart(category_summary).mark_bar().encode(
                    x=alt.X("amount:Q", title="Amount (€)"),
                    y=alt.Y("category:N", title="Category", sort="-x"),
                    color=alt.Color("category:N", legend=None),
                    tooltip=["category", "amount"],
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            with c2:
                st.subheader("🥧 Category distribution")
                pie_chart = alt.Chart(category_summary).mark_arc().encode(
                    theta="amount:Q",
                    color=alt.Color("category:N", legend=alt.Legend(title="Category")),
                    tooltip=["category", "amount"],
                ).interactive()
                st.altair_chart(pie_chart, use_container_width=True)

            st.divider()
            st.subheader("📊 Advanced statistics")
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric("Median", f"€{expense_df['amount'].median():.2f}")
            with sc2:
                st.metric("Standard deviation", f"€{expense_df['amount'].std():.2f}")
            with sc3:
                st.metric("Highest", f"€{expense_df['amount'].max():.2f}")
            with sc4:
                st.metric("Lowest", f"€{expense_df[expense_df['amount'] > 0]['amount'].min():.2f}" if not expense_df[expense_df["amount"] > 0].empty else "€0.00")

with budget_tab:
    st.subheader("🎯 Monthly budget")
    budget_df = get_budget_df(user_id)
    if budget_df.empty:
        for category, value in DEFAULT_BUDGETS.items():
            save_budget(user_id, category, value)
        budget_df = get_budget_df(user_id)

    budget_values = {}
    for _, row in budget_df.iterrows():
        budget_values[row["category"]] = st.number_input(f"{row['category']} (€)", value=float(row["value"]), step=10.0, key=f"budget_{user_id}_{row['category']}")

    if st.button("💾 Save budget"):
        for category, value in budget_values.items():
            save_budget(user_id, category, value)
        st.success("Budget updated successfully!")
        st.rerun()

    if st.button("🔄 Reset budget"):
        for category, value in DEFAULT_BUDGETS.items():
            save_budget(user_id, category, value)
        st.success("Budget reset to default values.")
        st.rerun()

    st.divider()
    st.subheader("📊 Budget vs actual spending")
    current_month_df = transactions_df[transactions_df["date"].dt.month == datetime.now().month].copy() if not transactions_df.empty else pd.DataFrame(columns=["id", "date", "amount", "category", "description"])
    budget_summary_df = calculate_budget_summary(current_month_df, user_id)
    if budget_summary_df.empty:
        st.info("No budget data available yet.")
    else:
        for _, row in budget_summary_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                emoji = "🔴" if row["used_percent"] > 100 else "🟡" if row["used_percent"] > 75 else "🟢"
                st.write(f"{emoji} **{row['category']}**")
                st.progress(min(row["used_percent"] / 100, 1.0))
                if 75 <= row["used_percent"] < 100:
                    st.caption("⚠️ Warning: close to the limit.")
                elif row["used_percent"] >= 100:
                    st.caption("🚨 Budget exceeded!")
            with col2:
                st.metric("Budget", f"€{row['budget']:.2f}", label_visibility="collapsed")
            with col3:
                st.metric("Used", f"€{row['actual']:.2f}", label_visibility="collapsed")
            with col4:
                st.metric("Left", f"€{row['remaining']:.2f}", label_visibility="collapsed")

with savings_tab:
    st.subheader("💼 Savings goals")
    goal_df = get_goals_df(user_id)
    if goal_df.empty:
        st.info("No savings goals yet. Create one to start tracking your goals.")
    else:
        total_target = goal_df["target"].sum()
        total_saved = goal_df["saved"].sum()
        total_remaining = total_target - total_saved
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎯 Total target", f"€{total_target:.2f}")
        with c2:
            st.metric("💰 Saved", f"€{total_saved:.2f}")
        with c3:
            st.metric("📌 Remaining", f"€{total_remaining:.2f}")

        st.divider()
        for _, row in goal_df.iterrows():
            progress = min(row["saved"] / row["target"], 1.0) if row["target"] > 0 else 0.0
            remaining = row["target"] - row["saved"]
            st.write(f"**{row['name']}**")
            st.progress(progress)
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                st.caption(f"Saved: €{row['saved']:.2f}")
            with col_b:
                st.caption(f"Target: €{row['target']:.2f}")
            with col_c:
                st.caption(f"Left: €{remaining:.2f}")
            if progress >= 1:
                st.success("Goal achieved! 🎉")
            elif progress >= 0.75:
                st.warning("You are close to reaching this goal.")
            st.write("---")

    st.subheader("Create new goal")
    with st.form("goal_form", clear_on_submit=True):
        goal_name = st.text_input("Goal name")
        goal_target = st.number_input("Target (€)", min_value=0.0, step=50.0)
        goal_description = st.text_input("Description (optional)")
        if st.form_submit_button("Add goal"):
            if goal_name.strip():
                save_goal(user_id, goal_name, goal_target, goal_description)
                st.success("Goal added successfully")
                st.rerun()
            else:
                st.warning("Please enter a goal name.")

    st.subheader("Add contribution")
    goals_for_contribution = get_goals_df(user_id)
    if goals_for_contribution.empty:
        st.info("Create a goal first.")
    else:
        with st.form("goal_contribution_form"):
            selected_goal = st.selectbox("Choose goal", goals_for_contribution["name"].tolist())
            contribution = st.number_input("Contribution (€)", min_value=0.0, step=10.0)
            if st.form_submit_button("Add to goal"):
                goal_id = int(goals_for_contribution.loc[goals_for_contribution["name"] == selected_goal, "id"].iloc[0])
                if contribution > 0:
                    add_to_goal(user_id, goal_id, contribution)
                    st.success(f"Added €{contribution:.2f} to {selected_goal}.")
                    st.rerun()

    st.subheader("Delete goal")
    goals_for_delete = get_goals_df(user_id)
    if goals_for_delete.empty:
        st.info("Nothing to delete.")
    else:
        goal_to_delete = st.selectbox("Select goal", goals_for_delete["name"].tolist(), key="goal_delete_select")
        if st.button("Delete selected goal"):
            goal_id = int(goals_for_delete.loc[goals_for_delete["name"] == goal_to_delete, "id"].iloc[0])
            delete_goal(user_id, goal_id)
            st.warning(f"Goal '{goal_to_delete}' deleted.")
            st.rerun()

with transactions_tab:
    st.subheader("📋 All transactions")
    df = transactions_df.copy()
    if df.empty:
        st.info("No transactions to display. Add some from the sidebar.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            selected_categories = st.multiselect("Filter by category", df["category"].unique(), default=list(df["category"].unique()))
        with c2:
            date_range = st.date_input("Date range", value=(df["date"].min().date(), df["date"].max().date()))
        with c3:
            sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])

        filtered_df = df[df["category"].isin(selected_categories)].copy()
        if len(date_range) == 2:
            filtered_df = filtered_df[(filtered_df["date"] >= pd.to_datetime(date_range[0])) & (filtered_df["date"] <= pd.to_datetime(date_range[1]))]

        if sort_by == "Date (newest)":
            filtered_df = filtered_df.sort_values("date", ascending=False)
        elif sort_by == "Date (oldest)":
            filtered_df = filtered_df.sort_values("date", ascending=True)
        elif sort_by == "Amount (high)":
            filtered_df = filtered_df.sort_values("amount", ascending=False)
        else:
            filtered_df = filtered_df.sort_values("amount", ascending=True)

        display_df = filtered_df[["date", "amount", "category", "description"]].copy()
        display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
        display_df["amount"] = display_df["amount"].apply(lambda x: f"€{x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button("📤 Export filtered CSV", export_transactions_csv(filtered_df), file_name="filtered_transactions.csv", mime="text/csv")

        st.divider()
        st.subheader("✏️ Edit or delete transaction")
        if not filtered_df.empty:
            transaction_id = st.selectbox(
                "Choose transaction",
                filtered_df["id"].tolist(),
                format_func=lambda x: f"#{x} - {filtered_df.loc[filtered_df['id'] == x, 'category'].iloc[0]} - €{filtered_df.loc[filtered_df['id'] == x, 'amount'].iloc[0]:.2f}",
            )
            row = filtered_df[filtered_df["id"] == transaction_id].iloc[0]
            transaction_categories = get_all_categories(user_id)
            with st.form("edit_transaction_form"):
                edit_amount = st.number_input("Edit amount (€)", min_value=0.0, value=float(row["amount"]), step=0.01)
                edit_category = st.selectbox("Edit category", transaction_categories, index=transaction_categories.index(row["category"]) if row["category"] in transaction_categories else 0)
                edit_description = st.text_input("Edit description", value=row["description"])
                edit_date = st.date_input("Edit date", value=row["date"].date())
                c_edit, c_delete = st.columns(2)
                with c_edit:
                    save_edit = st.form_submit_button("💾 Save changes")
                with c_delete:
                    delete_button = st.form_submit_button("🗑️ Delete")

                if save_edit:
                    update_transaction(user_id, transaction_id, edit_amount, edit_category, edit_description, edit_date)
                    st.success("Transaction updated successfully!")
                    st.rerun()
                if delete_button:
                    delete_transaction(user_id, transaction_id)
                    st.warning("Transaction deleted.")
                    st.rerun()

        st.divider()
        total = filtered_df[filtered_df["category"] != "Income"]["amount"].sum()
        income = filtered_df[filtered_df["category"] == "Income"]["amount"].sum()
        net = income - total
        count = len(filtered_df)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total spending", f"€{total:.2f}")
        with c2:
            st.metric("Total income", f"€{income:.2f}")
        with c3:
            st.metric("Net", f"€{net:.2f}")
        with c4:
            st.metric("Transactions", count)

with st.sidebar:
    st.subheader("➕ Add transaction")
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            amount = st.number_input("Amount (€)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        with c2:
            category_options = get_all_categories(user_id)
            category = st.selectbox("Category", category_options)
        description = st.text_input("Description")
        date_value = st.date_input("Date", datetime.now())
        submitted = st.form_submit_button("💾 Save transaction")
        if submitted:
            if amount <= 0:
                st.error("Enter an amount greater than 0.")
            else:
                save_transaction(user_id, amount, category, description, date_value)
                st.session_state.flash = "Transaction saved!"
                st.rerun()
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))

    with st.expander("🏷️ Manage categories"):
        new_category = st.text_input("New category")
        new_emoji = st.selectbox("Emoji", ["🍔", "🚗", "🎬", "💡", "🏃", "🛍️", "📚", "📺", "✈️", "💅", "📦", "🏥", "🎮", "📱", "👕"])
        if st.button("Add category"):
            if new_category.strip():
                add_custom_category(user_id, new_category, new_emoji)
                save_budget(user_id, new_category, 100)
                st.success("Category added.")
                st.rerun()

st.divider()
st.markdown(
    """
    <div style='text-align: center; opacity: 0.7; font-size: 12px;'>
    💰 Finance Dashboard Pro | Personal private account | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
