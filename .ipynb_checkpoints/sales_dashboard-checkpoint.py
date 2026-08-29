import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Sales & Profit Optimization",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    df = pd.read_csv(
        "Superstore.csv",
        encoding="latin1"
    )

    df.columns = df.columns.str.strip()

    df["Order Date"] = pd.to_datetime(
        df["Order Date"]
    )

    df["Ship Date"] = pd.to_datetime(
        df["Ship Date"]
    )

    # Additional calculated columns
    df["Profit Margin"] = np.where(
        df["Sales"] != 0,
        (df["Profit"] / df["Sales"]) * 100,
        0
    )

    df["Shipping Days"] = (
        df["Ship Date"] -
        df["Order Date"]
    ).dt.days

    return df


df = load_data()

# ============================================================
# TITLE
# ============================================================

st.title("📊 Sales & Profit Optimization Dashboard")

st.markdown(
    """
    **Business objective:** Identify revenue drivers, 
    profitability problems, discount risks and 
    opportunities for business improvement.
    """
)

# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Dashboard Filters")

# Date filter
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Region
selected_regions = st.sidebar.multiselect(
    "Region",
    sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique())
)

# Category
selected_categories = st.sidebar.multiselect(
    "Category",
    sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)

# Segment
selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    sorted(df["Segment"].unique()),
    default=sorted(df["Segment"].unique())
)

# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df[
    (df["Order Date"].dt.date >= date_range[0]) &
    (df["Order Date"].dt.date <= date_range[1]) &
    (df["Region"].isin(selected_regions)) &
    (df["Category"].isin(selected_categories)) &
    (df["Segment"].isin(selected_segments))
].copy()

# ============================================================
# CHECK DATA
# ============================================================

if filtered_df.empty:

    st.warning(
        "No data matches the selected filters."
    )

    st.stop()

# ============================================================
# KPI CALCULATIONS
# ============================================================

total_sales = filtered_df["Sales"].sum()

total_profit = filtered_df["Profit"].sum()

total_orders = filtered_df["Order ID"].nunique()

total_customers = filtered_df["Customer ID"].nunique()

profit_margin = (
    total_profit / total_sales * 100
    if total_sales != 0
    else 0
)

average_order_value = (
    total_sales / total_orders
    if total_orders != 0
    else 0
)

# ============================================================
# KPI ROW
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "💰 Revenue",
    f"${total_sales:,.0f}"
)

col2.metric(
    "💵 Profit",
    f"${total_profit:,.0f}"
)

col3.metric(
    "📦 Orders",
    f"{total_orders:,}"
)

col4.metric(
    "👥 Customers",
    f"{total_customers:,}"
)

col5.metric(
    "📊 Profit Margin",
    f"{profit_margin:.2f}%"
)

st.divider()

# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.header("📈 Executive Overview")

# Monthly analysis

filtered_df["Month"] = (
    filtered_df["Order Date"]
    .dt.to_period("M")
    .astype(str)
)

monthly = (
    filtered_df
    .groupby("Month")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=monthly["Month"],
        y=monthly["Sales"],
        mode="lines+markers",
        name="Sales"
    )
)

fig.add_trace(
    go.Scatter(
        x=monthly["Month"],
        y=monthly["Profit"],
        mode="lines+markers",
        name="Profit"
    )
)

fig.update_layout(
    title="Sales vs Profit Over Time",
    xaxis_title="Month",
    yaxis_title="Amount"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ============================================================
# CATEGORY PERFORMANCE
# ============================================================

st.header("🛍️ Category Profitability")

category = (
    filtered_df
    .groupby("Category")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

category["Profit Margin"] = (
    category["Profit"] /
    category["Sales"] *
    100
)

col1, col2 = st.columns(2)

fig_category = px.bar(
    category,
    x="Category",
    y="Sales",
    color="Category",
    title="Sales by Category",
    text_auto=".2s"
)

col1.plotly_chart(
    fig_category,
    use_container_width=True
)

fig_margin = px.bar(
    category,
    x="Category",
    y="Profit Margin",
    color="Category",
    title="Profit Margin by Category",
    text_auto=".1f"
)

col2.plotly_chart(
    fig_margin,
    use_container_width=True
)

# ============================================================
# PRODUCT PERFORMANCE MATRIX
# ============================================================

st.header("🎯 Product Performance")

product = (
    filtered_df
    .groupby("Product Name")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum")
    )
    .reset_index()
)

product["Profit Margin"] = (
    product["Profit"] /
    product["Sales"] *
    100
)

# Performance classification

sales_median = product["Sales"].median()
profit_median = product["Profit"].median()

def classify_product(row):

    if (
        row["Sales"] >= sales_median
        and row["Profit"] >= profit_median
    ):
        return "⭐ Star"

    elif (
        row["Sales"] >= sales_median
        and row["Profit"] < profit_median
    ):
        return "⚠️ High Sales / Low Profit"

    elif (
        row["Sales"] < sales_median
        and row["Profit"] >= profit_median
    ):
        return "💎 High Profit / Low Sales"

    else:
        return "❓ Low Priority"


product["Performance"] = (
    product.apply(
        classify_product,
        axis=1
    )
)

fig_product = px.scatter(
    product,
    x="Sales",
    y="Profit",
    size="Quantity",
    color="Performance",
    hover_name="Product Name",
    title="Product Sales vs Profit",
    log_x=True
)

fig_product.update_layout(
    xaxis_title="Sales",
    yaxis_title="Profit"
)

st.plotly_chart(
    fig_product,
    use_container_width=True
)

# ============================================================
# TOP PRODUCTS
# ============================================================

col1, col2 = st.columns(2)

top_sales = (
    product
    .sort_values(
        "Sales",
        ascending=False
    )
    .head(10)
)

fig_top_sales = px.bar(
    top_sales.sort_values("Sales"),
    x="Sales",
    y="Product Name",
    orientation="h",
    title="🏆 Top 10 Products by Sales",
    text_auto=".2s"
)

col1.plotly_chart(
    fig_top_sales,
    use_container_width=True
)

top_profit = (
    product
    .sort_values(
        "Profit",
        ascending=False
    )
    .head(10)
)

fig_top_profit = px.bar(
    top_profit.sort_values("Profit"),
    x="Profit",
    y="Product Name",
    orientation="h",
    title="💰 Top 10 Products by Profit",
    text_auto=".2s"
)

col2.plotly_chart(
    fig_top_profit,
    use_container_width=True
)

# ============================================================
# DISCOUNT ANALYSIS
# ============================================================

st.header("🏷️ Discount & Profitability Analysis")

discount = (
    filtered_df
    .groupby("Discount")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique")
    )
    .reset_index()
)

fig_discount = px.scatter(
    discount,
    x="Discount",
    y="Profit",
    size="Sales",
    hover_data=["Orders"],
    title="Discount vs Profit"
)

fig_discount.update_layout(
    xaxis_title="Discount",
    yaxis_title="Profit"
)

st.plotly_chart(
    fig_discount,
    use_container_width=True
)

# ============================================================
# LOSS-MAKING PRODUCTS
# ============================================================

st.subheader("🚨 Loss-Making Products")

loss_products = (
    product[
        product["Profit"] < 0
    ]
    .sort_values(
        "Profit"
    )
    .head(10)
)

if not loss_products.empty:

    st.dataframe(
        loss_products[
            [
                "Product Name",
                "Sales",
                "Profit",
                "Profit Margin"
            ]
        ],
        use_container_width=True
    )

else:

    st.success(
        "No loss-making products found "
        "for the selected filters."
    )

# ============================================================
# CUSTOMER ANALYSIS
# ============================================================

st.header("👥 Customer Analysis")

customer = (
    filtered_df
    .groupby(
        [
            "Customer ID",
            "Customer Name"
        ]
    )
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique")
    )
    .reset_index()
)

customer["Profit Margin"] = (
    customer["Profit"] /
    customer["Sales"] *
    100
)

col1, col2 = st.columns(2)

top_customers = (
    customer
    .sort_values(
        "Sales",
        ascending=False
    )
    .head(10)
)

fig_customer = px.bar(
    top_customers.sort_values("Sales"),
    x="Sales",
    y="Customer Name",
    orientation="h",
    title="🏆 Top 10 Customers by Revenue",
    text_auto=".2s"
)

col1.plotly_chart(
    fig_customer,
    use_container_width=True
)

segment = (
    filtered_df
    .groupby("Segment")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

fig_segment = px.pie(
    segment,
    names="Segment",
    values="Sales",
    title="Customer Segment Revenue"
)

col2.plotly_chart(
    fig_segment,
    use_container_width=True
)

# ============================================================
# REGIONAL ANALYSIS
# ============================================================

st.header("🌎 Regional Performance")

region = (
    filtered_df
    .groupby("Region")
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

region["Profit Margin"] = (
    region["Profit"] /
    region["Sales"] *
    100
)

fig_region = px.bar(
    region,
    x="Region",
    y="Profit",
    color="Profit Margin",
    title="Regional Profitability",
    text_auto=".2s"
)

st.plotly_chart(
    fig_region,
    use_container_width=True
)

# ============================================================
# SHIPPING ANALYSIS
# ============================================================

st.header("🚚 Shipping Performance")

shipping = (
    filtered_df
    .groupby("Ship Mode")
    .agg(
        Orders=("Order ID", "nunique"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Shipping_Days=("Shipping Days", "mean")
    )
    .reset_index()
)

fig_shipping = px.bar(
    shipping,
    x="Ship Mode",
    y="Avg_Shipping_Days",
    color="Ship Mode",
    title="Average Shipping Time by Ship Mode",
    text_auto=".1f"
)

st.plotly_chart(
    fig_shipping,
    use_container_width=True
)

# ============================================================
# AUTOMATIC BUSINESS INSIGHTS
# ============================================================

st.header("💡 Business Insights")

best_category = (
    category
    .sort_values(
        "Profit",
        ascending=False
    )
    .iloc[0]
)

worst_category = (
    category
    .sort_values(
        "Profit"
    )
    .iloc[0]
)

best_region = (
    region
    .sort_values(
        "Profit",
        ascending=False
    )
    .iloc[0]
)

best_product = (
    product
    .sort_values(
        "Profit",
        ascending=False
    )
    .iloc[0]
)

negative_profit_count = (
    (product["Profit"] < 0)
    .sum()
)

col1, col2 = st.columns(2)

col1.success(
    f"""
    🏆 **Most Profitable Category**

    {best_category['Category']}

    Profit: ${best_category['Profit']:,.0f}
    """
)

col2.warning(
    f"""
    ⚠️ **Least Profitable Category**

    {worst_category['Category']}

    Profit: ${worst_category['Profit']:,.0f}
    """
)

col1.info(
    f"""
    🌎 **Best Region**

    {best_region['Region']}

    Profit: ${best_region['Profit']:,.0f}
    """
)

col2.success(
    f"""
    💎 **Most Profitable Product**

    {best_product['Product Name']}

    Profit: ${best_product['Profit']:,.0f}
    """
)

st.metric(
    "🚨 Products With Negative Profit",
    negative_profit_count
)

# ============================================================
# RECOMMENDATIONS
# ============================================================

st.header("🎯 Recommended Business Actions")

recommendations = []

if negative_profit_count > 0:

    recommendations.append(
        "Review loss-making products and investigate "
        "their pricing, discounts and costs."
    )

if profit_margin < 10:

    recommendations.append(
        "Overall profit margin is relatively low. "
        "Review discounting and product pricing."
    )

if best_category["Profit Margin"] > worst_category["Profit Margin"]:

    recommendations.append(
        f"Consider increasing focus on "
        f"{best_category['Category']} because it "
        f"has stronger profitability."
    )

if not recommendations:

    recommendations.append(
        "Continue monitoring product, regional and "
        "discount-level profitability."
    )

for recommendation in recommendations:

    st.write(
        "👉 " + recommendation
    )

# ============================================================
# DATA TABLE
# ============================================================

with st.expander("📋 View Filtered Data"):

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

# ============================================================
# DOWNLOAD
# ============================================================

csv = filtered_df.to_csv(
    index=False
)

st.download_button(
    "⬇️ Download Filtered Data",
    data=csv,
    file_name="filtered_superstore.csv",
    mime="text/csv"
)

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Sales & Profit Optimization Dashboard | "
    "Python • Pandas • NumPy • Plotly • Streamlit"
)