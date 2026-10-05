import html
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from analytics import (
    calculate_budget_summary,
    export_transactions_csv,
    forecast_spending,
    get_monthly_spending,
    get_spending_insights,
)
from auth_manager import (
    get_user_settings,
    init_auth_db,
    login_user,
    register_user,
    update_user_settings,
)
from db import (
    DEFAULT_BUDGETS,
    add_custom_category,
    add_to_goal,
    delete_goal,
    delete_transaction,
    get_all_categories,
    get_budget_df,
    get_goals_df,
    get_transactions_df,
    init_db,
    save_budget,
    save_goal,
    save_transaction,
    update_transaction,
)
from theme import THEMES, apply_theme, style_chart


def render_add_transaction(user_id, prefix, show_category_manager):
    st.subheader("➕ Add transaction")
    with st.form(f"{prefix}_transaction_form", clear_on_submit=True):
        amount = st.number_input(
            "Amount (€)", min_value=0.0, value=0.0, step=0.01, key=f"{prefix}_amount"
        )
        category = st.selectbox("Category", get_all_categories(user_id), key=f"{prefix}_category")
        description = st.text_input("Description", key=f"{prefix}_description")
        date_value = st.date_input("Date", datetime.now(), key=f"{prefix}_date")
        submitted = st.form_submit_button(
            "💾 Save transaction", key=f"{prefix}_submit"
        )
        if submitted:
            if amount <= 0:
                st.warning("Amount must be greater than 0")
            else:
                save_transaction(user_id, amount, category, description, date_value)
                st.session_state.app_toast = "Transaction saved successfully!"
                st.rerun()

    if show_category_manager:
        with st.expander("🏷️ Manage categories"):
            new_category = st.text_input("New category", key=f"{prefix}_new_category")
            new_emoji = st.selectbox(
                "Emoji",
                ["🍔", "🚗", "🎬", "💡", "🏃", "🛍️", "📚", "📺", "✈️", "💅", "📦", "🏥", "🎮", "📱", "👕"],
                key=f"{prefix}_new_emoji",
            )
            if st.button("Add category", key=f"{prefix}_add_category"):
                if not new_category.strip():
                    st.warning("Enter a category name.")
                elif len(new_category.strip()) > 40:
                    st.warning("Category names must be 40 characters or fewer.")
                elif new_category.strip().casefold() == "income":
                    st.warning("Income is a reserved category.")
                elif add_custom_category(user_id, new_category, new_emoji):
                    save_budget(user_id, new_category, 100.0)
                    st.session_state.app_toast = "Category added."
                    st.rerun()
                else:
                    st.warning("That category already exists.")


def render_transactions_list(user_id, transactions_df):
    st.subheader("📋 All transactions")
    df = transactions_df.copy()
    if df.empty:
        st.info("No transactions to display yet.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_categories = st.multiselect(
            "Filter by category",
            df["category"].unique(),
            default=list(df["category"].unique()),
        )
    with col2:
        date_range = st.date_input(
            "Date range",
            value=(df["date"].min().date(), df["date"].max().date()),
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"],
        )

    filtered_df = df[df["category"].isin(selected_categories)].copy()
    if len(date_range) == 2:
        transaction_dates = filtered_df["date"].dt.date
        filtered_df = filtered_df[
            (transaction_dates >= date_range[0]) & (transaction_dates <= date_range[1])
        ]

    sort_options = {
        "Date (newest)": ("date", False),
        "Date (oldest)": ("date", True),
        "Amount (high)": ("amount", False),
        "Amount (low)": ("amount", True),
    }
    sort_column, ascending = sort_options[sort_by]
    filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
    display_df = filtered_df[["date", "amount", "category", "description"]].copy()
    display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
    display_df["amount"] = display_df["amount"].apply(lambda value: f"€{value:.2f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.download_button(
        "📤 Export filtered CSV",
        export_transactions_csv(filtered_df),
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )

    st.divider()
    st.subheader("✏️ Edit or delete transaction")
    if not filtered_df.empty:
        transaction_id = st.selectbox(
            "Choose transaction",
            filtered_df["id"].tolist(),
            format_func=lambda value: (
                f"#{value} - "
                f"{filtered_df.loc[filtered_df['id'] == value, 'category'].iloc[0]} - "
                f"€{filtered_df.loc[filtered_df['id'] == value, 'amount'].iloc[0]:.2f}"
            ),
            key="edit_transaction_id",
        )
        row = filtered_df[filtered_df["id"] == transaction_id].iloc[0]
        transaction_categories = get_all_categories(user_id)
        with st.form("edit_transaction_form"):
            edit_amount = st.number_input(
                "Edit amount (€)",
                min_value=0.0,
                value=float(row["amount"]),
                step=0.01,
                key=f"edit_amount_{transaction_id}",
            )
            edit_category = st.selectbox(
                "Edit category",
                transaction_categories,
                index=(
                    transaction_categories.index(row["category"])
                    if row["category"] in transaction_categories
                    else 0
                ),
                key=f"edit_category_{transaction_id}",
            )
            edit_description = st.text_input(
                "Edit description",
                value=row["description"],
                key=f"edit_description_{transaction_id}",
            )
            edit_date = st.date_input(
                "Edit date",
                value=row["date"].date(),
                key=f"edit_date_{transaction_id}",
            )
            col_edit, col_delete = st.columns(2)
            with col_edit:
                save_edit = st.form_submit_button("💾 Save changes")
            with col_delete:
                delete_button = st.form_submit_button("🗑️ Delete")

            if save_edit:
                update_transaction(
                    user_id,
                    transaction_id,
                    edit_amount,
                    edit_category,
                    edit_description,
                    edit_date,
                )
                st.session_state.app_toast = "Transaction updated successfully!"
                st.rerun()
            if delete_button:
                delete_transaction(user_id, transaction_id)
                st.session_state.app_toast = "Transaction deleted."
                st.rerun()

    st.divider()
    total = filtered_df[filtered_df["category"] != "Income"]["amount"].sum()
    income = filtered_df[filtered_df["category"] == "Income"]["amount"].sum()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total spending", f"€{total:.2f}")
    with col2:
        st.metric("Total income", f"€{income:.2f}")
    with col3:
        st.metric("Net", f"€{income - total:.2f}")
    with col4:
        st.metric("Transactions", len(filtered_df))


st.set_page_config(page_title="Finance Dashboard Pro", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
init_auth_db()
init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = ""


def show_auth_page():
    st.title("💰 Finance Dashboard Pro")
    st.write("Login to access your private financial dashboard.")
    auth_tab, register_tab = st.tabs(["Login", "Register"])

    with auth_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", key="login_submit")
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
            reg_username = st.text_input("Choose username", key="register_username")
            reg_email = st.text_input("Email", key="register_email")
            reg_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm password", type="password", key="register_confirm_password")
            submitted = st.form_submit_button("Create account", key="register_submit")
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
settings = get_user_settings(user_id)
if st.session_state.get("theme_user_id") != user_id:
    st.session_state.theme = settings.get("theme", "light")
    st.session_state.theme_user_id = user_id

with st.sidebar:
    st.title(f"👋 {username}")
    st.caption("Private finance dashboard")

    st.subheader("Settings")
    theme = st.selectbox("Theme", ["light", "dark"], key="theme")
    notifications_enabled = st.checkbox("Enable notifications", value=bool(settings.get("notifications_enabled", 1)))
    if st.button("Save settings"):
        update_user_settings(user_id, {"theme": theme, "notifications_enabled": int(notifications_enabled)})
        st.success("Settings saved")

    st.divider()
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.theme_user_id = None
        st.rerun()

apply_theme()
toast_message = st.session_state.pop("app_toast", None)
if toast_message:
    st.toast(toast_message)

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
    now = datetime.now()
    current_month = transactions_df[
        (transactions_df["date"].dt.month == now.month)
        & (transactions_df["date"].dt.year == now.year)
    ]
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
    st.metric("📈 30-day forecast", f"€{forecast:.2f}" if forecast is not None else "Not enough data")
    if forecast is None:
        st.caption("Forecast available after 7 days with expenses.")

if not transactions_df.empty:
    st.divider()
    st.subheader("🔍 Smart insights")
    for insight in get_spending_insights(transactions_df):
        st.markdown(f"<div class='insight-box'>{html.escape(insight)}</div>", unsafe_allow_html=True)

st.divider()
overview_tab, analytics_tab, transactions_tab, budget_tab, savings_tab = st.tabs(
    ["Overview", "Analytics", "Transactions", "Budget", "Savings"]
)

with overview_tab:
    with st.expander("➕ Add transaction"):
        render_add_transaction(user_id, "ov", show_category_manager=False)

    st.subheader("📝 Recent transactions")
    if transactions_df.empty:
        st.info("Add your first transaction to start tracking your finances.")
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
                color=alt.value(THEMES[st.session_state.get("theme", "light")]["accent"]),
            ).interactive()
            st.altair_chart(style_chart(trend_chart), use_container_width=True)

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
                st.altair_chart(style_chart(chart), use_container_width=True)
            with c2:
                st.subheader("🥧 Category distribution")
                pie_chart = alt.Chart(category_summary).mark_arc().encode(
                    theta="amount:Q",
                    color=alt.Color("category:N", legend=alt.Legend(title="Category")),
                    tooltip=["category", "amount"],
                ).interactive()
                st.altair_chart(style_chart(pie_chart), use_container_width=True)

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

with transactions_tab:
    render_add_transaction(user_id, "tx", show_category_manager=True)
    render_transactions_list(user_id, transactions_df)

with budget_tab:
    st.subheader("🎯 Monthly budget")
    budget_df = get_budget_df(user_id)
    if budget_df.empty:
        for category, value in DEFAULT_BUDGETS.items():
            save_budget(user_id, category, value)
        budget_df = get_budget_df(user_id)

    budget_values = {}
    for _, row in budget_df.iterrows():
        budget_values[row["category"]] = st.number_input(
            f"{row['category']} (€)",
            min_value=0.0,
            value=float(row["value"]),
            step=10.0,
            key=f"budget_{user_id}_{row['category']}",
        )

    if st.button("💾 Save budget"):
        for category, value in budget_values.items():
            save_budget(user_id, category, value)
        st.session_state.app_toast = "Budget updated successfully!"
        st.rerun()

    if st.button("🔄 Reset budget"):
        for category, value in DEFAULT_BUDGETS.items():
            save_budget(user_id, category, value)
        st.session_state.app_toast = "Budget reset to default values."
        st.rerun()

    st.divider()
    st.subheader("📊 Budget vs actual spending")
    now = datetime.now()
    current_month_df = (
        transactions_df[
            (transactions_df["date"].dt.month == now.month)
            & (transactions_df["date"].dt.year == now.year)
        ].copy()
        if not transactions_df.empty
        else pd.DataFrame(columns=["id", "date", "amount", "category", "description"])
    )
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
        goal_target = st.number_input("Target (€)", min_value=0.0, value=0.0, step=50.0)
        goal_description = st.text_input("Description (optional)")
        if st.form_submit_button("Add goal"):
            if goal_target <= 0:
                st.warning("Target amount must be greater than 0.")
            elif goal_name.strip():
                try:
                    save_goal(user_id, goal_name, goal_target, goal_description)
                except sqlite3.IntegrityError:
                    st.error("A goal with that name already exists.")
                else:
                    st.session_state.app_toast = "Goal added successfully."
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
            contribution = st.number_input("Contribution (€)", min_value=0.0, value=0.0, step=10.0)
            if st.form_submit_button("Add to goal"):
                goal_id = int(goals_for_contribution.loc[goals_for_contribution["name"] == selected_goal, "id"].iloc[0])
                if contribution > 0:
                    add_to_goal(user_id, goal_id, contribution)
                    st.session_state.app_toast = f"Added €{contribution:.2f} to {selected_goal}."
                    st.rerun()
                else:
                    st.warning("Contribution must be greater than 0.")

    st.subheader("Delete goal")
    goals_for_delete = get_goals_df(user_id)
    if goals_for_delete.empty:
        st.info("Nothing to delete.")
    else:
        goal_to_delete = st.selectbox("Select goal", goals_for_delete["name"].tolist(), key="goal_delete_select")
        if st.button("Delete selected goal"):
            goal_id = int(goals_for_delete.loc[goals_for_delete["name"] == goal_to_delete, "id"].iloc[0])
            delete_goal(user_id, goal_id)
            st.session_state.app_toast = f"Goal '{goal_to_delete}' deleted."
            st.rerun()

st.divider()
st.markdown(
    """
    <div style='text-align: center; opacity: 0.65; font-size: 12px;'>
    💰 Finance Dashboard Pro | Personal private account | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
