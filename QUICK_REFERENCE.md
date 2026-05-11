# SmartRetail AI - Developer Quick Reference Guide

## 📖 Documentation Navigation

| Need | Document | Section |
|------|----------|---------|
| **System Overview** | PROJECT_OVERVIEW.md | Full architecture + business context |
| **Technical Deep Dive** | TECHNICAL_DOCUMENTATION.md | Implementation details, algorithms, formulas |
| **Module Connections** | INTERCONNECTIONS_MAP.md | Data flows, dependencies, sequences |
| **Getting Started** | This file (Quick Reference) | Common tasks & patterns |
| **Deployment** | RUN.md | Installation & execution |

---

## 🎯 Common Tasks & How-Tos

### Task 1: Add a New Query Type

**Scenario:** You want to handle a new query like "Show customer churn risk"

**Steps:**
1. **Identify Route Category**
   - Is it about inventory? → librarian
   - About operations (add/sell)? → clerk
   - About analytics? → analytics
   - About forecasting? → forecaster

2. **Update Manager Agent** (if new keyword not covered)
   ```python
   # agents/manager.py
   if "churn" in query_lower:
       state["route"] = "analytics"
       return state
   ```

3. **Implement Logic in Target Agent**
   ```python
   # agents/analytics.py
   if any(k in query for k in ["churn", "churn risk"]):
       # Your logic here
       payload = customer_summary_payload()
       # Extract churn data
       state["response"] = "..."
       return state
   ```

4. **Test Locally**
   ```bash
   # Test query
   python -c "
   from graph.workflow import graph
   result = graph.invoke({'query': 'Show customer churn risk'})
   print(result['response'])
   "
   ```

**Key Pattern:**
```
Manager classifies intent
    ↓
Routes to appropriate agent
    ↓
Agent calls relevant tools
    ↓
Tools fetch/compute data
    ↓
Agent formats response
    ↓
Frontend displays result
```

---

### Task 2: Add New ML Model (e.g., Churn Prediction)

**Scenario:** You want to add churn prediction using GradientBoosting

**Directory Structure:**
```
backend/models/
├── apriori_analysis.py
├── churn_predictor.py  ← NEW
└── __init__.py
```

**Implementation:**
```python
# backend/models/churn_predictor.py
from sklearn.ensemble import GradientBoostingClassifier
import joblib

class ChurnPredictor:
    def __init__(self):
        self.model = GradientBoostingClassifier(n_estimators=100)
        self.scaler = StandardScaler()
    
    def prepare_features(self, customer_id):
        """Engineer features from RFM + transaction history"""
        recency = compute_recency(customer_id)
        frequency = compute_frequency(customer_id)
        monetary = compute_monetary(customer_id)
        
        # Add trend features
        freq_trend = recent_freq - old_freq
        
        return np.array([recency, frequency, monetary, freq_trend])
    
    def predict_churn(self, customer_id):
        """Returns P(churn within 30 days)"""
        features = self.prepare_features(customer_id)
        features_scaled = self.scaler.transform([features])
        return self.model.predict_proba(features_scaled)[0, 1]

# Integration
def analytics_agent(state: dict) -> dict:
    query = state["query"].lower()
    
    if "churn" in query:
        from backend.models.churn_predictor import ChurnPredictor
        
        predictor = ChurnPredictor()
        predictor.model = joblib.load("churn_model.pkl")
        
        at_risk = []
        for cid in get_all_customers():
            churn_prob = predictor.predict_churn(cid)
            if churn_prob > 0.7:
                at_risk.append((cid, churn_prob))
        
        state["response"] = format_churn_report(at_risk)
    
    return state
```

**Training Pipeline:**
```python
# scripts/train_churn_model.py
from backend.models.churn_predictor import ChurnPredictor
from tools.customer_analytics import load_customers, load_transactions

# Prepare training data
known_churners = load_churned_customers()  # Customers with no purchases in 90 days
features = np.array([
    ChurnPredictor().prepare_features(cid)
    for cid in known_churners + active_customers
])
labels = np.array([1] * len(known_churners) + [0] * len(active_customers))

# Train
predictor = ChurnPredictor()
predictor.model.fit(features, labels)

# Save
joblib.dump(predictor.model, "churn_model.pkl")
```

---

### Task 3: Integrate New Data Source

**Scenario:** You have a new CSV file (promotions_schedule.csv) to integrate

**Steps:**

1. **Place file in data/ folder**
   ```
   data/promotions_schedule.csv
   ```

2. **Create loader function**
   ```python
   # tools/customer_analytics.py (or new file: tools/promotions_tools.py)
   
   def load_promotions() -> pd.DataFrame:
       """Load promotion schedule"""
       import os
       path = os.path.join(os.path.dirname(__file__), "..", "data", "promotions_schedule.csv")
       return pd.read_csv(path)
   ```

3. **Use in agent**
   ```python
   # agents/analytics.py
   
   if "promotion" in query:
       promos = load_promotions()
       upcoming = promos[promos["start_date"] > today]
       state["response"] = format_promotions(upcoming)
   ```

4. **Validate**
   ```bash
   python -c "
   from tools.customer_analytics import load_promotions
   df = load_promotions()
   print(df.head())
   "
   ```

---

### Task 4: Customize Prophet Forecast Parameters

**Scenario:** You want to adjust seasonality for better accuracy on a specific product

**Current Settings** (in product_wise_prophet_forecasting.py):
```python
model = Prophet(
    daily_seasonality=True,      # Enabled
    weekly_seasonality=True,     # Enabled
    yearly_seasonality=True,     # Enabled
    interval_width=0.95,         # 95% CI
    growth="linear"              # Trend type
)
```

**Customization Examples:**

```python
# Example 1: Reduce seasonality complexity for hourly data
model = Prophet(
    daily_seasonality=10,  # More Fourier terms (higher = more complex)
    weekly_seasonality=5,
    yearly_seasonality=3
)

# Example 2: Add custom seasonality (e.g., monthly promotions)
model = Prophet()
model.add_seasonality(name="monthly", period=30, fourier_order=3)
model.fit(df)

# Example 3: Handle logistic saturation (max capacity)
model = Prophet(
    growth="logistic",
    cap=1000  # Max units per day
)
model.fit(df)

# Example 4: Add holidays/events
model = Prophet()
holidays = pd.DataFrame({
    "holiday": ["Diwali", "Christmas"],
    "ds": pd.to_datetime(["2024-11-01", "2024-12-25"]),
    "lower_window": -5,
    "upper_window": 5
})
model.add_country_holidays(country_name="IN")
model.fit(df)
```

**How to Test Impact:**
```python
# Compare 2 models
model1 = Prophet(daily_seasonality=True)
model1.fit(df)
forecast1 = model1.predict(future)

model2 = Prophet(daily_seasonality=False)
model2.fit(df)
forecast2 = model2.predict(future)

# Evaluate on test set
mape1 = mean_absolute_percentage_error(y_test, forecast1["yhat"][-100:])
mape2 = mean_absolute_percentage_error(y_test, forecast2["yhat"][-100:])

print(f"Model 1 MAPE: {mape1:.2%}")
print(f"Model 2 MAPE: {mape2:.2%}")
```

---

### Task 5: Adjust RFM Thresholds & Segment Behavior

**Scenario:** Current at-risk definition too aggressive; want to optimize

**Current Logic** (in tools/customer_analytics.py):
```python
# RFM score computation
rec_score = 1 if rec < cluster_profiles["recency"].median() else 0
freq_score = 1 if freq > cluster_profiles["frequency"].median() else 0
mon_score = 1 if mon > cluster_profiles["monetary"].median() else 0

# Scoring
if score == 3:
    label = "Champions"
elif score == 2 and rec_score == 1:
    label = "Loyal"
elif score >= 1 and rec_score == 1:
    label = "At-Risk"
else:
    label = "Lost"
```

**Customize Thresholds:**
```python
# Option 1: Use percentiles instead of median
rec_threshold = cluster_profiles["recency"].quantile(0.25)  # More aggressive
freq_threshold = cluster_profiles["frequency"].quantile(0.75)
mon_threshold = cluster_profiles["monetary"].quantile(0.75)

# Option 2: Weighted scoring
def compute_segment_score(rec, freq, mon):
    # Weight monetary most heavily (high-value customers prioritized)
    rec_score = 1 if rec < rec_threshold else 0
    freq_score = 1 if freq > freq_threshold else 0
    mon_score = 1 if mon > mon_threshold else 0
    
    weighted_score = 0.2 * rec_score + 0.3 * freq_score + 0.5 * mon_score
    return weighted_score

# Option 3: Time-decay (prefer recent activity)
def compute_recency_weight(recency_days):
    # Exponential decay
    return np.exp(-0.01 * recency_days)

# Usage
segment = determine_segment(
    rec_score=compute_recency_weight(recency),
    freq_score=freq_score,
    mon_score=mon_score
)
```

---

## 🔧 Configuration Reference

### Environment Variables (.env)

```bash
# Required
GROQ_API_KEY=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

# Optional
DATABASE_URL=postgresql://user:pass@localhost/smartretail
LOG_LEVEL=INFO
DEBUG=False
```

### Application Settings (backend/config.py)

```python
class Settings:
    # LLM Settings
    LLM_MODEL = "llama-3.1-8b-instant"
    LLM_TEMPERATURE = 0.0  # Deterministic routing
    
    # Forecasting Settings
    FORECAST_DAYS = 30
    MIN_HISTORICAL_POINTS = 100  # Min data points for Prophet
    
    # Segmentation Settings
    CUSTOMER_SEGMENTS = 4
    RFM_MEDIAN_THRESHOLD = 0.5  # Percentile for RFM scoring
    
    # Apriori Settings
    MIN_SUPPORT = 0.01
    MIN_CONFIDENCE = 0.2
    MIN_LIFT = 1.0
    APRIORI_TOP_N = 20  # Top N rules to return
    
    # Database Settings
    DATABASE_URL = "sqlite:///./inventory.db"
    
    # Voice Settings
    SAMPLE_RATE = 16000
    AUDIO_DURATION = 10  # seconds
```

---

## 🐛 Debugging Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'sounddevice'"

**Cause:** Package not installed  
**Fix:**
```bash
pip install sounddevice soundfile groq
```

---

### Issue 2: "GroqError: api_key client option must be set"

**Cause:** .env file not loaded or GROQ_API_KEY missing  
**Fix:**
```python
# app.py (beginning of file)
from dotenv import load_dotenv
load_dotenv()  # Must be before any Groq imports
```

---

### Issue 3: "No product named 'blue pen' in inventory"

**Cause:** Database points to wrong path or empty DB  
**Fix:**
```bash
# Check where DB is created
python -c "
from tools.db import DB_PATH
print(f'Database path: {DB_PATH}')
"

# Seed data if empty
python seed.py
```

---

### Issue 4: "Forecast returns all zeros"

**Cause:** Insufficient historical data or all zeros in input  
**Fix:**
```python
# Check data quality
df = prepare_prophet_dataframe(sales_df, "product_name")
print(f"Data shape: {df.shape}")
print(f"Non-zero rows: {(df['y'] > 0).sum()}")
print(df.head(20))

# Need at least 100+ data points with variation
```

---

### Issue 5: "K-Means clustering produces identical segment sizes"

**Cause:** Data not normalized or natural K ≠ 4  
**Fix:**
```python
# Check normalization
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
rfm_norm = scaler.fit_transform(rfm_df[["recency", "frequency", "monetary"]])
print(rfm_norm.std(axis=0))  # Should be ~1.0 each

# Find optimal K via silhouette
from sklearn.metrics import silhouette_score
scores = []
for k in range(2, 10):
    km = KMeans(n_clusters=k, random_state=42)
    score = silhouette_score(rfm_norm, km.fit_predict(rfm_norm))
    scores.append((k, score))
    print(f"K={k}: Silhouette={score:.3f}")

# Use K with highest score
optimal_k = max(scores, key=lambda x: x[1])[0]
```

---

## 📊 Performance Optimization Tips

### Tip 1: Cache Heavy Computations

```python
# Use Streamlit cache
@st.cache_data(ttl=3600)  # Cache for 1 hour
def customer_summary_payload():
    """Expensive RFM computation"""
    payload = compute_rfm_clustering()
    return payload

# On subsequent calls, cached result returned instantly
```

---

### Tip 2: Optimize SQL Queries

```python
# SLOW: Full table scan
SELECT * FROM sales WHERE created_at > some_date

# FAST: Indexed column
CREATE INDEX idx_sales_date ON sales(created_at)
SELECT * FROM sales WHERE created_at > some_date

# FAST: Aggregate in DB instead of Python
SELECT customer_id, COUNT(*) as frequency, SUM(amount) as monetary
FROM sales
GROUP BY customer_id
-- vs fetching all and grouping in pandas
```

---

### Tip 3: Batch Prophet Forecasts

```python
# SLOW: Loop through each product
for product in products:
    df = prepare_prophet_dataframe(sales_df, product)
    forecast = run_prophet_for_product(df, 30)
    # ... ~1.5s per product

# FAST: Parallel processing
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(
        lambda p: (p, run_prophet_for_product(
            prepare_prophet_dataframe(sales_df, p), 30
        )),
        products
    )
```

---

## 🧪 Testing Patterns

### Unit Test Example

```python
# tests/test_inventory_tools.py
import pytest
from tools.inventory_tools import normalize_product_name

def test_normalize_plurals():
    assert normalize_product_name("pens") == "pen"
    assert normalize_product_name("boxes") == "box"
    assert normalize_product_name("berries") == "berry"
    assert normalize_product_name("pen") == "pen"  # Idempotent

def test_normalize_special_cases():
    assert normalize_product_name("data") == "data"  # Exception
    assert normalize_product_name("") == ""
```

---

### Integration Test Example

```python
# tests/test_agent_flow.py
from graph.workflow import graph

def test_librarian_stock_query():
    result = graph.invoke({
        "query": "How many blue pens in stock?"
    })
    
    assert result["route"] == "librarian"
    assert "100" in result["response"]  # Expected stock value
    assert "blue pen" in result["response"]
```

---

## 📚 Key Code Locations

| Component | File | Key Function |
|-----------|------|--------------|
| Intent Classification | agents/manager.py | routing_chain.invoke() |
| Stock Queries | agents/librarian.py | get_stock() |
| RFM Computation | tools/customer_analytics.py | customer_summary_payload() |
| Apriori Rules | backend/models/apriori_analysis.py | get_apriori_rules() |
| Prophet Forecasting | product_wise_prophet_forecasting.py | run_prophet_for_product() |
| Database | tools/db.py | get_connection() |
| Frontend | frontend/dashboard.py | Streamlit pages |
| API | backend/main.py | @app.post("/api/query") |

---

## 🚀 Deployment Checklist

- [ ] All dependencies installed (`pip install -r requirements-full.txt`)
- [ ] .env file created with GROQ_API_KEY
- [ ] Database seeded (`python seed.py`)
- [ ] RFM segmentation initialized (`python init_segmentation.py`)
- [ ] Prophet models trained (auto on first forecast)
- [ ] Apriori rules computed (auto on first analytics query)
- [ ] Tests pass (`pytest`)
- [ ] Backend starts without errors (`python run_backend.py`)
- [ ] Frontend starts without errors (`streamlit run frontend/dashboard.py`)
- [ ] Test queries work end-to-end
- [ ] Logs clean (no warnings)

---

**For detailed technical information, see TECHNICAL_DOCUMENTATION.md**
