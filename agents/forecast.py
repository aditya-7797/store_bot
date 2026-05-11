"""
Forecast Agent — answers sales prediction queries using Prophet.
Example queries:
  - "What will be the sales of Milk next month?"
  - "Predict demand for Rice in the next 30 days"
  - "How much Sugar will sell next month?"
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Products available for forecasting (must match grocery_sales_dataset.csv)
# ---------------------------------------------------------------------------
FORECAST_PRODUCTS = [
    "Rice", "Wheat Flour", "Milk", "Sugar", "Salt",
    "Cooking Oil", "Eggs", "Bread", "Tea", "Coffee",
]

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "grocery_sales_dataset.csv"


def _resolve_product(query: str) -> str | None:
    """Return the best matching forecast product name from the query."""
    q = query.lower()

    # 1) Exact (case-insensitive) match
    for p in FORECAST_PRODUCTS:
        if p.lower() in q:
            return p

    # 2) Token overlap — helps "wheat" match "Wheat Flour"
    best, best_score = None, 0
    for p in FORECAST_PRODUCTS:
        tokens = [t for t in p.lower().split() if len(t) >= 3]
        score = sum(1 for t in tokens if t in q)
        if score > best_score:
            best_score, best = score, p

    return best if best_score > 0 else None


def _load_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["date"])


def _run_prophet(df: pd.DataFrame, product: str, days: int = 30) -> int | None:
    """Train Prophet on one product and return total predicted units for next `days` days."""
    try:
        from prophet import Prophet  # imported here to avoid slow startup
    except ImportError:
        return None

    product_df = df[df["product_name"] == product].copy()
    if product_df.empty:
        return None

    daily = (
        product_df.groupby("date", as_index=False)["quantity"]
        .sum()
        .rename(columns={"date": "ds", "quantity": "y"})
        .sort_values("ds")
    )

    # Fill missing dates with 0
    full_dates = pd.date_range(daily["ds"].min(), daily["ds"].max(), freq="D")
    daily = (
        daily.set_index("ds")
        .reindex(full_dates)
        .fillna(0.0)
        .rename_axis("ds")
        .reset_index()
    )

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=True,
    )
    model.fit(daily)

    future = model.make_future_dataframe(periods=days, freq="D")
    forecast = model.predict(future)

    total = int(forecast.tail(days)["yhat"].clip(lower=0).round().sum())
    return total


def forecast_agent(state: dict) -> dict:
    query = state.get("query", "")

    product = _resolve_product(query)
    if not product:
        state["response"] = (
            "I couldn't identify which product you want a forecast for. "
            "Try asking like: \"What will be the sales of Milk next month?\""
        )
        return state

    df = _load_csv()
    if df.empty:
        state["response"] = "Sales data not found. Please ensure grocery_sales_dataset.csv exists."
        return state

    predicted = _run_prophet(df, product, days=30)

    if predicted is None:
        state["response"] = (
            f"No historical sales data found for '{product}'. "
            "Cannot generate a forecast."
        )
        return state

    state["response"] = (
        f"📈 **Sales Forecast for {product} (Next 30 Days)**\n\n"
        f"Predicted total sales: **{predicted} units**\n\n"
        # f"_This forecast is generated using the Prophet time-series model "
        # f"based on historical sales data._"
    )
    return state
