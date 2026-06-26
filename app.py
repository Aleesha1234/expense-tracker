

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

import utils

# Page configuration  (must be the very first Streamlit call)

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS tweaks

st.markdown("""
<style>
/* Metric card borders */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e0e6ed;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,.06);
}
/* Sidebar title */
.sidebar-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e2a38;
    margin-bottom: 0.25rem;
}
/* Section headers */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 2px solid #2980b9;
    padding-bottom: 4px;
    margin-bottom: 12px;
}
/* Success / error banner */
div[data-baseweb="notification"] {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# Helpers

def fmt_currency(value: float) -> str:
    """Format a float as a Rupee amount string, e.g. Rs. 1,234.50"""
    return f"Rs. {value:,.2f}"


def _delta_color(value: float) -> str:
    """Map a numeric delta to a Streamlit metric delta_color string."""
    if value > 0:
        return "normal"
    if value < 0:
        return "inverse"
    return "off"

# Sidebar navigation

with st.sidebar:
    st.markdown('<p class="sidebar-title">💰 Expense Tracker</p>', unsafe_allow_html=True)
    st.caption("Manage your personal finances")
    st.divider()

    page = st.radio(
        "Navigate",
        options=[
            "📊  Dashboard",
            "➕  Add Transaction",
            "📋  Transactions",
            "📈  Charts",
            "💾  Export",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Quick stats in sidebar
    df_sidebar = utils.load_data()
    summary    = utils.get_summary(df_sidebar)
    st.caption(f"**Balance:** {fmt_currency(summary['balance'])}")
    st.caption(f"**Transactions:** {len(df_sidebar)}")


# Initialise CSV on every run (no-op if already exists)

utils.initialize_csv()


# PAGE: Dashboard

if page == "📊  Dashboard":

    st.title("📊 Dashboard")
    st.caption("A snapshot of your financial position.")
    st.divider()

    df      = utils.load_data()
    summary = utils.get_summary(df)

    # --- KPI Cards -----------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="💵 Total Income",
            value=fmt_currency(summary["total_income"]),
        )
    with col2:
        st.metric(
            label="💸 Total Expenses",
            value=fmt_currency(summary["total_expenses"]),
        )
    with col3:
        balance = summary["balance"]
        st.metric(
            label="🏦 Current Balance",
            value=fmt_currency(balance),
            delta=fmt_currency(balance),
            delta_color=_delta_color(balance),
        )

    st.divider()

    # --- Income vs Expense bar (monthly overview) ---------------------------
    monthly = utils.monthly_income_vs_expense(df)

    if monthly.empty:
        st.info("No transactions yet. Use **➕ Add Transaction** to get started.")
    else:
        st.markdown('<p class="section-header">Monthly Income vs Expenses</p>',
                    unsafe_allow_html=True)

        fig = px.bar(
            monthly,
            x="month",
            y="amount",
            color="type",
            barmode="group",
            color_discrete_map={"Income": "#27ae60", "Expense": "#e74c3c"},
            labels={"month": "Month", "amount": "Amount (Rs.)", "type": ""},
            text_auto=".2s",
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Recent transactions table ------------------------------------
        st.markdown('<p class="section-header">Recent Transactions</p>',
                    unsafe_allow_html=True)

        recent = df.sort_values("date", ascending=False).head(5).copy()
        recent["date"]   = recent["date"].dt.strftime("%d %b %Y")
        recent["amount"] = recent["amount"].apply(fmt_currency)
        recent = recent[["date", "type", "category", "amount", "description"]]
        recent.columns   = ["Date", "Type", "Category", "Amount", "Description"]

        st.dataframe(recent, use_container_width=True, hide_index=True)


# PAGE: Add Transaction
elif page == "➕  Add Transaction":

    st.title("➕ Add Transaction")
    st.caption("Record a new income or expense entry.")
    st.divider()

    with st.form("add_transaction_form", clear_on_submit=True):

        col_left, col_right = st.columns(2)

        with col_left:
            txn_type = st.selectbox(
                "Transaction Type *",
                options=["Expense", "Income"],
                help="Select whether this is money coming in or going out.",
            )

            amount = st.number_input(
                "Amount (Rs.) *",
                min_value=0.01,
                max_value=10_000_000.0,
                value=100.0,
                step=0.01,
                format="%.2f",
                help="Enter the transaction amount.",
            )

            txn_date = st.date_input(
                "Date *",
                value=date.today(),
                max_value=date.today(),
                help="Transaction date (cannot be in the future).",
            )

        with col_right:
            # Show the relevant category list based on transaction type
            categories = (
                utils.INCOME_CATEGORIES
                if txn_type == "Income"
                else utils.EXPENSE_CATEGORIES
            )
            category = st.selectbox(
                "Category *",
                options=categories,
                help="Choose the category that best fits this transaction.",
            )

            description = st.text_area(
                "Description",
                placeholder="Optional — e.g. 'Monthly grocery run'",
                max_chars=200,
                height=120,
                help="Add a short note about this transaction.",
            )

        st.divider()
        submitted = st.form_submit_button(
            "💾 Save Transaction",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            utils.add_transaction(
                txn_type=txn_type,
                category=category,
                amount=amount,
                txn_date=txn_date,
                description=description,
            )
            st.success(
                f"✅ {txn_type} of **{fmt_currency(amount)}** "
                f"({category}) saved successfully!"
            )
            st.balloons()


# PAGE: Transactions
elif page == "📋  Transactions":

    st.title("📋 Transactions")
    st.caption("Browse, search, filter, and delete your transaction history.")
    st.divider()

    df = utils.load_data()

    if df.empty:
        st.info("No transactions yet. Use **➕ Add Transaction** to get started.")
    else:
        # --- Filters --------------------------------------------------------
        all_categories = sorted(df["category"].unique().tolist())

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 2, 2, 2])

        with filter_col1:
            keyword = st.text_input("🔍 Search", placeholder="Keyword in description or category")

        with filter_col2:
            txn_type_filter = st.selectbox("Type", ["All", "Income", "Expense"])

        with filter_col3:
            category_filter = st.selectbox("Category", ["All"] + all_categories)

        with filter_col4:
            sort_order = st.selectbox("Sort", ["Newest First", "Oldest First"])

        # --- Apply filters --------------------------------------------------
        filtered = utils.filter_transactions(
            df,
            txn_type=txn_type_filter,
            category=category_filter,
            keyword=keyword,
            sort_order=sort_order,
        )

        st.caption(f"Showing **{len(filtered)}** of **{len(df)}** transactions.")
        st.divider()

        if filtered.empty:
            st.warning("No transactions match your filters.")
        else:
            # --- Display table ----------------------------------------------
            display = filtered.copy()
            display["date"] = display["date"].dt.strftime("%d %b %Y")

            # Colour-code the type column
            def _style_type(val):
                color = "#27ae60" if val == "Income" else "#e74c3c"
                return f"color: {color}; font-weight: 600;"

            styled = (
                display[["id", "date", "type", "category", "amount", "description"]]
                .rename(columns={
                    "id": "ID", "date": "Date", "type": "Type",
                    "category": "Category", "amount": "Amount (Rs.)",
                    "description": "Description",
                })
                .style.map(_style_type, subset=["Type"])
                .format({"Amount (Rs.)": "{:,.2f}"})
            )

            st.dataframe(styled, use_container_width=True, hide_index=True)

            # --- Delete section ---------------------------------------------
            st.divider()
            st.markdown('<p class="section-header">Delete a Transaction</p>',
                        unsafe_allow_html=True)

            available_ids = filtered["id"].tolist()
            del_col1, del_col2 = st.columns([3, 1])

            with del_col1:
                del_id = st.selectbox(
                    "Select Transaction ID to delete",
                    options=available_ids,
                    format_func=lambda i: (
                        f"ID {i}  —  "
                        + filtered.loc[filtered['id'] == i, 'date'].dt.strftime('%d %b %Y').values[0]
                        + "  "
                        + filtered.loc[filtered['id'] == i, 'type'].values[0]
                        + "  Rs. "
                        + f"{filtered.loc[filtered['id'] == i, 'amount'].values[0]:,.2f}"
                        + "  ("
                        + filtered.loc[filtered['id'] == i, 'category'].values[0]
                        + ")"
                    ),
                )

            with del_col2:
                st.write("")   # vertical alignment spacer
                st.write("")
                if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                    utils.delete_transaction(del_id)
                    st.success(f"Transaction ID {del_id} deleted.")
                    st.rerun()


# PAGE: Charts
elif page == "📈  Charts":

    st.title("📈 Charts")
    st.caption("Visualise where your money goes.")
    st.divider()

    df = utils.load_data()

    if df.empty:
        st.info("No transactions yet. Add some data to see your charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        # --- Pie chart: Expenses by Category --------------------------------
        with chart_col1:
            st.markdown('<p class="section-header">Expenses by Category</p>',
                        unsafe_allow_html=True)

            cat_data = utils.expense_by_category(df)

            if cat_data.empty:
                st.info("No expense data available yet.")
            else:
                fig_pie = px.pie(
                    cat_data,
                    names="category",
                    values="amount",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    hole=0.4,
                )
                fig_pie.update_traces(
                    textposition="outside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>Rs. %{value:,.2f}<br>%{percent}",
                )
                fig_pie.update_layout(
                    showlegend=True,
                    legend=dict(orientation="v", x=1.05),
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_pie, use_container_width=True)

                # Top category callout
                top = cat_data.iloc[0]
                st.info(
                    f"💡 Highest spend category: **{top['category']}** "
                    f"({fmt_currency(top['amount'])})"
                )

        # --- Bar chart: Monthly Expenses ------------------------------------
        with chart_col2:
            st.markdown('<p class="section-header">Monthly Expenses</p>',
                        unsafe_allow_html=True)

            monthly = utils.monthly_expenses(df)

            if monthly.empty:
                st.info("No expense data available yet.")
            else:
                fig_bar = px.bar(
                    monthly,
                    x="month",
                    y="amount",
                    color="amount",
                    color_continuous_scale=["#fad7a0", "#e74c3c"],
                    labels={"month": "Month", "amount": "Total Expenses (Rs.)"},
                    text_auto=".2s",
                )
                fig_bar.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis=dict(tickangle=-30),
                )
                fig_bar.update_traces(
                    marker_line_color="#c0392b",
                    marker_line_width=1.2,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # Month with highest expense
                peak = monthly.loc[monthly["amount"].idxmax()]
                st.info(
                    f"💡 Peak spending month: **{peak['month']}** "
                    f"({fmt_currency(peak['amount'])})"
                )

        # --- Income vs Expense over time (full-width) ----------------------
        st.divider()
        st.markdown('<p class="section-header">Income vs Expenses — Monthly Comparison</p>',
                    unsafe_allow_html=True)

        iv_e = utils.monthly_income_vs_expense(df)

        if iv_e.empty:
            st.info("Not enough data for a comparison chart.")
        else:
            fig_cmp = px.bar(
                iv_e,
                x="month",
                y="amount",
                color="type",
                barmode="group",
                color_discrete_map={"Income": "#27ae60", "Expense": "#e74c3c"},
                labels={"month": "Month", "amount": "Amount (Rs.)", "type": ""},
                text_auto=".2s",
            )
            fig_cmp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis=dict(tickangle=-30),
            )
            st.plotly_chart(fig_cmp, use_container_width=True)


# PAGE: Export
elif page == "💾  Export":

    st.title("💾 Export Data")
    st.caption("Download your transaction history as a CSV file.")
    st.divider()

    df = utils.load_data()

    if df.empty:
        st.info("No transactions to export yet.")
    else:
        st.markdown('<p class="section-header">Export Preview</p>',
                    unsafe_allow_html=True)

        preview = df.copy()
        preview["date"]   = preview["date"].dt.strftime("%Y-%m-%d")
        preview["amount"] = preview["amount"].apply(lambda x: f"{x:,.2f}")

        st.dataframe(preview, use_container_width=True, hide_index=True)

        st.divider()

        # Summary before download
        summary = utils.get_summary(df)
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        exp_col1.metric("Total Rows",     len(df))
        exp_col2.metric("Date Range",
                        f"{df['date'].min().strftime('%d %b %Y')} → "
                        f"{df['date'].max().strftime('%d %b %Y')}")
        exp_col3.metric("Net Balance",    fmt_currency(summary["balance"]))

        st.divider()

        # Download button
        csv_bytes = utils.export_csv_bytes(df)
        filename  = f"expenses_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"

        st.download_button(
            label="⬇️  Download CSV",
            data=csv_bytes,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            type="primary",
        )

        st.caption(
            f"File will be saved as **{filename}** — "
            f"{len(csv_bytes):,} bytes."
        )
