"""
Shared customer analytics helpers for SmartRetail AI.

This module loads the customer datasets from data/ and provides
RFM aggregation plus KMeans clustering utilities that can be reused
by both the FastAPI backend and the Streamlit dashboard.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from tools.db import get_connection

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
CUSTOMER_TRANSACTIONS_FILE = DATA_DIR / "customer_transactions.csv"


def _candidate_paths(filename: str) -> list[Path]:
    return [DATA_DIR / filename, ROOT_DIR / filename]


def _first_existing_path(paths: Iterable[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def load_csv_dataset(*filenames: str) -> pd.DataFrame:
    """Load a CSV from data/ with a repository root fallback."""
    for filename in filenames:
        path = _first_existing_path(_candidate_paths(filename))
        if path is not None:
            return pd.read_csv(path)
    return pd.DataFrame()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    normalized = df.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    return normalized


def load_customers() -> pd.DataFrame:
    return _normalize_columns(load_csv_dataset("indian_general_store_customers_1000.csv", "customers.csv"))


def load_transactions() -> pd.DataFrame:
    return _normalize_columns(load_csv_dataset("customer_transactions.csv", "transactions.csv"))


def load_rfm_segments() -> pd.DataFrame:
    return _normalize_columns(load_csv_dataset("rfm_segmentation.csv", "rfm_segments.csv"))


def load_preferences() -> pd.DataFrame:
    return _normalize_columns(load_csv_dataset("customer_category_preferences.csv", "preferences.csv"))


def build_product_price_map() -> dict[int, float]:
    """Estimate unit prices for each product from sales table with fallback pricing."""
    FALLBACK_PRICES = {
        "bread": 30, "milk": 45, "eggs": 60, "butter": 120, "cheese": 180,
        "yogurt": 40, "rice": 50, "wheat flour": 35, "sugar": 40, "salt": 15,
        "oil": 110, "spices": 80, "tea": 180, "coffee": 200, "biscuits": 25,
        "chocolate": 30, "chips": 20, "juice": 35, "water": 20, "soda": 30,
        "snacks": 40, "nuts": 200, "fruits": 60, "vegetables": 50,
        "paneer": 250, "meat": 300, "fish": 250, "dal": 80, "flour": 35,
    }
    
    query = """
        SELECT product_id, AVG(price) AS avg_price
        FROM sales
        WHERE product_id IS NOT NULL AND price IS NOT NULL AND price > 0
        GROUP BY product_id
    """
    conn = get_connection()
    try:
        price_df = pd.read_sql_query(query, conn)
        products_df = pd.read_sql_query("SELECT id, name FROM products", conn)
    finally:
        conn.close()

    price_map = {}
    if not price_df.empty:
        price_df["product_id"] = pd.to_numeric(price_df["product_id"], errors="coerce")
        price_df["avg_price"] = pd.to_numeric(price_df["avg_price"], errors="coerce")
        price_df = price_df.dropna(subset=["product_id", "avg_price"])
        price_map = {
            int(row.product_id): float(row.avg_price)
            for row in price_df.itertuples(index=False)
        }
    
    # Fallback: assign prices based on product names
    if not products_df.empty:
        for _, row in products_df.iterrows():
            product_id = int(row["id"])
            if product_id not in price_map:
                product_name = str(row["name"]).lower().strip()
                fallback_price = 50.0
                for key, val in FALLBACK_PRICES.items():
                    if key in product_name or product_name in key:
                        fallback_price = float(val)
                        break
                price_map[product_id] = fallback_price
    
    return price_map


def append_customer_transaction(transaction_row: dict) -> None:
    """Append a transaction row to the live customer_transactions.csv dataset."""
    CUSTOMER_TRANSACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Normalize incoming row to match historical CSV format:
    # transaction_id: sequential integer (ignore TX- prefixes)
    # purchase_date: YYYY-MM-DD (date only)
    # price: empty (historical dataset left this blank)

    # Load existing file if present to compute next transaction id
    if CUSTOMER_TRANSACTIONS_FILE.exists():
        existing = pd.read_csv(CUSTOMER_TRANSACTIONS_FILE)
    else:
        existing = pd.DataFrame(columns=["transaction_id", "customer_id", "product_id", "quantity", "purchase_date", "price"])

    # Determine next numeric transaction id
    if "transaction_id" in existing.columns and not existing.empty:
        numeric_tx = pd.to_numeric(existing["transaction_id"], errors="coerce")
        max_tx = int(numeric_tx.max()) if not numeric_tx.isna().all() else 1000
        next_tx = max_tx + 1
    else:
        next_tx = 1001

    row = transaction_row.copy()
    # override transaction_id with sequential integer
    row["transaction_id"] = int(next_tx)

    # Normalize purchase_date to date-only string
    try:
        row_dt = pd.to_datetime(row.get("purchase_date"))
        row["purchase_date"] = row_dt.strftime("%Y-%m-%d")
    except Exception:
        # leave as-is if parsing fails
        pass

    # Ensure price is blank to match historical rows
    row["price"] = ""

    new_row = pd.DataFrame([row])
    combined = pd.concat([existing, new_row], ignore_index=True, sort=False)
    combined.to_csv(CUSTOMER_TRANSACTIONS_FILE, index=False)


def load_sales_history() -> pd.DataFrame:
    """Load real sales rows from the SQLite database joined to product names."""
    query = """
        SELECT
            date(s.created_at) AS sale_date,
            p.name AS product_name,
            s.quantity,
            s.price,
            s.transaction_id
        FROM sales s
        JOIN products p ON p.id = s.product_id
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    if df.empty:
        return df
    df = _normalize_columns(df)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["revenue"] = (df["quantity"] * df["price"]).round(2)
    return df.dropna(subset=["sale_date"])


def build_sales_trend() -> pd.DataFrame:
    """Aggregate real sales into a daily trend dataframe."""
    sales = load_sales_history()
    if sales.empty:
        return pd.DataFrame(columns=["date", "total_revenue", "total_units"])

    trend = (
        sales.groupby(sales["sale_date"].dt.date)
        .agg(total_revenue=("revenue", "sum"), total_units=("quantity", "sum"))
        .reset_index()
        .rename(columns={"sale_date": "date"})
    )
    trend["date"] = pd.to_datetime(trend["date"])
    trend["total_revenue"] = trend["total_revenue"].round(2)
    trend["total_units"] = trend["total_units"].round(0).astype(int)
    return trend.sort_values("date").reset_index(drop=True)


def build_top_selling_products(top_n: int = 5) -> pd.DataFrame:
    """Aggregate product sales from the SQLite database."""
    sales = load_sales_history()
    if sales.empty:
        return pd.DataFrame(columns=["product_name", "total_units", "total_revenue"])

    top_products = (
        sales.groupby("product_name")
        .agg(total_units=("quantity", "sum"), total_revenue=("revenue", "sum"))
        .reset_index()
        .sort_values(["total_units", "total_revenue"], ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    top_products["total_units"] = top_products["total_units"].round(0).astype(int)
    top_products["total_revenue"] = top_products["total_revenue"].round(2)
    return top_products


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def compute_rfm_from_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """Compute basic RFM metrics from transaction-level data."""
    transactions = _normalize_columns(transactions)
    if transactions.empty:
        return pd.DataFrame(columns=[
            "customer_id",
            "recency_days",
            "frequency",
            "monetary_value",
            "total_purchases",
            "total_spent_rupees",
            "last_purchase_days_ago",
            "average_order_value",
            "segment",
        ])

    customer_col = _pick_column(transactions, ["customer_id", "customerid", "client_id"])
    date_col = _pick_column(transactions, ["purchase_date", "date", "created_at", "transaction_date"])
    monetary_col = _pick_column(transactions, ["total_spent_rupees", "monetary_value", "amount", "revenue", "price"])
    quantity_col = _pick_column(transactions, ["quantity", "qty", "units"])

    if customer_col is None:
        return pd.DataFrame()

    working = transactions.copy()
    working[customer_col] = pd.to_numeric(working[customer_col], errors="coerce")
    working = working.dropna(subset=[customer_col])

    if date_col is not None:
        working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
        working = working.dropna(subset=[date_col])
        reference_date = working[date_col].max()
        if pd.isna(reference_date):
            reference_date = pd.Timestamp.today().normalize()
    else:
        reference_date = pd.Timestamp.today().normalize()

    # Determine if we should use the monetary column or fall back to quantity-based estimation
    use_monetary = False
    if monetary_col is not None:
        working[monetary_col] = pd.to_numeric(working[monetary_col], errors="coerce")
        non_zero_frac = (working[monetary_col].fillna(0.0) > 0).sum() / max(1, len(working))
        if non_zero_frac >= 0.1:
            # monetary column has enough non-zero values; use it
            use_monetary = True
            working[monetary_col] = working[monetary_col].fillna(0.0)

    # If monetary is not available or mostly empty, use quantity-based estimation
    if not use_monetary:
        if quantity_col is not None:
            working[quantity_col] = pd.to_numeric(working[quantity_col], errors="coerce").fillna(0.0)
            price_lookup = build_product_price_map()
            # Determine a sensible fallback price: median of known prices or 50
            if price_lookup:
                try:
                    median_price = float(pd.Series(list(price_lookup.values())).median())
                except Exception:
                    median_price = 50.0
            else:
                median_price = 50.0

            if "product_id" in working.columns:
                working["_estimated_price"] = pd.to_numeric(working["product_id"], errors="coerce").map(price_lookup).fillna(median_price)
            else:
                working["_estimated_price"] = median_price
            working["_estimated_value"] = working[quantity_col] * working["_estimated_price"]
            monetary_col = "_estimated_value"
        else:
            working["_estimated_value"] = 1.0
            monetary_col = "_estimated_value"
    elif quantity_col is not None:
        # Already set use_monetary=True and working[monetary_col] is ready
        pass
    else:
        # Fallback: use constant 1.0 for all transactions
        working["_estimated_value"] = 1.0
        monetary_col = "_estimated_value"

    if "transaction_id" in working.columns:
        aggregated = working.groupby(customer_col).agg(
            total_purchases=("transaction_id", "nunique"),
            total_spent_rupees=(monetary_col, "sum"),
        )
    else:
        aggregated = working.groupby(customer_col).agg(
            total_purchases=(customer_col, "size"),
            total_spent_rupees=(monetary_col, "sum"),
        )

    if date_col is not None:
        last_purchase = working.groupby(customer_col)[date_col].max()
        recency_days = (reference_date - last_purchase).dt.days
        aggregated = aggregated.join(recency_days.rename("last_purchase_days_ago"))
    else:
        aggregated["last_purchase_days_ago"] = 0

    aggregated = aggregated.reset_index().rename(columns={customer_col: "customer_id"})
    aggregated["frequency"] = aggregated["total_purchases"]
    aggregated["recency_days"] = aggregated["last_purchase_days_ago"].fillna(0)
    aggregated["monetary_value"] = aggregated["total_spent_rupees"].fillna(0.0)
    aggregated["average_order_value"] = aggregated.apply(
        lambda row: float(row["total_spent_rupees"]) / row["total_purchases"] if row["total_purchases"] else 0.0,
        axis=1,
    )

    # Assign RFM scores (1-4) using quantiles and map to human-friendly segments
    try:
        # Recency: lower is better -> invert labels so lowest recency gets highest score
        if "recency_days" in aggregated.columns and aggregated["recency_days"].nunique() > 1:
            aggregated["recency_score"] = pd.qcut(aggregated["recency_days"], 4, labels=[4, 3, 2, 1]).astype(int)
        else:
            aggregated["recency_score"] = 4

        if "frequency" in aggregated.columns and aggregated["frequency"].nunique() > 1:
            aggregated["frequency_score"] = pd.qcut(aggregated["frequency"], 4, labels=[1, 2, 3, 4]).astype(int)
        else:
            aggregated["frequency_score"] = 1

        if "monetary_value" in aggregated.columns and aggregated["monetary_value"].nunique() > 1:
            aggregated["monetary_score"] = pd.qcut(aggregated["monetary_value"], 4, labels=[1, 2, 3, 4]).astype(int)
        else:
            aggregated["monetary_score"] = 1

        aggregated["rfm_score"] = aggregated["recency_score"] + aggregated["frequency_score"] + aggregated["monetary_score"]

        def _map_segment(score: int) -> str:
            if score >= 10:
                return "Champions"
            if score >= 7:
                return "Loyal"
            if score >= 4:
                return "At Risk"
            return "Lost"

        aggregated["segment"] = aggregated["rfm_score"].apply(lambda v: _map_segment(int(v)))
    except Exception:
        aggregated["segment"] = "Unknown"
    rounded = aggregated.sort_values(["total_spent_rupees", "total_purchases"], ascending=False).reset_index(drop=True)
    for column in ["total_spent_rupees", "average_order_value", "monetary_value", "recency_days", "last_purchase_days_ago"]:
        if column in rounded.columns:
            rounded[column] = rounded[column].round(2)
    if "total_purchases" in rounded.columns:
        rounded["total_purchases"] = rounded["total_purchases"].round(0).astype(int)
    return rounded


def enrich_rfm_segments(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the RFM dataframe has standard columns and numeric types."""
    rfm_df = _normalize_columns(rfm_df)
    if rfm_df.empty:
        return rfm_df

    rename_map = {
        "total_spent": "total_spent_rupees",
        "spent": "total_spent_rupees",
        "last_purchase": "last_purchase_days_ago",
        "recency": "last_purchase_days_ago",
        "segment_label": "segment",
        "customer_segment": "segment",
    }
    rfm_df = rfm_df.rename(columns={k: v for k, v in rename_map.items() if k in rfm_df.columns})

    if "customer_id" in rfm_df.columns:
        rfm_df["customer_id"] = pd.to_numeric(rfm_df["customer_id"], errors="coerce")

    for column in ["total_purchases", "total_spent_rupees", "last_purchase_days_ago", "average_order_value"]:
        if column in rfm_df.columns:
            rfm_df[column] = pd.to_numeric(rfm_df[column], errors="coerce")

    if "average_order_value" not in rfm_df.columns and {"total_spent_rupees", "total_purchases"}.issubset(rfm_df.columns):
        rfm_df["average_order_value"] = rfm_df.apply(
            lambda row: float(row["total_spent_rupees"]) / row["total_purchases"] if row["total_purchases"] else 0.0,
            axis=1,
        )

    if "segment" not in rfm_df.columns:
        rfm_df["segment"] = "Unknown"

    return rfm_df


def build_customer_kmeans(rfm_df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Cluster customers using standardized RFM features."""
    rfm_df = enrich_rfm_segments(rfm_df)
    required = ["total_purchases", "total_spent_rupees", "last_purchase_days_ago"]
    if rfm_df.empty or not all(column in rfm_df.columns for column in required):
        return pd.DataFrame()

    model_df = rfm_df.dropna(subset=required).copy()
    if model_df.empty:
        return pd.DataFrame()

    if len(model_df) < n_clusters:
        n_clusters = max(1, len(model_df))

    features = model_df[required].astype(float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model_df["cluster"] = model.fit_predict(scaled)

    cluster_stats = (
        model_df.groupby("cluster")[required]
        .mean()
        .reset_index()
        .sort_values("cluster")
    )

    cluster_size = model_df.groupby("cluster").size().rename("cluster_size").reset_index()
    cluster_stats = cluster_stats.merge(cluster_size, on="cluster", how="left")
    for column in ["total_purchases", "total_spent_rupees", "last_purchase_days_ago"]:
        if column in cluster_stats.columns:
            cluster_stats[column] = cluster_stats[column].round(0)
    if "cluster_size" in cluster_stats.columns:
        cluster_stats["cluster_size"] = cluster_stats["cluster_size"].round(0).astype(int)
    return cluster_stats


def build_customer_kmeans_assignments(rfm_df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Return customer-level KMeans assignments for plotting and drill-downs."""
    rfm_df = enrich_rfm_segments(rfm_df)
    required = ["total_purchases", "total_spent_rupees", "last_purchase_days_ago"]
    if rfm_df.empty or not all(column in rfm_df.columns for column in required):
        return pd.DataFrame()

    model_df = rfm_df.dropna(subset=required).copy()
    if model_df.empty:
        return pd.DataFrame()

    if len(model_df) < n_clusters:
        n_clusters = max(1, len(model_df))

    features = model_df[required].astype(float)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model_df["cluster"] = model.fit_predict(scaled)
    result = model_df[["customer_id", "total_purchases", "total_spent_rupees", "last_purchase_days_ago", "average_order_value", "segment", "cluster"]].reset_index(drop=True)
    for column in ["total_purchases", "total_spent_rupees", "last_purchase_days_ago", "average_order_value"]:
        if column in result.columns:
            result[column] = result[column].round(2)
    if "customer_id" in result.columns:
        result["customer_id"] = result["customer_id"].astype(int)
    if "cluster" in result.columns:
        result["cluster"] = result["cluster"].astype(int)
        result["cluster_label"] = result["cluster"].map(lambda value: f"Cluster {value}")
    return result


def customer_summary_payload() -> dict:
    """Build a dashboard-ready summary payload from the available datasets."""
    customers = load_customers()
    transactions = load_transactions()
    preferences = load_preferences()
    rfm = compute_rfm_from_transactions(transactions) if not transactions.empty else enrich_rfm_segments(load_rfm_segments())

    if rfm.empty:
        rfm = pd.DataFrame(columns=[
            "customer_id",
            "total_purchases",
            "total_spent_rupees",
            "last_purchase_days_ago",
            "average_order_value",
            "segment",
        ])

    customer_count = int(len(customers)) if not customers.empty else int(rfm["customer_id"].nunique()) if not rfm.empty else 0
    active_customers = int((rfm["last_purchase_days_ago"] <= 30).sum()) if "last_purchase_days_ago" in rfm.columns and not rfm.empty else 0
    total_spent = float(rfm["total_spent_rupees"].sum()) if "total_spent_rupees" in rfm.columns and not rfm.empty else 0.0
    avg_order = float(rfm["average_order_value"].mean()) if "average_order_value" in rfm.columns and not rfm.empty else 0.0

    segment_counts = (
        rfm["segment"].fillna("Unknown").value_counts().reset_index()
        if not rfm.empty and "segment" in rfm.columns
        else pd.DataFrame(columns=["index", "segment"])
    )
    if not segment_counts.empty:
        segment_counts.columns = ["segment", "count"]

    kmeans_stats = build_customer_kmeans(rfm)
    kmeans_assignments = build_customer_kmeans_assignments(rfm)

    top_customers = pd.DataFrame()
    if not rfm.empty and "total_spent_rupees" in rfm.columns:
        top_customers = rfm.sort_values("total_spent_rupees", ascending=False).head(10).copy()
        for column in ["total_spent_rupees", "average_order_value", "last_purchase_days_ago"]:
            if column in top_customers.columns:
                top_customers[column] = top_customers[column].round(2)
        if "total_purchases" in top_customers.columns:
            top_customers["total_purchases"] = top_customers["total_purchases"].round(0).astype(int)

    category_counts = pd.DataFrame()
    if not preferences.empty and "primary_category" in preferences.columns:
        category_counts = preferences["primary_category"].value_counts().reset_index()
        category_counts.columns = ["category", "count"]

    return {
        "customer_count": customer_count,
        "active_customers": active_customers,
        "total_spent": total_spent,
        "average_order_value": avg_order,
        "customers": customers,
        "transactions": transactions,
        "rfm": rfm,
        "segment_counts": segment_counts,
        "kmeans_stats": kmeans_stats,
        "kmeans_assignments": kmeans_assignments,
        "top_customers": top_customers,
        "category_counts": category_counts,
        "preferences": preferences,
    }


def recommend_products_for_high_value_customers(top_n: int = 5) -> dict[str, Any]:
    """Recommend products based on real purchases from high-value customers."""
    transactions = load_transactions()
    if transactions.empty:
        return {
            "status": "no_transactions",
            "message": "No customer transactions found.",
            "recommendations": pd.DataFrame(),
        }

    rfm = enrich_rfm_segments(load_rfm_segments())
    if rfm.empty:
        rfm = compute_rfm_from_transactions(transactions)

    if rfm.empty or "customer_id" not in rfm.columns:
        return {
            "status": "no_rfm",
            "message": "RFM data unavailable for identifying high-value customers.",
            "recommendations": pd.DataFrame(),
        }

    rfm = rfm.copy()
    rfm["customer_id"] = pd.to_numeric(rfm["customer_id"], errors="coerce")
    rfm = rfm.dropna(subset=["customer_id"])

    high_value = pd.DataFrame()
    if "segment" in rfm.columns:
        segment_text = rfm["segment"].astype(str).str.lower()
        high_value = rfm[
            segment_text.str.contains("high value", na=False)
            | segment_text.str.contains("high-value", na=False)
            | segment_text.str.contains("vip", na=False)
            | segment_text.str.contains("champion", na=False)
        ].copy()

    # Fallback for datasets that don't label segments the same way.
    if high_value.empty and "total_spent_rupees" in rfm.columns:
        spend = pd.to_numeric(rfm["total_spent_rupees"], errors="coerce").fillna(0.0)
        threshold = float(spend.quantile(0.80))
        high_value = rfm[spend >= threshold].copy()

    if high_value.empty:
        return {
            "status": "no_high_value_customers",
            "message": "No high-value customers found in the current dataset.",
            "recommendations": pd.DataFrame(),
        }

    customer_col = _pick_column(transactions, ["customer_id", "customerid", "client_id"])
    product_col = _pick_column(transactions, ["product_id", "productid", "item_id"])
    quantity_col = _pick_column(transactions, ["quantity", "qty", "units"])
    tx_col = _pick_column(transactions, ["transaction_id", "invoice_id", "order_id"])

    if customer_col is None or product_col is None:
        return {
            "status": "missing_columns",
            "message": "transactions data requires customer_id and product_id columns.",
            "recommendations": pd.DataFrame(),
        }

    tx = transactions.copy()
    tx[customer_col] = pd.to_numeric(tx[customer_col], errors="coerce")
    tx[product_col] = pd.to_numeric(tx[product_col], errors="coerce")
    tx = tx.dropna(subset=[customer_col, product_col])
    tx[customer_col] = tx[customer_col].astype(int)
    tx[product_col] = tx[product_col].astype(int)

    if quantity_col is not None:
        tx[quantity_col] = pd.to_numeric(tx[quantity_col], errors="coerce").fillna(0.0)
    else:
        quantity_col = "_default_quantity"
        tx[quantity_col] = 1.0

    high_value_ids = set(high_value["customer_id"].astype(int).tolist())
    hv_tx = tx[tx[customer_col].isin(high_value_ids)].copy()
    if hv_tx.empty:
        return {
            "status": "no_high_value_transactions",
            "message": "High-value customers exist, but no matching transactions were found.",
            "recommendations": pd.DataFrame(),
        }

    group_cols = [product_col]
    agg_map: dict[str, tuple[str, str]] = {
        "distinct_customers": (customer_col, "nunique"),
        "total_units": (quantity_col, "sum"),
    }
    if tx_col is not None:
        agg_map["order_count"] = (tx_col, "nunique")
    else:
        agg_map["order_count"] = (customer_col, "size")

    ranked = (
        hv_tx.groupby(group_cols)
        .agg(**agg_map)
        .reset_index()
        .rename(columns={product_col: "product_id"})
    )

    # Map product ids to names from live catalog when possible.
    conn = get_connection()
    try:
        product_map_df = pd.read_sql_query("SELECT id, name FROM products", conn)
    finally:
        conn.close()

    if not product_map_df.empty:
        product_map_df["id"] = pd.to_numeric(product_map_df["id"], errors="coerce")
        product_map_df = product_map_df.dropna(subset=["id"])
        product_map_df["id"] = product_map_df["id"].astype(int)
        ranked = ranked.merge(
            product_map_df.rename(columns={"id": "product_id", "name": "product_name"}),
            on="product_id",
            how="left",
        )

        # Fallback for legacy datasets where transaction product ids start at 1..N,
        # while current DB ids have shifted due to SQLite autoincrement.
        missing_name_ratio = ranked["product_name"].isna().mean() if "product_name" in ranked.columns and len(ranked) else 1.0
        if missing_name_ratio > 0.5:
            ordered = product_map_df.sort_values("id").reset_index(drop=True)
            ordered["legacy_product_id"] = ordered.index + 1
            ranked = ranked.merge(
                ordered[["legacy_product_id", "name"]].rename(
                    columns={"legacy_product_id": "product_id", "name": "legacy_product_name"}
                ),
                on="product_id",
                how="left",
            )
            ranked["product_name"] = ranked["product_name"].fillna(ranked["legacy_product_name"])
            ranked = ranked.drop(columns=["legacy_product_name"], errors="ignore")
    else:
        ranked["product_name"] = pd.NA

    ranked["product_name"] = ranked["product_name"].fillna(
        ranked["product_id"].map(lambda value: f"Product ID {int(value)}")
    )

    total_hv_customers = max(1, len(high_value_ids))
    ranked["customer_penetration_pct"] = (
        ranked["distinct_customers"].astype(float) / float(total_hv_customers) * 100.0
    ).round(2)

    ranked = ranked.sort_values(
        ["distinct_customers", "order_count", "total_units"],
        ascending=False,
    ).head(top_n)

    for numeric_col in ["distinct_customers", "order_count", "total_units"]:
        ranked[numeric_col] = pd.to_numeric(ranked[numeric_col], errors="coerce").fillna(0).astype(int)

    return {
        "status": "ok",
        "high_value_customer_count": int(len(high_value_ids)),
        "recommendations": ranked.reset_index(drop=True),
    }