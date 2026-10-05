import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Page config
st.set_page_config(
    page_title="💰 Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Data storage using session state
if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "budget" not in st.session_state:
    st.session_state.budget = {
        "Food": 500,
        "Transport": 150,
        "Entertainment": 300,
        "Utilities": 200,
        "Other": 200
    }

# Sidebar for adding transactions
st.sidebar.title("➕ Add Transaction")
with st.sidebar.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
    
    with col2:
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Entertainment", "Utilities", "Other", "Income"]
        )
    
    description = st.text_input("Description")
    date = st.date_input("Date", datetime.now())
    
    submitted = st.form_submit_button("💾 Save Transaction")
    
    if submitted and amount > 0:
        st.session_state.transactions.append({
            "date": date,
            "amount": amount,
            "category": category,
            "description": description
        })
        st.sidebar.success("Transaction saved!")

# Main dashboard
st.title("💰 Personal Finance Dashboard")

# Convert to DataFrame for analysis
if st.session_state.transactions:
    df = pd.DataFrame(st.session_state.transactions)
    df["date"] = pd.to_datetime(df["date"])
else:
    df = pd.DataFrame(columns=["date", "amount", "category", "description"])

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Analytics", "🎯 Budget", "📋 Transactions"])

# ============= TAB 1: OVERVIEW =============
with tab1:
    if len(df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        # Total spending (excluding income)
        total_spending = df[df["category"] != "Income"]["amount"].sum()
        
        # Total income
        total_income = df[df["category"] == "Income"]["amount"].sum()
        
        # Net balance
        net_balance = total_income - total_spending
        
        # Average transaction
        avg_transaction = df[df["category"] != "Income"]["amount"].mean()
        
        with col1:
            st.metric("💸 Total Spending", f"€{total_spending:.2f}")
        with col2:
            st.metric("💵 Total Income", f"€{total_income:.2f}")
        with col3:
            st.metric("💳 Net Balance", f"€{net_balance:.2f}", 
                     delta=f"€{net_balance:.2f}" if net_balance >= 0 else f"-€{abs(net_balance):.2f}")
        with col4:
            st.metric("📊 Avg Transaction", f"€{avg_transaction:.2f}")
        
        st.divider()
        
        # Recent transactions
        st.subheader("📝 Recent Transactions")
        recent = df.sort_values("date", ascending=False).head(10)
        
        display_df = recent.copy()
        display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
        display_df["amount"] = display_df["amount"].apply(lambda x: f"€{x:.2f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("👉 Start by adding your first transaction in the sidebar!")

# ============= TAB 2: ANALYTICS =============
with tab2:
    if len(df) > 0:
        # Expense by category chart
        expense_df = df[df["category"] != "Income"].copy()
        
        if len(expense_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💹 Spending by Category")
                category_summary = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                
                chart = alt.Chart(category_summary.reset_index()).mark_bar().encode(
                    x=alt.X("amount:Q", title="Amount (€)"),
                    y=alt.Y("category:N", sort="-x", title="Category"),
                    color=alt.Color("category:N", legend=None),
                    tooltip=["category", "amount"]
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)
            
            with col2:
                st.subheader("🥧 Category Distribution")
                pie_data = category_summary.reset_index()
                pie_data.columns = ["category", "amount"]
                
                pie_chart = alt.Chart(pie_data).mark_arc().encode(
                    theta="amount:Q",
                    color=alt.Color("category:N", legend=alt.Legend(title="Category")),
                    tooltip=["category", "amount"]
                ).interactive()
                
                st.altair_chart(pie_chart, use_container_width=True)
            
            st.divider()
            
            # Daily spending trend
            st.subheader("📅 Spending Trend (Last 30 days)")
            last_30 = expense_df[expense_df["date"] >= (datetime.now() - timedelta(days=30))]
            
            if len(last_30) > 0:
                daily_spending = last_30.groupby(last_30["date"].dt.date)["amount"].sum().reset_index()
                daily_spending.columns = ["date", "amount"]
                
                trend_chart = alt.Chart(daily_spending).mark_line(point=True, strokeDash=[5, 5]).encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("amount:Q", title="Amount (€)"),
                    tooltip=["date", "amount"]
                ).interactive()
                
                st.altair_chart(trend_chart, use_container_width=True)
    else:
        st.info("Add transactions to see analytics!")

# ============= TAB 3: BUDGET =============
with tab3:
    st.subheader("🎯 Monthly Budget")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("**Set your budget limits for each category:**")
    
    with col2:
        if st.button("🔄 Reset Budget"):
            st.session_state.budget = {
                "Food": 500,
                "Transport": 150,
                "Entertainment": 300,
                "Utilities": 200,
                "Other": 200
            }
            st.rerun()
    
    # Edit budget
    col1, col2, col3, col4, col5 = st.columns(5)
    categories = list(st.session_state.budget.keys())
    
    with col1:
        st.session_state.budget["Food"] = st.number_input("Food (€)", value=st.session_state.budget["Food"], step=10)
    with col2:
        st.session_state.budget["Transport"] = st.number_input("Transport (€)", value=st.session_state.budget["Transport"], step=10)
    with col3:
        st.session_state.budget["Entertainment"] = st.number_input("Entertainment (€)", value=st.session_state.budget["Entertainment"], step=10)
    with col4:
        st.session_state.budget["Utilities"] = st.number_input("Utilities (€)", value=st.session_state.budget["Utilities"], step=10)
    with col5:
        st.session_state.budget["Other"] = st.number_input("Other (€)", value=st.session_state.budget["Other"], step=10)
    
    st.divider()
    
    # Budget vs Actual
    st.subheader("📊 Budget vs Actual Spending")
    
    current_month = df[df["date"].dt.month == datetime.now().month]
    
    budget_data = []
    for category in categories:
        actual = current_month[current_month["category"] == category]["amount"].sum()
        budget = st.session_state.budget[category]
        remaining = budget - actual
        used_percent = (actual / budget * 100) if budget > 0 else 0
        
        budget_data.append({
            "category": category,
            "budget": budget,
            "actual": actual,
            "remaining": remaining,
            "used_percent": used_percent
        })
    
    budget_df = pd.DataFrame(budget_data)
    
    for idx, row in budget_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Progress bar with color based on usage
            if row["used_percent"] > 100:
                color = "🔴"
                bg_color = "#ff6b6b"
            elif row["used_percent"] > 75:
                color = "🟡"
                bg_color = "#ffd93d"
            else:
                color = "🟢"
                bg_color = "#6bcf7f"
            
            st.write(f"{color} **{row['category']}**")
            st.progress(min(row["used_percent"] / 100, 1.0))
        
        with col2:
            st.metric("Budget", f"€{row['budget']:.2f}", label_visibility="collapsed")
        
        with col3:
            st.metric("Used", f"€{row['actual']:.2f}", label_visibility="collapsed")
        
        with col4:
            st.metric("Left", f"€{row['remaining']:.2f}", label_visibility="collapsed")

# ============= TAB 4: TRANSACTIONS =============
with tab4:
    st.subheader("📋 All Transactions")
    
    if len(df) > 0:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_category = st.multiselect(
                "Filter by Category",
                df["category"].unique(),
                default=df["category"].unique()
            )
        
        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(df["date"].min().date(), df["date"].max().date()),
                key="date_range"
            )
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])
        
        # Apply filters
        filtered_df = df[df["category"].isin(selected_category)].copy()
        
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df["date"] >= pd.to_datetime(date_range[0])) &
                (filtered_df["date"] <= pd.to_datetime(date_range[1]))
            ]
        
        # Sort
        if sort_by == "Date (newest)":
            filtered_df = filtered_df.sort_values("date", ascending=False)
        elif sort_by == "Date (oldest)":
            filtered_df = filtered_df.sort_values("date", ascending=True)
        elif sort_by == "Amount (high)":
            filtered_df = filtered_df.sort_values("amount", ascending=False)
        else:
            filtered_df = filtered_df.sort_values("amount", ascending=True)
        
        # Display
        display_df = filtered_df.copy()
        display_df["date"] = display_df["date"].dt.strftime("%d/%m/%Y")
        display_df["amount"] = display_df["amount"].apply(lambda x: f"€{x:.2f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary statistics for filtered data
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
    else:
        st.info("No transactions to display. Add some in the sidebar!")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    💰 Personal Finance Dashboard | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
