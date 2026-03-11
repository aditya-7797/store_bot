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

# ==================== Configuration ====================

st.set_page_config(
    page_title="SmartRetail AI",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"

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

# ==================== PAGE 1: Dashboard ====================

if page == "📊 Dashboard":
    st.title("📊 Business Dashboard")
    st.markdown("### Overview of your retail operations")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value="₹2,45,000",
            delta="+12% from last month"
        )
    
    with col2:
        st.metric(
            label="Total Products",
            value="150",
            delta="+5 new products"
        )
    
    with col3:
        st.metric(
            label="Profit Margin",
            value="23.5%",
            delta="+2.1%"
        )
    
    with col4:
        st.metric(
            label="Active Customers",
            value="567",
            delta="+15%"
        )
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Sales Trend (Last 30 Days)")
        # Sample data - replace with real data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        sales = pd.DataFrame({
            'Date': dates,
            'Sales': [8000 + i*100 + (i%7)*500 for i in range(30)]
        })
        fig = px.line(sales, x='Date', y='Sales', markers=True)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.subheader("🏆 Top Products")
        # Get products from API
        products_data = call_api("/api/inventory/products")
        if products_data:
            df = pd.DataFrame(products_data)
            df = df.sort_values('stock', ascending=False).head(5)
            fig = px.bar(df, x='name', y='stock', color='stock')
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Start the FastAPI backend to see real data")
    
    # Recent Activity
    st.markdown("---")
    st.subheader("📋 Recent Transactions")
    st.info("💡 Transaction tracking will be added in Phase 2")

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
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("Cannot load inventory data. Make sure backend is running.")

# ==================== PAGE 4: Analytics ====================

elif page == "📈 Analytics":
    st.title("📈 Business Analytics")
    st.markdown("### Sales and profit analysis")
    
    st.info("🚧 **Coming in Phase 2**\n\nThis section will include:\n- Sales trends\n- Profit analysis\n- Product performance\n- Revenue breakdown")
    
    # Placeholder charts
    st.subheader("📊 Monthly Revenue")
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    revenue = [45000, 52000, 48000, 61000, 58000, 67000]
    fig = px.bar(x=months, y=revenue, labels={'x': 'Month', 'y': 'Revenue (₹)'})
    st.plotly_chart(fig, use_container_width=True)

# ==================== PAGE 5: Forecasting ====================

elif page == "🔮 Forecasting":
    st.title("🔮 Sales Forecasting")
    st.markdown("### AI-powered demand prediction")
    
    st.info("🚧 **Coming in Phase 3**\n\nThis section will include:\n- Product demand forecasting (ARIMA/Prophet)\n- Seasonal trend analysis\n- Stock recommendations\n- Confidence intervals")
    
    # Placeholder
    st.subheader("Select Product to Forecast")
    product = st.selectbox("Product", ["Blue Pen", "Oil Bottle", "Biscuit Box"])
    days = st.slider("Forecast Days", 7, 90, 30)
    
    if st.button("Generate Forecast"):
        st.warning("Forecasting model not yet implemented. Coming in Phase 3!")

# ==================== PAGE 6: Customers ====================

elif page == "👥 Customers":
    st.title("👥 Customer Intelligence")
    st.markdown("### Customer segmentation and analysis")
    
    st.info("🚧 **Coming in Phase 3**\n\nThis section will include:\n- Customer segmentation (K-Means)\n- RFM analysis\n- Buying patterns\n- Target group identification")
    
    # Placeholder
    st.subheader("Customer Segments")
    segments = pd.DataFrame({
        'Segment': ['High Value', 'Regular', 'Budget', 'Occasional'],
        'Count': [45, 120, 180, 222],
        'Avg. Spend': [5000, 2000, 800, 300]
    })
    
    fig = px.pie(segments, values='Count', names='Segment', title='Customer Distribution')
    st.plotly_chart(fig, use_container_width=True)

# ==================== Footer ====================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; padding: 2rem;'>"
    "SmartRetail AI v1.0 | Built with Streamlit + FastAPI + LangGraph"
    "</div>",
    unsafe_allow_html=True
)
