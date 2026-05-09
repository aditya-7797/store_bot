"""
SmartRetail AI - Streamlit Dashboard
Main dashboard with multiple pages
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt

from tools.customer_analytics import customer_summary_payload, load_customers, load_sales_history

# ==================== Configuration ====================

st.set_page_config(
    page_title="SmartRetail AI",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"
TARGET_FORECAST_PRODUCTS = [
    "Rice",
    "Wheat Flour",
    "Milk",
    "Sugar",
    "Salt",
    "Cooking Oil",
    "Eggs",
    "Bread",
    "Tea",
    "Coffee",
]
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _resolve_dataset_path(filename: str) -> Path:
    for candidate in (DATA_DIR / filename, ROOT_DIR / filename):
        if candidate.exists():
            return candidate
    return DATA_DIR / filename

# ==================== Custom Styling ====================

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: white !important;
    }
    .stMetric .metric-value {
        color: white !important;
    }
    h1 {
        color: #667eea;
        font-weight: 700;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== Sidebar Navigation ====================

st.sidebar.title("🏪 SmartRetail AI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🤖 AI Assistant", "📦 Inventory", "📈 Analytics", "🔮 Forecasting", "👥 Customers"]
)

st.sidebar.markdown("---")
st.sidebar.info("**Version:** 1.0.0\n\n**Status:** ✅ Active")

# ==================== Helper Functions ====================

def call_api(endpoint: str, method: str = "GET", data: dict = None):
    """Call FastAPI backend"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("🔴 Cannot connect to backend. Make sure FastAPI is running on port 8000.")
        st.code("python backend/main.py", language="bash")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def load_forecasting_dataset() -> pd.DataFrame:
    """Load live sales history for forecasting."""
    df = load_sales_history().copy()
    if df.empty:
        return pd.DataFrame(columns=["date", "product_name", "quantity"])

    df = df.rename(columns={"sale_date": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df


def load_customer_insights() -> dict:
    """Load customer datasets and derived analytics."""
    return customer_summary_payload()


def prepare_prophet_product_data(df: pd.DataFrame, product_name: str) -> pd.DataFrame:
    """Prepare Prophet-formatted daily sales dataframe for one product."""
    product_df = df[df["product_name"] == product_name].copy()
    if product_df.empty:
        return pd.DataFrame(columns=["ds", "y"])

    daily = (
        product_df.groupby("date", as_index=False)["quantity"]
        .sum()
        .rename(columns={"date": "ds", "quantity": "y"})
        .sort_values("ds")
    )
    full_dates = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = (
        daily.set_index("ds")
        .reindex(full_dates)
        .fillna(0.0)
        .rename_axis("ds")
        .reset_index()
    )
    return daily


def run_prophet_for_product(prophet_df: pd.DataFrame, forecast_days: int) -> pd.DataFrame:
    """Train Prophet model and return forecast dataframe."""
    from prophet import Prophet

    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=forecast_days, freq="D")
    forecast = model.predict(future)
    return model, forecast

# ==================== PAGE 1: Dashboard ====================

if page == "📊 Dashboard":
    st.title("📊 Business Dashboard")
    st.markdown("### Overview of your retail operations")

    customer_payload = load_customer_insights()
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Customers",
            value=f"{customer_payload.get('customer_count', 0):,}",
            delta="From customer dataset"
        )
    
    with col2:
        st.metric(
            label="Active Customers",
            value=f"{customer_payload.get('active_customers', 0):,}",
            delta="Last 30 days"
        )
    
    with col3:
        st.metric(
            label="Total Revenue",
            value=f"₹{customer_payload.get('total_spent', 0.0):,.0f}",
            delta="From RFM data"
        )
    
    with col4:
        st.metric(
            label="Avg. Order Value",
            value=f"₹{customer_payload.get('average_order_value', 0.0):,.0f}",
            delta="Customer spend"
        )
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Sales Trend (Up to Apr 23)")
        trend_data = call_api("/api/analytics/sales-trend")
        if trend_data and trend_data.get("trend"):
            trend_df = pd.DataFrame(trend_data["trend"])
            trend_df["date"] = pd.to_datetime(trend_df["date"])
            trend_df = trend_df.sort_values("date")
            # Limit the sales trend to April 23 of the current year
            cutoff = pd.Timestamp(year=datetime.now().year, month=4, day=23)
            trend_df = trend_df[trend_df["date"] <= cutoff]
            if trend_df.empty:
                st.info("No sales data up to Apr 23 is available.")
            else:
                trend_fig = px.line(
                    trend_df,
                    x="date",
                    y="total_revenue",
                    markers=True,
                    labels={"date": "Date", "total_revenue": "Revenue (₹)"},
                )
                trend_fig.update_layout(height=350)
                st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Sales trend data is not available yet.")
    
    with col_right:
        st.subheader("🏆 Top Products")
        top_products_data = call_api("/api/analytics/top-selling-products?limit=5")
        if top_products_data and top_products_data.get("products"):
            top_products_df = pd.DataFrame(top_products_data["products"])
            top_products_fig = px.bar(
                top_products_df,
                x="product_name",
                y="total_units",
                color="total_units",
                hover_data={"total_revenue": True},
                labels={"product_name": "Product", "total_units": "Units Sold"},
            )
            top_products_fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(top_products_fig, use_container_width=True)
        else:
            st.info("Sales-based top products data is not available yet.")
    
    # Recent Activity
    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    sales_df = load_forecasting_dataset()
    if not sales_df.empty:
        display_cols = [col for col in ["date", "product_name", "quantity", "transaction_id", "price"] if col in sales_df.columns]
        st.dataframe(sales_df.sort_values("date", ascending=False).head(10)[display_cols], use_container_width=True, height=320)
    else:
        st.info("No live transactions yet.")

# ==================== PAGE 2: AI Assistant ====================

elif page == "🤖 AI Assistant":
    st.title("🤖 AI Assistant")
    st.markdown("### Ask questions in natural language")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about inventory, sales, or analytics..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = call_api("/api/query", method="POST", data={"query": prompt})
                
                if result:
                    response = result.get("response", "No response")
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("Failed to get response from AI agent")
    
    # Example queries
    st.markdown("---")
    st.markdown("### 💡 Example Queries")
    col1, col2 = st.columns(2)
    with col1:
        st.code("How many blue pens in stock?", language="text")
        st.code("Add 10 oil bottles", language="text")
        st.code("List all products", language="text")
    with col2:
        st.code("Sell 5 biscuit boxes", language="text")
        st.code("What's the current stock?", language="text")
        st.code("Update inventory", language="text")

# ==================== PAGE 3: Inventory ====================

elif page == "📦 Inventory":
    st.title("📦 Inventory Management")
    st.markdown("### Current stock levels")
    
    # Get inventory data
    products_data = call_api("/api/inventory/products")
    
    if products_data:
        df = pd.DataFrame(products_data)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", len(df))
        with col2:
            st.metric("Total Stock Units", df['stock'].sum())
        with col3:
            low_stock = len(df[df['stock'] < 20])
            st.metric("Low Stock Items", low_stock, delta=f"⚠️" if low_stock > 0 else "✅")
        
        st.markdown("---")
        
        # Inventory table
        st.subheader("📋 Product List")
        
        # Add search
        search = st.text_input("🔍 Search products", "")
        if search:
            df = df[df['name'].str.contains(search, case=False)]
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Stock visualization
        st.markdown("---")
        st.subheader("📊 Stock Levels Visualization")
        fig = px.bar(
            df.sort_values('stock', ascending=True).tail(15),
            x='stock',
            y='name',
            orientation='h',
            color='stock',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Cannot load inventory data. Make sure backend is running.")

    # ---- Stock Management Forms ----
    st.markdown("---")
    st.subheader("🛠️ Manage Stock")

    tab1, tab2, tab3 = st.tabs(["➕ Add New Product", "📈 Restock Existing", "📉 Sell / Remove"])

    # --- Tab 1: Add New Product ---
    with tab1:
        st.markdown("Add a brand new product to the inventory.")
        with st.form("add_new_product_form"):
            new_name = st.text_input("Product Name", placeholder="e.g. red marker")
            new_qty = st.number_input("Initial Stock Quantity", min_value=1, value=10, step=1)
            submitted = st.form_submit_button("Add Product")

        if submitted:
            if not new_name.strip():
                st.error("Please enter a product name.")
            else:
                result = call_api("/api/inventory/update", method="POST", data={
                    "product_name": new_name.strip().lower(),
                    "quantity": int(new_qty)
                })
                if result:
                    st.success(f"✅ '{new_name.strip()}' added with {new_qty} units.")
                    st.rerun()

    # --- Tab 2: Restock Existing ---
    with tab2:
        st.markdown("Add more stock to an existing product.")
        products_data2 = call_api("/api/inventory/products")
        if products_data2:
            product_names = [p["name"] for p in products_data2]
            with st.form("restock_form"):
                selected = st.selectbox("Select Product", product_names)
                restock_qty = st.number_input("Quantity to Add", min_value=1, value=10, step=1)
                restock_btn = st.form_submit_button("Add Stock")

            if restock_btn:
                result = call_api("/api/inventory/update", method="POST", data={
                    "product_name": selected,
                    "quantity": int(restock_qty)
                })
                if result:
                    st.success(f"✅ Added {restock_qty} units to '{selected}'. New stock: {result.get('new_stock')}")
                    st.rerun()
        else:
            st.warning("Cannot load products. Make sure backend is running.")

    # --- Tab 3: Record Sale ---
    with tab3:
        st.markdown("Record a live sale so the charts and customer stats update immediately.")
        customers_data = load_customers()
        products_data3 = call_api("/api/inventory/products")

        if products_data3:
            product_names3 = [p["name"] for p in products_data3]

            with st.form("sell_form"):
                # Customer selection: existing or new
                col_cust_type, col_cust_input = st.columns(2)
                with col_cust_type:
                    cust_type = st.radio("Customer Type", ["Existing", "New"], horizontal=True)
                
                with col_cust_input:
                    if cust_type == "Existing" and not customers_data.empty:
                        customer_options = customers_data[[col for col in ["customer_id", "first_name", "last_name"] if col in customers_data.columns]].copy()
                        customer_options["display"] = customer_options.apply(
                            lambda row: f"{int(row['customer_id'])} - {row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                            axis=1,
                        )
                        selected_customer_display = st.selectbox("Select Customer", customer_options["display"].tolist())
                        selected_customer_row = customer_options[customer_options["display"] == selected_customer_display].iloc[0]
                        selected_customer_id = int(selected_customer_row["customer_id"])
                    else:
                        selected_customer_id = st.number_input("Customer ID", min_value=1, value=1001, step=1)
                sell_selected = st.selectbox("Select Product", product_names3)
                sell_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
                sale_date = st.date_input("Purchase Date")
                submitted_sale = st.form_submit_button("Record Transaction")

            if submitted_sale:
                result = call_api("/api/transactions/record", method="POST", data={
                    "customer_id": selected_customer_id,
                    "product_name": sell_selected,
                    "quantity": int(sell_qty),
                    "purchase_date": f"{sale_date} 12:00:00",
                })
                if result:
                    st.success(f"✅ Transaction {result.get('transaction_id')} recorded for customer {selected_customer_id}.")
                    st.rerun()
        else:
            st.warning("Cannot load customers or products. Make sure backend is running.")

# ==================== PAGE 4: Analytics ====================

elif page == "📈 Analytics":
    st.title("📈 Business Analytics")
    st.markdown("### Market Basket Analysis (Apriori)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        min_support = st.slider("Min Support", min_value=0.005, max_value=0.2, value=0.02, step=0.005)
    with col2:
        min_confidence = st.slider("Min Confidence", min_value=0.05, max_value=0.9, value=0.25, step=0.05)
    with col3:
        min_lift = st.slider("Min Lift", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
    with col4:
        top_n = st.slider("Top Rules", min_value=5, max_value=50, value=20, step=5)

    endpoint = (
        f"/api/analytics/apriori-rules?min_support={min_support}"
        f"&min_confidence={min_confidence}&min_lift={min_lift}&top_n={top_n}"
    )
    analysis = call_api(endpoint)

    if not analysis:
        st.warning("Unable to fetch Apriori analysis. Ensure backend is running and data is seeded.")
    else:
        summary = analysis.get("summary", {})
        rules = analysis.get("rules", [])

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Transactions", summary.get("transactions", 0))
        s2.metric("Distinct Products", summary.get("distinct_products", 0))
        s3.metric("Frequent Itemsets", summary.get("frequent_itemsets", 0))
        s4.metric("Rules", summary.get("rules", 0))

        if not rules:
            st.info("No rules found for these thresholds. Try lowering support/confidence.")
        else:
            rules_df = pd.DataFrame(rules)
            rules_df["antecedent"] = rules_df["antecedents"].apply(lambda x: ", ".join(x))
            rules_df["consequent"] = rules_df["consequents"].apply(lambda x: ", ".join(x))
            rules_df["rule"] = rules_df["antecedent"] + " → " + rules_df["consequent"]

            st.markdown("---")
            st.subheader("📋 Top Association Rules")
            st.dataframe(
                rules_df[["rule", "support", "confidence", "lift", "leverage", "conviction"]],
                use_container_width=True,
                height=360,
            )

            st.markdown("---")
            st.subheader("🎯 Confidence vs Lift")
            bubble_fig = px.scatter(
                rules_df,
                x="confidence",
                y="lift",
                size="support",
                hover_name="rule",
                color="lift",
                color_continuous_scale="Viridis",
            )
            bubble_fig.update_layout(height=420)
            st.plotly_chart(bubble_fig, use_container_width=True)

            st.markdown("---")
            st.subheader("💡 Suggested Bundle Actions")
            top3 = rules_df.sort_values(["lift", "confidence"], ascending=False).head(3)
            for _, row in top3.iterrows():
                st.write(
                    f"- If customer buys **{row['antecedent']}**, recommend **{row['consequent']}** "
                    f"(confidence: {row['confidence']:.2f}, lift: {row['lift']:.2f})"
                )

# ==================== PAGE 5: Forecasting ====================

elif page == "🔮 Forecasting":
    st.title("🔮 Sales Forecasting")
    st.markdown("### Product-wise Prophet Forecasting")
    st.caption("Install dependency if needed: `pip install prophet`")

    try:
        from prophet import Prophet  # noqa: F401
    except ImportError:
        st.error("Prophet is not installed. Run: pip install prophet")
        st.stop()

    sales_df = load_forecasting_dataset()

    col_a, col_b = st.columns([2, 1])
    with col_a:
        selected_products = st.multiselect(
            "Products to forecast",
            TARGET_FORECAST_PRODUCTS,
            default=TARGET_FORECAST_PRODUCTS,
        )
    with col_b:
        forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30, step=1)

    if st.button("Generate Product-wise Forecast", type="primary"):
        if not selected_products:
            st.warning("Please select at least one product.")
            st.stop()

        all_rows = []
        summary_rows = []

        for product in selected_products:
            st.markdown("---")
            st.subheader(f"📦 {product}")

            prophet_df = prepare_prophet_product_data(sales_df, product)
            if prophet_df.empty:
                st.warning(f"No historical data available for {product}.")
                summary_rows.append(
                    {
                        "product_name": product,
                        "total_expected_sales_next_month": 0.0,
                        "status": "No historical data",
                    }
                )
                continue

            with st.spinner(f"Training Prophet model for {product}..."):
                model, forecast = run_prophet_for_product(prophet_df, forecast_days)

            next_period = forecast.tail(forecast_days).copy()
            next_period["product_name"] = product
            next_period = next_period[
                ["product_name", "ds", "yhat", "yhat_lower", "yhat_upper"]
            ].reset_index(drop=True)
            all_rows.append(next_period)

            total_sales = float(next_period["yhat"].sum())
            summary_rows.append(
                {
                    "product_name": product,
                    "total_expected_sales_next_month": total_sales,
                    "status": "Forecast generated",
                }
            )

            st.metric("Total expected sales (selected period)", f"{total_sales:.2f}")
            st.dataframe(next_period[["ds", "yhat", "yhat_lower", "yhat_upper"]], use_container_width=True)

            line_fig = px.line(
                next_period,
                x="ds",
                y="yhat",
                title=f"{product} - Forecast for Next {forecast_days} Days",
            )
            line_fig.add_scatter(
                x=next_period["ds"],
                y=next_period["yhat_lower"],
                mode="lines",
                name="Lower Bound",
                line=dict(dash="dash"),
            )
            line_fig.add_scatter(
                x=next_period["ds"],
                y=next_period["yhat_upper"],
                mode="lines",
                name="Upper Bound",
                line=dict(dash="dash"),
            )
            st.plotly_chart(line_fig, use_container_width=True)

            st.markdown("**Trend and Seasonality**")
            comp_fig = model.plot_components(forecast)
            st.pyplot(comp_fig)
            plt.close(comp_fig)

        st.markdown("---")
        st.subheader("📊 Total Expected Sales (Next Month)")
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True)

        if all_rows:
            combined_forecast = pd.concat(all_rows, ignore_index=True)
            csv_data = combined_forecast.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Forecast CSV",
                data=csv_data,
                file_name="product_wise_prophet_forecast_next_30_days.csv",
                mime="text/csv",
            )

# ==================== PAGE 6: Customers ====================

elif page == "👥 Customers":
    st.title("👥 Customer Intelligence")
    st.markdown("### Customer segmentation and analysis")

    customer_payload = load_customer_insights()
    customers_df = customer_payload.get("customers", pd.DataFrame())
    rfm_df = customer_payload.get("rfm", pd.DataFrame())
    preferences_df = customer_payload.get("preferences", pd.DataFrame())
    segment_counts = customer_payload.get("segment_counts", pd.DataFrame())
    kmeans_stats = customer_payload.get("kmeans_stats", pd.DataFrame())
    kmeans_assignments = customer_payload.get("kmeans_assignments", pd.DataFrame())
    top_customers = customer_payload.get("top_customers", pd.DataFrame())
    category_counts = customer_payload.get("category_counts", pd.DataFrame())

    if customers_df.empty and rfm_df.empty:
        st.info("Place customers.csv, transactions.csv, rfm_segments.csv, and preferences.csv inside data/ to unlock this page.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Customers", f"{customer_payload.get('customer_count', 0):,}")
        col2.metric("Active Customers", f"{customer_payload.get('active_customers', 0):,}")
        col3.metric("Total Spend", f"₹{customer_payload.get('total_spent', 0.0):,.0f}")
        col4.metric("Avg Order Value", f"₹{customer_payload.get('average_order_value', 0.0):,.0f}")

        st.markdown("---")
        left_col, right_col = st.columns(2)

        with left_col:
            st.subheader("RFM Segments")
            if not segment_counts.empty:
                segment_fig = px.pie(segment_counts, values="count", names="segment", title="Customer Segment Distribution")
                st.plotly_chart(segment_fig, use_container_width=True)
            else:
                st.info("No segment data available yet.")

        with right_col:
            st.subheader("Category Preferences")
            if not category_counts.empty:
                category_fig = px.bar(category_counts, x="category", y="count", color="count", title="Primary Category Preferences")
                st.plotly_chart(category_fig, use_container_width=True)
            elif not preferences_df.empty and "primary_category" in preferences_df.columns:
                category_counts = preferences_df["primary_category"].value_counts().reset_index()
                category_counts.columns = ["category", "count"]
                category_fig = px.bar(category_counts, x="category", y="count", color="count", title="Primary Category Preferences")
                st.plotly_chart(category_fig, use_container_width=True)
            else:
                st.info("No category preference data available yet.")

        st.markdown("---")
        st.subheader("RFM Scatter")
        if not rfm_df.empty:
            rfm_fig = px.scatter(
                rfm_df,
                x="last_purchase_days_ago",
                y="total_spent_rupees",
                size="total_purchases",
                color="segment",
                hover_name="customer_id",
                labels={"last_purchase_days_ago": "Recency (days)", "total_spent_rupees": "Monetary (₹)"},
            )
            st.plotly_chart(rfm_fig, use_container_width=True)
        else:
            st.info("RFM data is not available yet.")

        st.markdown("---")
        st.subheader("KMeans Clustering")
        if not kmeans_assignments.empty:
            kmeans_fig = px.scatter(
                kmeans_assignments,
                x="last_purchase_days_ago",
                y="total_spent_rupees",
                color="cluster_label",
                size="total_purchases",
                hover_name="customer_id",
                title="Customer KMeans Clusters",
                labels={"last_purchase_days_ago": "Recency (days)", "total_spent_rupees": "Monetary (₹)", "cluster_label": "Cluster"},
                color_discrete_sequence=px.colors.qualitative.Set2,
                hover_data={
                    "segment": True,
                    "total_purchases": True,
                    "average_order_value": True,
                    "cluster": True,
                },
            )
            kmeans_fig.update_traces(marker=dict(opacity=0.78, line=dict(width=0.5, color="white")))
            kmeans_fig.update_layout(
                height=520,
                legend_title_text="KMeans Cluster",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                margin=dict(l=10, r=10, t=70, b=10),
                template="plotly_white",
            )
            st.plotly_chart(kmeans_fig, use_container_width=True)
        else:
            st.info("KMeans plot will appear once the RFM data is available.")

        if not kmeans_stats.empty:
            st.markdown("##### Cluster Summary")
            st.dataframe(kmeans_stats, use_container_width=True, height=240)
        else:
            st.info("KMeans summary will appear after the RFM dataset is loaded.")

        st.markdown("---")
        st.subheader("Top Customers")
        if not top_customers.empty:
            top_view = top_customers[[col for col in ["customer_id", "segment", "total_purchases", "total_spent_rupees", "last_purchase_days_ago", "average_order_value"] if col in top_customers.columns]]
            st.dataframe(top_view, use_container_width=True, height=280)
        else:
            st.info("Top customer ranking will show up once the RFM file is available.")

# ==================== Footer ====================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; padding: 2rem;'>"
    "SmartRetail AI v1.0 | Built with Streamlit + FastAPI + LangGraph"
    "</div>",
    unsafe_allow_html=True
)
