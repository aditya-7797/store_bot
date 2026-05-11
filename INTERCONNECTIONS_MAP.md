# SmartRetail AI - System Interconnections & Data Flow Architecture

## 📡 Complete Module Dependency Graph

```
ENTRY POINTS:
├── app.py (Streamlit Chat UI)
├── frontend/dashboard.py (Streamlit Dashboard)
├── voice_cli.py (CLI with speech input)
└── run_backend.py (FastAPI HTTP server)

LAYER 1: REQUEST ROUTING
├── app.py → graph.invoke({"query": str})
├── frontend/dashboard.py → backend/main.py REST calls
├── voice_cli.py → graph.invoke() + speech_to_text()
└── run_backend.py → FastAPI handlers

LAYER 2: ORCHESTRATION ENGINE
└── graph/workflow.py (LangGraph StateGraph)
    ├── Compiles to DAG bytecode
    ├── Entry point: manager_agent
    └── Conditional routing via state["route"]

LAYER 3: INTELLIGENT AGENTS
├── agents/manager.py
│   ├── Imports: ChatGroq, ChatPromptTemplate
│   ├── Uses: LLM for intent classification
│   └── Output: state["route"] = "librarian|clerk|analytics"
│
├── agents/librarian.py
│   ├── Imports: tools/inventory_tools.py
│   ├── Operations: get_stock(), get_all_products()
│   ├── Processing: Product name normalization
│   └── Output: Stock level response
│
├── agents/clerk.py
│   ├── Imports: tools/inventory_tools.py
│   ├── Operations: update_stock(product, ±quantity)
│   ├── Validation: Prevent negative inventory
│   └── Output: Transaction confirmation
│
├── agents/analytics.py
│   ├── Imports: 
│   │   ├── tools/customer_analytics.py
│   │   ├── backend/models/apriori_analysis.py
│   │   └── tools/inventory_tools.py
│   ├── Operations:
│   │   ├── RFM Segmentation (if "segment|rfm" in query)
│   │   ├── Top Customers (if "top customer|high value" in query)
│   │   └── Product Associations (if "sell with|recommend" in query)
│   └── Output: Aggregated analytics response
│
└── agents/forecaster.py (NEW)
    ├── Imports:
    │   ├── product_wise_prophet_forecasting.py
    │   └── tools/customer_analytics.py
    ├── Operations:
    │   ├── prepare_prophet_dataframe() → Filter & aggregate historical sales
    │   ├── train_and_forecast_product() → Prophet model training
    │   ├── Extract next N days predictions
    │   └── Compute confidence intervals (95% CI)
    └── Output: Demand forecast with uncertainty bands

LAYER 4: TOOLS & UTILITIES
├── tools/db.py
│   ├── get_connection() → SQLite connection with auto-schema
│   ├── Schema initialization on first call
│   └── Connection pooling (optional, for production)
│
├── tools/inventory_tools.py
│   ├── get_all_products() → SELECT * FROM products
│   ├── get_stock(product_name) → SELECT stock WHERE name = ?
│   ├── update_stock(product_name, quantity) → UPDATE stock
│   ├── normalize_product_name(name) → Handle plurals
│   └── cleanup_duplicates() → Deduplicate via normalization
│
├── tools/customer_analytics.py
│   ├── load_customers() → Read CSV (indian_general_store_customers_1000.csv)
│   ├── load_transactions() → Read CSV (customer_transactions.csv)
│   ├── load_preferences() → Read CSV (customer_category_preferences.csv)
│   ├── compute_rfm_scores() → Recency, Frequency, Monetary
│   ├── customer_summary_payload() → Orchestrates RFM + clustering + KMeans
│   ├── append_customer_transaction() → Write transaction to CSV
│   └── build_sales_trend() → Aggregate sales over time periods
│
├── tools/voice_tools.py
│   ├── speech_to_text(audio_path) → Groq Whisper API
│   └── Returns transcribed text for NL processing
│
├── backend/models/apriori_analysis.py
│   ├── _fetch_sales_baskets() → SELECT transaction data from DB
│   ├── get_apriori_rules(min_support, min_confidence, min_lift)
│   │   ├── Pivot table: transactions × products (boolean matrix)
│   │   ├── apriori() → Frequent itemsets
│   │   ├── association_rules() → Generate rules
│   │   ├── Filter by confidence & lift
│   │   └── Serialize to JSON
│   └── Output: Serializable rules list
│
└── product_wise_prophet_forecasting.py
    ├── load_sales_data() → Read CSV (grocery_sales_dataset.csv)
    ├── prepare_prophet_dataframe(df, product_name)
    │   ├── Filter by product
    │   ├── Group by date, sum quantity
    │   ├── Forward-fill missing dates with 0
    │   └── Return [ds, y] DataFrame
    ├── train_and_forecast_product(prophet_df, days)
    │   ├── Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    │   ├── model.fit(prophet_df)
    │   ├── model.make_future_dataframe(periods=days)
    │   ├── model.predict(future)
    │   └── Return forecast with yhat, yhat_upper, yhat_lower
    └── Output: Forecast DataFrame

LAYER 5: DATA PERSISTENCE
├── inventory.db (SQLite)
│   ├── Table: products
│   │   └── Columns: id, name (UNIQUE), stock
│   ├── Table: sales
│   │   └── Columns: id, product_id, quantity, price, created_at
│   └── Schema defined in schema.sql
│
├── data/
│   ├── customer_transactions.csv
│   │   └── Columns: transaction_id, customer_id, product_id, quantity, purchase_date, price
│   ├── indian_general_store_customers_1000.csv
│   │   └── Columns: customer_id, [customer demographics]
│   ├── customer_category_preferences.csv
│   │   └── Columns: customer_id, primary_category, category_spend_percentage, last_category_purchase_days_ago
│   ├── rfm_segmentation.csv
│   │   └── Columns: customer_id, recency, frequency, monetary, segment
│   └── grocery_sales_dataset.csv
│       └── Columns: date, product_name, quantity (Prophet training data)
│
└── .env
    └── Configuration: GROQ_API_KEY, DATABASE_URL

PRESENTATION LAYER:
├── app.py (Chat UI)
│   ├── Streamlit page layout
│   ├── Audio recording (sounddevice)
│   ├── Speech recognition (voice_tools)
│   ├── Graph invocation
│   └── Chat message display
│
└── frontend/dashboard.py (Dashboard)
    ├── Page selector: Dashboard | AI Assistant | Inventory | Analytics | Forecasting | Customers
    ├── Inventory Page
    │   ├── get_all_products() → Display table
    │   └── Update stock UI
    ├── Analytics Page
    │   ├── Apriori rules visualization
    │   ├── Product association heatmap
    │   └── Bundle recommendations
    ├── Forecasting Page (NEW)
    │   ├── load_forecasting_dataset()
    │   ├── prepare_prophet_product_data(sales_df, product)
    │   ├── run_prophet_for_product(prophet_df, forecast_days)
    │   ├── Plotly visualization (historical + forecast + CI)
    │   └── CSV export
    └── Customers Page
        ├── customer_summary_payload()
        ├── RFM segment counts
        ├── Top customers by spend
        └── Cluster analysis

SERVICE LAYER:
└── backend/main.py (FastAPI)
    ├── POST /api/query → query_agent() → graph.invoke()
    ├── GET /api/inventory/products → get_all_products()
    ├── GET /api/inventory/stock/{product} → get_stock()
    ├── POST /api/inventory/update → update_stock()
    ├── GET /api/customers/segments → customer_summary_payload()
    ├── GET /api/customers/summary → get_top_customers()
    ├── GET /api/analytics/apriori → get_apriori_rules()
    ├── GET /api/forecast/{product} → run_prophet_for_product()
    └── GET /health → System health check

CONFIGURATION:
└── backend/config.py
    ├── Settings class
    ├── LLM_MODEL = "llama-3.1-8b-instant"
    ├── FORECAST_DAYS = 30
    ├── CUSTOMER_SEGMENTS = 4
    ├── MIN_SUPPORT = 0.01
    └── MIN_CONFIDENCE = 0.2
```

---

## 🔄 Data Flow Sequences

### Sequence 1: Stock Query (Librarian Path)

```
User Input: "How many blue pens?"
    ↓
[app.py]
final_state = graph.invoke({"query": "How many blue pens?"})
    ↓
[workflow.py]
StateGraph.invoke() → Entry point: manager_agent
    ↓
[agents/manager.py - Manager Node]
routing_chain = ChatPromptTemplate → ChatGroq
result = routing_chain.invoke({"query": "How many blue pens?"})
state["route"] = "librarian"
    ↓
[workflow.py - Conditional Edge]
if state["route"] == "librarian":
    node = librarian_agent
    ↓
[agents/librarian.py - Librarian Node]
query = "how many blue pens?"
product = "blue pens".replace("how many", "").strip()
product = normalize_product_name("blue pens")  → "blue pen"
    ↓
[tools/inventory_tools.py]
stock = get_stock("blue pen")
    ↓
[tools/db.py]
conn = sqlite3.connect(inventory.db)
cur.execute("SELECT stock FROM products WHERE name = ?", ("blue pen",))
result = cur.fetchone() → (100,)
    ↓
[inventory.db]
READ products table
    ↓
[tools/inventory_tools.py]
return 100
    ↓
[agents/librarian.py]
if result:
    state["response"] = f"There are 100 blue pen in stock."
    ↓
[app.py]
Display: "There are 100 blue pen in stock."
```

---

### Sequence 2: Customer Segmentation Query (Analytics Path)

```
User Input: "Show customer segments"
    ↓
[app.py]
graph.invoke({"query": "Show customer segments"})
    ↓
[agents/manager.py]
query_lower = "show customer segments"
if any(keyword in query_lower for keyword in ["customer", "segment", ...]):
    state["route"] = "analytics"
    return state
    ↓
[agents/analytics.py - Analytics Node]
query = "show customer segments"
if any(k in query for k in ["segment", "segmentation", "rfm", "cluster"]):
    wants_segment_summary = True
    ↓
[tools/customer_analytics.py]
payload = customer_summary_payload()
    ↓
    [Substep A: Load Data]
    customers_df = load_customers()  # Read CSV: 1000 customers
    transactions_df = load_transactions()  # Read CSV: 5000 transactions
    
    ↓
    [Substep B: Compute RFM]
    reference_date = transactions_df["purchase_date"].max()
    
    # Recency
    recency = (reference_date - transactions_df.groupby("customer_id")["purchase_date"].max()).days
    
    # Frequency
    frequency = transactions_df.groupby("customer_id").size()
    
    # Monetary
    monetary = transactions_df.groupby("customer_id")["amount"].sum()
    
    rfm_df = pd.DataFrame({
        "recency": recency,
        "frequency": frequency,
        "monetary": monetary
    })
    
    ↓
    [Substep C: Normalize RFM]
    scaler = StandardScaler()
    rfm_normalized = scaler.fit_transform(rfm_df[["recency", "frequency", "monetary"]])
    rfm_normalized[:, 0] = -rfm_normalized[:, 0]  # Invert recency
    
    ↓
    [Substep D: K-Means Clustering]
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(rfm_normalized)
    
    ↓
    [Substep E: Segment Labeling]
    cluster_profiles = rfm_df.groupby(cluster_labels).mean()
    if score == 3:
        segment = "Champions"
    elif score == 2 and rec_score == 1:
        segment = "Loyal"
    elif score >= 1 and rec_score == 1:
        segment = "At-Risk"
    else:
        segment = "Lost"
    
    ↓
    [Substep F: Aggregate Counts]
    segment_counts = {
        "Champions": 292,
        "Loyal": 269,
        "At-Risk": 307,
        "Lost": 132
    }
    
    ↓
[agents/analytics.py]
lines = ["Customer segmentation summary:"]
for segment, count in segment_counts.items():
    lines.append(f"- {segment}: {count} customers")
    
state["response"] = "\n".join(lines)
    ↓
[app.py]
Display: "Customer segmentation summary:\n- Champions: 292 customers\n- Loyal: 269 customers\n..."
```

---

### Sequence 3: Prophet Demand Forecasting (Forecaster Path) - NEW

```
User Query (via Chat or Dashboard): "Forecast milk demand next 30 days"
    ↓
[frontend/dashboard.py - Forecasting Page]
selected_products = ["Milk"]
forecast_days = 30
if st.button("Generate Forecast"):
    ↓
[product_wise_prophet_forecasting.py]
run_product_wise_forecasting(df, ["Milk"], 30)
    ↓
    [Step 1: Load Historical Sales Data]
    sales_df = pd.read_csv("grocery_sales_dataset.csv")
    sales_df["date"] = pd.to_datetime(sales_df["date"], dayfirst=True)
    
    ↓
    [Step 2: Filter & Aggregate by Product]
    prepare_prophet_dataframe(sales_df, "Milk")
    product_df = sales_df[sales_df["product_name"] == "Milk"].copy()
    daily_sales = product_df.groupby("date")["quantity"].sum()
    
    ↓
    [Step 3: Handle Missing Dates]
    full_dates = pd.date_range(daily_sales.index.min(), daily_sales.index.max(), freq="D")
    daily_sales = daily_sales.reindex(full_dates).fillna(0.0)
    
    ↓
    [Step 4: Prepare Prophet Format]
    prophet_df = pd.DataFrame({
        "ds": full_dates,  # Datetime
        "y": daily_sales.values  # Target (quantity)
    })
    
    ↓
    [Step 5: Train Prophet Model]
    from prophet import Prophet
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True
    )
    model.fit(prophet_df)  # MLE optimization
    
    [Model Learning:]
    - Trend: Linear or logistic growth pattern
    - Weekly: Day-of-week effects
    - Yearly: Seasonal patterns (festivals, weather)
    - Changepoints: Structural breaks in trend
    
    ↓
    [Step 6: Generate Forecast]
    future = model.make_future_dataframe(periods=30, freq="D")
    forecast = model.predict(future)  # DataFrame with [ds, yhat, yhat_upper, yhat_lower, trend, seasonal, ...]
    
    ↓
    [Step 7: Extract Next 30 Days]
    next_30 = forecast.tail(30).copy()
    next_30["product_name"] = "Milk"
    
    ↓
    [Step 8: Aggregate Metrics]
    total_expected = next_30["yhat"].sum()  → 1,200 units
    upper_bound = next_30["yhat_upper"].sum()  → 1,450 units
    lower_bound = next_30["yhat_lower"].sum()  → 950 units
    daily_avg = 1,200 / 30  → 40 units/day
    
    ↓
[frontend/dashboard.py]
    ↓
    [Visualization 1: Time-Series Plot]
    fig = go.Figure()
    fig.add_trace(historical)
    fig.add_trace(forecast_line)
    fig.add_trace(upper_bound_fill)
    fig.add_trace(lower_bound_fill)
    st.plotly_chart(fig)
    
    ↓
    [Visualization 2: Statistics]
    st.metric("Expected Demand", "1,200 units")
    st.metric("Upper CI (95%)", "1,450 units")
    st.metric("Lower CI (95%)", "950 units")
    st.metric("Daily Average", "40 units/day")
    
    ↓
    [Export: CSV]
    combined_forecast.to_csv("product_wise_prophet_forecast_next_30_days.csv")
    st.download_button("Download Forecast CSV")
    
    ↓
[User]
Display: Forecast chart + statistics + CSV download option
```

---

### Sequence 4: Apriori Market Basket Analysis

```
User Query: "What can I sell with bread loaf?"
    ↓
[agents/analytics.py]
query = "what can i sell with bread loaf?"
product = _resolve_product_from_query(query)
    → Best match: "bread loaf"
    ↓
[backend/models/apriori_analysis.py]
analysis = get_apriori_rules(min_support=0.02, min_confidence=0.2, min_lift=1.0)
    ↓
    [Step 1: Fetch Sales Data]
    query = """
        SELECT s.transaction_id, p.name AS product_name
        FROM sales s
        JOIN products p ON p.id = s.product_id
    """
    sales_df = pd.read_sql_query(query, conn)
    
    ↓
    [Step 2: Build Market Basket Matrix]
    basket = sales_df.pivot_table(
        index="transaction_id",
        columns="product_name",
        values=1,
        fill_value=0
    ).astype(bool)
    
    Result: Boolean matrix (transactions × products)
    Row example: [bread=1, butter=1, milk=0, eggs=1, ...]
    
    ↓
    [Step 3: Apply Apriori Algorithm]
    frequent_itemsets = apriori(basket, min_support=0.02, use_colnames=True)
    
    Finds all itemsets with support ≥ 2%
    Example itemsets:
    - {bread}: support=0.08
    - {butter}: support=0.05
    - {bread, butter}: support=0.04 ← Frequent pair!
    
    ↓
    [Step 4: Generate Association Rules]
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.2)
    
    For {bread, butter}:
    - confidence = support({bread, butter}) / support({bread}) = 0.04 / 0.08 = 0.5
    - lift = confidence / support({butter}) = 0.5 / 0.05 = 10
    
    ↓
    [Step 5: Filter & Rank]
    rules = rules[rules["lift"] >= 1.0]  # Only positive correlations
    rules.sort_values("lift", ascending=False)
    top_n = 3
    
    ↓
    [Step 6: Find Rules Where Bread is Antecedent]
    matches = [r for r in rules if "bread loaf" in r["antecedents"]]
    
    Example matches:
    - {bread loaf} → {butter}: conf=0.65, lift=2.3
    - {bread loaf} → {milk}: conf=0.42, lift=1.8
    - {bread loaf} → {eggs}: conf=0.38, lift=1.6
    
    ↓
    [Step 7: Format Response]
    lines = ["Top products to sell with bread loaf:"]
    for item, rule in ranked:
        lines.append(f"- {item} (confidence: {conf:.2f}, lift: {lift:.2f})")
    
    state["response"] = lines.join("\n")
    
    ↓
[agents/analytics.py]
state["response"] = "Top products to sell with bread loaf:\n- butter (conf: 0.65, lift: 2.30)\n- milk (conf: 0.42, lift: 1.80)\n- eggs (conf: 0.38, lift: 1.60)"
    ↓
[app.py]
Display recommendation to user
```

---

## 🎯 Critical Integration Points

### Integration Point 1: LangGraph → Agents

```python
# graph/workflow.py
workflow.add_node("manager", manager_agent)
workflow.add_conditional_edges(
    "manager",
    lambda state: state["route"],
    {
        "librarian": "librarian",
        "clerk": "clerk",
        "analytics": "analytics",
    }
)

# Each agent receives the SAME state dict:
def agent(state: dict) -> dict:
    # Read from state
    query = state.get("query")
    
    # Process
    response = process_query(query)
    
    # Write back to state
    state["response"] = response
    return state
```

**Key:** Agents are stateless functions; all state shared via dict passed through DAG

---

### Integration Point 2: Agents → Tools

```python
# agents/analytics.py calls tools
def analytics_agent(state: dict) -> dict:
    from tools.customer_analytics import customer_summary_payload
    
    payload = customer_summary_payload()
    # payload contains: segment_counts, top_customers, kmeans_stats
    
    # Use payload to format response
    state["response"] = format_response(payload)
    return state
```

**Key:** Tools encapsulate data fetching logic; agents focus on business logic

---

### Integration Point 3: Tools → Database & Files

```python
# tools/customer_analytics.py
def customer_summary_payload():
    customers_df = load_customers()  # Reads CSV
    transactions_df = load_transactions()  # Reads CSV
    
    # Compute RFM
    rfm = compute_rfm_scores(transactions_df)
    
    # Cluster
    kmeans_result = perform_rfm_clustering(rfm)
    
    return {
        "segment_counts": segment_df,
        "top_customers": top_cust_df,
        "kmeans_stats": cluster_stats_df
    }
```

**Key:** Tools handle all I/O; data transformation/computation isolated

---

### Integration Point 4: Frontend → Backend → Graph

```python
# app.py (Frontend)
final_state = graph.invoke({"query": user_input})
bot_reply = final_state.get("response")

# backend/main.py (Service)
@app.post("/api/query")
async def query_agent(request: QueryRequest):
    final_state = graph.invoke({"query": request.query})
    return QueryResponse(
        query=request.query,
        response=final_state.get("response"),
        route=final_state.get("route")
    )
```

**Key:** Frontend & Backend use same graph invocation; state flows through HTTP

---

### Integration Point 5: Prophet → Dashboard → Inventory

```python
# Forecasting integrates end-to-end:

1. Frontend loads historical data
   sales_df = load_forecasting_dataset()

2. Prophet trains on product data
   prophet_df = prepare_prophet_product_data(sales_df, "Milk")
   model, forecast = run_prophet_for_product(prophet_df, 30)

3. Extract demand expectation
   expected_demand = forecast["yhat"].sum()

4. Logic: Integrate with inventory alerts
   if current_stock < (expected_demand * safety_factor):
       send_alert("Low stock alert: Order soon")

5. Dynamic pricing (future)
   if expected_demand > historical_avg:
       suggested_price = base_price * 1.1  # Increase by 10%
```

**Key:** Forecast output feeds into operational decisions

---

## 📊 Data Model Relationships

```
┌──────────────┐          ┌──────────────┐
│   Products   │          │   Customers  │
├──────────────┤          ├──────────────┤
│ id (PK)      │◄─────────┤ customer_id  │
│ name         │   1:N    │ [demographics]
│ stock        │          │              │
└──────────────┘          └──────────────┘
      △                           △
      │ (product_id FK)          │ (customer_id FK)
      │                          │
      │ (sales_id FK)   (transaction_id FK)
      │                          │
      └──────────┬───────────────┘
                 │
         ┌───────▼─────────┐
         │ Sales / Trans.  │
         ├─────────────────┤
         │ id (PK)         │
         │ product_id (FK) │
         │ customer_id (FK)│
         │ quantity        │
         │ price           │
         │ created_at      │
         └─────────────────┘
```

**Apriori Mining:** Transactions × Products → Association Rules

**RFM Segmentation:** Customers + Transactions → Recency, Frequency, Monetary → Clusters

**Prophet Forecasting:** Sales × Time → Trend + Seasonality + Forecast

---

## 🔗 Configuration Cascade

```
.env (Environment)
    ↓
backend/config.py (Parsed Settings)
    ├── GROQ_API_KEY → agents/manager.py (LLM routing)
    ├── LLM_MODEL → agents/manager.py
    ├── FORECAST_DAYS → product_wise_prophet_forecasting.py
    ├── CUSTOMER_SEGMENTS → tools/customer_analytics.py (K=4)
    ├── MIN_SUPPORT → backend/models/apriori_analysis.py
    └── MIN_CONFIDENCE → backend/models/apriori_analysis.py

Each module reads from settings → Centralized config management
```

---

## 🚀 Request Lifecycle

```
REQUEST ENTERS SYSTEM:
    ↓
[Endpoint]
POST /api/query { "query": "How many blue pens?" }
    ↓
[Service Layer - backend/main.py]
@app.post("/api/query")
async def query_agent(request: QueryRequest)
    ↓
[Validation]
if not request.query:
    raise HTTPException("Query required")
    ↓
[Orchestration]
state = {"query": request.query}
final_state = graph.invoke(state)
    ↓
[Graph Execution]
Entry → Manager → Route → Specialized Agent → Tool Calls → DB/File I/O → Response
    ↓
[Response Formation]
return QueryResponse(
    query=request.query,
    response=final_state["response"],
    route=final_state["route"]
)
    ↓
[HTTP Response]
200 OK {
    "query": "How many blue pens?",
    "response": "There are 100 blue pen in stock.",
    "route": "librarian"
}
    ↓
[Frontend Rendering]
Display response to user
```

---

**This interconnection map shows how every component fits together in the SmartRetail AI system!**
