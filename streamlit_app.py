import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

import altair as alt
import pandas as pd
import streamlit as st

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


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            category TEXT PRIMARY KEY,
            value REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            saved REAL NOT NULL DEFAULT 0,
            description TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_categories (
            name TEXT PRIMARY KEY,
            emoji TEXT NOT NULL DEFAULT '📦'
        )
        """
    )

    existing_budget_categories = {
        row[0] for row in conn.execute("SELECT category FROM budgets").fetchall()
    }
    for category, value in DEFAULT_BUDGETS.items():
        if category not in existing_budget_categories:
            conn.execute(
                "INSERT INTO budgets (category, value) VALUES (?, ?)",
                (category, value),
            )

    existing_goal_names = {
        row[0] for row in conn.execute("SELECT name FROM savings_goals").fetchall()
    }
    for goal_name, target in DEFAULT_GOALS.items():
        if goal_name not in existing_goal_names:
            conn.execute(
                "INSERT INTO savings_goals (name, target, saved, description) VALUES (?, ?, ?, ?)",
                (goal_name, target, 0, ""),
            )

    conn.commit()
    conn.close()


def get_transactions_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT id, date, amount, category, description
        FROM transactions
        ORDER BY date DESC, id DESC
        """,
        conn,
    )
    conn.close()

    if df.empty:
        return pd.DataFrame(
            columns=["id", "date", "amount", "category", "description"]
        )

    df["date"] = pd.to_datetime(df["date"])
    return df


def get_budget_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT category, value FROM budgets ORDER BY category ASC",
        conn,
    )
    conn.close()

    if df.empty:
        return pd.DataFrame(columns=["category", "value"])
    return df


def get_goals_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT id, name, target, saved, description FROM savings_goals ORDER BY name ASC",
        conn,
    )
    conn.close()

    if df.empty:
        return pd.DataFrame(columns=["id", "name", "target", "saved", "description"])
    return df


def save_transaction(amount, category, description, date_value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO transactions (date, amount, category, description)
        VALUES (?, ?, ?, ?)
        """,
        (str(date_value), float(amount), category, description.strip() or "No description"),
    )
    conn.commit()
    conn.close()


def update_transaction(transaction_id, amount, category, description, date_value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        UPDATE transactions
        SET date = ?, amount = ?, category = ?, description = ?
        WHERE id = ?
        """,
        (str(date_value), float(amount), category, description.strip() or "No description", int(transaction_id)),
    )
    conn.commit()
    conn.close()


def delete_transaction(transaction_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM transactions WHERE id = ?", (int(transaction_id),))
    conn.commit()
    conn.close()


def save_budget(category, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO budgets (category, value) VALUES (?, ?) ON CONFLICT(category) DO UPDATE SET value = excluded.value",
        (category, float(value)),
    )
    conn.commit()
    conn.close()


def add_custom_category(name, emoji="📦"):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO custom_categories (name, emoji) VALUES (?, ?)",
            (name, emoji),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_all_categories():
    conn = sqlite3.connect(DB_PATH)
    budget_categories = [row[0] for row in conn.execute("SELECT category FROM budgets").fetchall()]
    custom_categories = [row[0] for row in conn.execute("SELECT name FROM custom_categories").fetchall()]
    conn.close()
    return list(set(budget_categories + custom_categories + ["Income"]))


def save_goal(name, target, description=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO savings_goals (name, target, saved, description) VALUES (?, ?, 0, ?)",
        (name.strip(), float(target), description.strip()),
    )
    conn.commit()
    conn.close()


def add_to_goal(goal_id, amount):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE savings_goals SET saved = saved + ? WHERE id = ?",
        (float(amount), int(goal_id)),
    )
    conn.commit()
    conn.close()


def delete_goal(goal_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM savings_goals WHERE id = ?", (int(goal_id),))
    conn.commit()
    conn.close()


def export_transactions_csv(df):
    if df.empty:
        return pd.DataFrame(columns=["date", "amount", "category", "description"]).to_csv(index=False).encode("utf-8")

    return df[["date", "amount", "category", "description"]].copy().assign(
        date=lambda x: x["date"].dt.strftime("%Y-%m-%d"),
        amount=lambda x: x["amount"].map(lambda val: f"€{val:.2f}"),
    ).to_csv(index=False).encode("utf-8")


def calculate_budget_summary(df):
    rows = []
    for _, row in get_budget_df().iterrows():
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
    """Simples previsão de gastos baseada na média"""
    if df.empty or len(df) < 7:
        return None
    
    expense_df = df[df["category"] != "Income"].copy()
    daily_avg = expense_df["amount"].sum() / len(df["date"].unique()) if len(df["date"].unique()) > 0 else 0
    
    return daily_avg * days_ahead


def get_spending_insights(df):
    """Gera insights automáticos sobre gastos"""
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
            insights.append(f"⚠️ **Transação grande**: €{max_transaction:.2f} - significativamente acima da média")
        
        last_7_days = df[df["date"] >= (datetime.now() - timedelta(days=7))]
        last_30_days = df[df["date"] >= (datetime.now() - timedelta(days=30))]
        
        if len(last_7_days) > 0 and len(last_30_days) > 0:
            avg_7 = last_7_days[last_7_days["category"] != "Income"]["amount"].mean()
            avg_30 = last_30_days[last_30_days["category"] != "Income"]["amount"].mean()
            if avg_7 > avg_30 * 1.2:
                insights.append(f"📈 **Tendência**: Gastos acima da média este mês")
    
    return insights


st.set_page_config(
    page_title="💰 Finance Dashboard Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
    }
    .stMetric {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px;
    }
    .insight-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

with st.sidebar:
    st.title("➕ Add Transaction")
    
    # Selector para adicionar categoria customizada
    with st.expander("🏷️ Manage Categories"):
        new_cat = st.text_input("Nova categoria")
        new_emoji = st.selectbox("Emoji", ["🍔", "🚗", "🎬", "💡", "🏃", "🛍️", "📚", "📺", "✈️", "💅", "📦", "🏥", "🎮", "📱", "👕"])
        if st.button("Add Category"):
            if new_cat:
                add_custom_category(new_cat, new_emoji)
                save_budget(new_cat, 100)
                st.success("Categoria adicionada!")
                st.rerun()
    
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
        with col2:
            categories = get_all_categories()
            category = st.selectbox("Category", categories)

        description = st.text_input("Description")
        date_value = st.date_input("Date", datetime.now())

        submitted = st.form_submit_button("💾 Save Transaction")

        if submitted and amount > 0:
            save_transaction(amount, category, description, date_value)
            st.sidebar.success("Transaction saved!")
            st.rerun()

st.title("💰 Personal Finance Dashboard Pro")

transactions_df = get_transactions_df()
expense_df = transactions_df[transactions_df["category"] != "Income"].copy() if not transactions_df.empty else pd.DataFrame(columns=["id", "date", "amount", "category", "description"])

# Overview metrics
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
    st.metric("💸 Total Spending", f"€{total_spending:.2f}")
with col2:
    st.metric("💵 Total Income", f"€{total_income:.2f}")
with col3:
    st.metric(
        "💳 Net Balance",
        f"€{net_balance:.2f}",
        delta=f"€{net_balance:.2f}" if net_balance >= 0 else f"-€{abs(net_balance):.2f}",
    )
with col4:
    st.metric("📊 Avg Transaction", f"€{avg_transaction:.2f}")
with col5:
    forecast = forecast_spending(transactions_df, 30)
    if forecast:
        st.metric("📈 30-Day Forecast", f"€{forecast:.2f}")

# Insights automáticos
if not transactions_df.empty:
    insights = get_spending_insights(transactions_df)
    if insights:
        st.divider()
        st.subheader("🔍 Smart Insights")
        for insight in insights:
            st.markdown(f"<div class='insight-box'>{insight}</div>", unsafe_allow_html=True)

st.divider()

overview_tab, analytics_tab, budget_tab, savings_tab, transactions_tab, comparison_tab = st.tabs(
    ["📊 Overview", "📈 Analytics", "🎯 Budget", "💼 Savings", "📋 Transactions", "📊 Comparison"]
)

with overview_tab:
    st.subheader("📝 Recent Transactions")
    if transactions_df.empty:
        st.info("👉 Add your first transaction from the sidebar to start tracking your finances.")
    else:
        recent = transactions_df.sort_values("date", ascending=False).head(15).copy()
        recent["date"] = recent["date"].dt.strftime("%d/%m/%Y")
        recent["amount"] = recent["amount"].apply(lambda x: f"€{x:.2f}")
        st.dataframe(recent, use_container_width=True, hide_index=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📅 This Month Spending", f"€{month_spending:.2f}")
    with col2:
        st.metric("📥 This Month Income", f"€{month_income:.2f}")

    if not transactions_df.empty:
        st.subheader("📈 Monthly Spending Trend")
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
            category_summary = (
                expense_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            )

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💹 Spending by Category")
                chart = alt.Chart(category_summary).mark_bar().encode(
                    x=alt.X("amount:Q", title="Amount (€)"),
                    y=alt.Y("category:N", title="Category", sort="-x"),
                    color=alt.Color("category:N", legend=None),
                    tooltip=["category", "amount"],
                ).interactive()
                st.altair_chart(chart, use_container_width=True)

            with col2:
                st.subheader("🥧 Category Distribution")
                pie_chart = alt.Chart(category_summary).mark_arc().encode(
                    theta="amount:Q",
                    color=alt.Color("category:N", legend=alt.Legend(title="Category")),
                    tooltip=["category", "amount"],
                ).interactive()
                st.altair_chart(pie_chart, use_container_width=True)

            st.divider()
            
            # Estatísticas Avançadas
            st.subheader("📊 Advanced Statistics")
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                median = expense_df["amount"].median()
                st.metric("📉 Median Transaction", f"€{median:.2f}")
            
            with stats_col2:
                std_dev = expense_df["amount"].std()
                st.metric("📊 Std Deviation", f"€{std_dev:.2f}")
            
            with stats_col3:
                max_trans = expense_df["amount"].max()
                st.metric("📈 Highest", f"€{max_trans:.2f}")
            
            with stats_col4:
                min_trans = expense_df[expense_df["amount"] > 0]["amount"].min() if not expense_df.empty else 0
                st.metric("📉 Lowest", f"€{min_trans:.2f}")

            st.divider()
            st.subheader("📅 Spending Trend (Last 30 days)")
            last_30 = transactions_df[transactions_df["date"] >= (datetime.now() - timedelta(days=30))].copy()
            last_30 = last_30[last_30["category"] != "Income"]

            if not last_30.empty:
                daily_spending = last_30.groupby(last_30["date"].dt.date, as_index=False)["amount"].sum()
                daily_spending.columns = ["date", "amount"]
                trend_chart = alt.Chart(daily_spending).mark_line(point=True, strokeDash=[5, 5]).encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("amount:Q", title="Amount (€)"),
                    tooltip=["date", "amount"],
                ).interactive()
                st.altair_chart(trend_chart, use_container_width=True)

            st.divider()
            st.subheader("📊 Comparison by Month")
            monthly_df = get_monthly_spending(transactions_df).tail(6)
            if not monthly_df.empty:
                monthly_chart = alt.Chart(monthly_df).mark_bar().encode(
                    x=alt.X("month:N", title="Month"),
                    y=alt.Y("amount:Q", title="Amount (€)"),
                    color=alt.condition(
                        alt.datum.amount >= monthly_df["amount"].median(),
                        alt.value("#ff7b72"),
                        alt.value("#4fc3f7"),
                    ),
                    tooltip=["month", "amount"],
                ).interactive()
                st.altair_chart(monthly_chart, use_container_width=True)
        else:
            st.info("Add expense transactions to see analytics.")

with budget_tab:
    st.subheader("🎯 Monthly Budget")
    budget_df = get_budget_df()
    categories = budget_df["category"].tolist()

    budget_values = {}
    for _, row in budget_df.iterrows():
        budget_values[row["category"]] = st.number_input(
            f"{row['category']} (€)",
            value=float(row["value"]),
            step=10,
            key=f"budget_{row['category']}",
        )

    if st.button("💾 Save Budget"):
        for category, value in budget_values.items():
            save_budget(category, value)
        st.success("Budget updated successfully!")
        st.rerun()

    if st.button("🔄 Reset Budget"):
        for category, value in DEFAULT_BUDGETS.items():
            save_budget(category, value)
        st.success("Budget reset to defaults.")
        st.rerun()

    st.divider()
    st.subheader("📊 Budget vs Actual Spending")

    current_month_df = transactions_df[transactions_df["date"].dt.month == datetime.now().month].copy() if not transactions_df.empty else pd.DataFrame(columns=["id", "date", "amount", "category"])
    budget_summary_df = calculate_budget_summary(current_month_df)

    if budget_summary_df.empty:
        st.info("No budget data available yet.")
    else:
        for _, row in budget_summary_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                if row["used_percent"] > 100:
                    emoji = "🔴"
                elif row["used_percent"] > 75:
                    emoji = "🟡"
                else:
                    emoji = "🟢"

                st.write(f"{emoji} **{row['category']}**")
                st.progress(min(row["used_percent"] / 100, 1.0))

                if row["used_percent"] >= 75 and row["used_percent"] < 100:
                    st.caption("⚠️ Warning: budget is getting close to the limit.")
                elif row["used_percent"] >= 100:
                    st.caption("🚨 Budget exceeded!")

            with col2:
                st.metric("Budget", f"€{row['budget']:.2f}", label_visibility="collapsed")
            with col3:
                st.metric("Used", f"€{row['actual']:.2f}", label_visibility="collapsed")
            with col4:
                st.metric("Left", f"€{row['remaining']:.2f}", label_visibility="collapsed")

with savings_tab:
    st.subheader("💼 Savings Goals")

    credit_col, add_col = st.columns([1.2, 1])

    with credit_col:
        goals_df = get_goals_df()
        if goals_df.empty:
            st.info("No savings goals yet. Create one to start tracking your plans.")
        else:
            total_target = goals_df["target"].sum()
            total_saved = goals_df["saved"].sum()
            total_remaining = total_target - total_saved
            completion_rate = (total_saved / total_target * 100) if total_target > 0 else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("🎯 Total Target", f"€{total_target:.2f}")
            with c2:
                st.metric("💰 Saved", f"€{total_saved:.2f}")
            with c3:
                st.metric("📌 Remaining", f"€{total_remaining:.2f}")

            st.divider()
            st.write(f"**Overall Progress: {completion_rate:.1f}%**")
            st.progress(min(completion_rate / 100, 1.0))

            st.divider()

            for _, row in goals_df.iterrows():
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

    with add_col:
        st.subheader("Create New Goal")
        with st.form("savings_goal_form", clear_on_submit=True):
            goal_name = st.text_input("Goal name")
            goal_target = st.number_input("Target (€)", min_value=0.0, step=50.0)
            goal_description = st.text_input("Description (optional)")
            if st.form_submit_button("Add Goal"):
                if goal_name.strip():
                    save_goal(goal_name, goal_target, goal_description)
                    st.success("Savings goal added.")
                    st.rerun()
                else:
                    st.warning("Please enter a goal name.")

        st.subheader("Add Contribution")
        goals_for_contribution = get_goals_df()
        if goals_for_contribution.empty:
            st.info("Create a savings goal first.")
        else:
            with st.form("goal_contribution_form"):
                selected_goal = st.selectbox(
                    "Choose goal",
                    goals_for_contribution["name"].tolist(),
                )
                contribution = st.number_input("Contribution (€)", min_value=0.0, step=10.0)
                if st.form_submit_button("Add to Goal"):
                    goal_id = int(goals_for_contribution.loc[goals_for_contribution["name"] == selected_goal, "id"].iloc[0])
                    if contribution > 0:
                        add_to_goal(goal_id, contribution)
                        st.success(f"Added €{contribution:.2f} to {selected_goal}.")
                        st.rerun()

        st.subheader("Delete Goal")
        goals_for_delete = get_goals_df()
        if goals_for_delete.empty:
            st.info("Nothing to delete.")
        else:
            goal_to_delete = st.selectbox("Select goal", goals_for_delete["name"].tolist(), key="goal_delete_select")
            if st.button("Delete Selected Goal"):
                goal_id = int(goals_for_delete.loc[goals_for_delete["name"] == goal_to_delete, "id"].iloc[0])
                delete_goal(goal_id)
                st.warning(f"Goal '{goal_to_delete}' deleted.")
                st.rerun()

with transactions_tab:
    st.subheader("📋 All Transactions")
    df = transactions_df.copy()

    if df.empty:
        st.info("No transactions to display. Add some in the sidebar!")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_categories = st.multiselect(
                "Filter by Category",
                df["category"].unique(),
                default=list(df["category"].unique()),
            )
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(df["date"].min().date(), df["date"].max().date()),
            )
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"],
            )

        filtered_df = df[df["category"].isin(selected_categories)].copy()
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df["date"] >= pd.to_datetime(date_range[0]))
                & (filtered_df["date"] <= pd.to_datetime(date_range[1]))
            ]

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

        csv_bytes = export_transactions_csv(filtered_df)
        st.download_button(
            label="📤 Export filtered CSV",
            data=csv_bytes,
            file_name="filtered_transactions.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("✏️ Edit or Delete Transaction")
        if not filtered_df.empty:
            transaction_id = st.selectbox(
                "Choose a transaction",
                filtered_df["id"].tolist(),
                format_func=lambda x: (
                    f"#{x} - {filtered_df.loc[filtered_df['id'] == x, 'category'].iloc[0]} - "
                    f"€{filtered_df.loc[filtered_df['id'] == x, 'amount'].iloc[0]:.2f}"
                ),
            )

            row = filtered_df[filtered_df["id"] == transaction_id].iloc[0]
            transaction_categories = get_all_categories()

            with st.form("edit_transaction_form"):
                edit_amount = st.number_input("Edit Amount (€)", min_value=0.0, value=float(row["amount"]), step=0.01)
                edit_category = st.selectbox(
                    "Edit Category",
                    transaction_categories,
                    index=transaction_categories.index(row["category"]) if row["category"] in transaction_categories else 0,
                )
                edit_description = st.text_input("Edit Description", value=row["description"])
                edit_date = st.date_input("Edit Date", value=row["date"].date())

                col_edit, col_delete = st.columns(2)
                with col_edit:
                    save_edit = st.form_submit_button("💾 Save Changes")
                with col_delete:
                    delete_button = st.form_submit_button("🗑️ Delete")

                if save_edit:
                    update_transaction(transaction_id, edit_amount, edit_category, edit_description, edit_date)
                    st.success("Transaction updated successfully!")
                    st.rerun()

                if delete_button:
                    delete_transaction(transaction_id)
                    st.warning("Transaction deleted.")
                    st.rerun()
        else:
            st.info("No transactions match the current filters.")

        st.divider()
        total = filtered_df[filtered_df["category"] != "Income"]["amount"].sum()
        income = filtered_df[filtered_df["category"] == "Income"]["amount"].sum()
        net = income - total
        count = len(filtered_df)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Spending", f"€{total:.2f}")
        with col2:
            st.metric("Total Income", f"€{income:.2f}")
        with col3:
            st.metric("Net", f"€{net:.2f}")
        with col4:
            st.metric("Transactions", count)

with comparison_tab:
    st.subheader("📊 Category Comparison Over Time")
    
    if transactions_df.empty:
        st.info("Add transactions to see comparisons.")
    else:
        expense_df_comp = transactions_df[transactions_df["category"] != "Income"].copy()
        
        if not expense_df_comp.empty:
            expense_df_comp["month"] = expense_df_comp["date"].dt.to_period("M").astype(str)
            
            category_month = expense_df_comp.groupby(["month", "category"], as_index=False)["amount"].sum()
            
            comparison_chart = alt.Chart(category_month).mark_line(point=True).encode(
                x=alt.X("month:N", title="Month"),
                y=alt.Y("amount:Q", title="Amount (€)"),
                color=alt.Color("category:N", title="Category"),
                tooltip=["month", "category", "amount"],
            ).interactive()
            
            st.altair_chart(comparison_chart, use_container_width=True)
            
            st.divider()
            st.subheader("🎯 Category Ranking by Total Spent")
            
            category_ranking = expense_df_comp.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            
            ranking_chart = alt.Chart(category_ranking).mark_bar().encode(
                y=alt.Y("category:N", sort="-x", title="Category"),
                x=alt.X("amount:Q", title="Total Amount (€)"),
                color=alt.Color("amount:Q", scale=alt.Scale(scheme="blues")),
                tooltip=["category", "amount"],
            ).interactive()
            
            st.altair_chart(ranking_chart, use_container_width=True)

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    💰 Personal Finance Dashboard Pro | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
