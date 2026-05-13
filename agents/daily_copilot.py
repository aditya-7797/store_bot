"""Daily Decision Copilot

Provides a lightweight, non-RAG set of business decisions computed from
the transactional SQLite DB and existing CSVs. Exposes functions that
return answers for the five owner questions.
"""
from __future__ import annotations

import sqlite3
from typing import List, Dict, Any
from datetime import datetime, timedelta
from backend.config import settings
import pandas as pd
from pathlib import Path


def _connect_db():
    return sqlite3.connect(settings.SQLITE_DB)


def _load_sales_df(days: int = 90) -> pd.DataFrame:
    conn = _connect_db()
    try:
        query = "SELECT s.created_at as date, p.name as product_name, s.quantity as quantity, s.price as price FROM sales s JOIN products p ON s.product_id = p.id"
        df = pd.read_sql(query, conn, parse_dates=["date"])
        if df.empty:
            return pd.DataFrame(columns=["date", "product_name", "quantity", "price"])
        cutoff = datetime.utcnow() - timedelta(days=days)
        df = df[df["date"] >= cutoff]
        return df
    finally:
        conn.close()


def reorder_recommendations(lead_time_days: int = 7, safety_days: int = 3, top_n: int = 20) -> List[Dict[str, Any]]:
    """Return list of products to reorder and suggested quantities.

    Simple rule: compute avg daily sales over last 30 days; reorder if
    current_stock < (avg_daily * (lead_time + safety)). Suggested qty =
    target - current_stock where target = avg_daily * (lead_time + safety + 7)
    """
    # load current stock
    conn = _connect_db()
    try:
        prod_df = pd.read_sql("SELECT id, name, stock FROM products", conn)
    finally:
        conn.close()

    sales = _load_sales_df(days=90)
    if sales.empty or prod_df.empty:
        return []

    daily = (
        sales.groupby("product_name")["quantity"].sum() / 30.0
    ).rename("avg_daily")

    merged = prod_df.merge(daily.rename("avg_daily"), left_on="name", right_index=True, how="left").fillna(0)
    merged["target"] = merged["avg_daily"] * (lead_time_days + safety_days + 7)
    merged["to_order"] = (merged["target"] - merged["stock"]).clip(lower=0).round().astype(int)
    to_order = (
        merged[merged["to_order"] > 0][["name", "stock", "avg_daily", "to_order"]]
        .sort_values("to_order", ascending=False)
        .head(top_n)
    )

    return [
        {
            "product": row["name"],
            "current_stock": int(row["stock"]),
            "avg_daily": float(row["avg_daily"]),
            "suggested_order": int(row["to_order"]),
        }
        for _, row in to_order.iterrows()
    ]


def stockout_risk(top_k: int = 5, horizon_days: int = 7) -> List[Dict[str, Any]]:
    """Predict which products may stock out in the next `horizon_days` using simple extrapolation."""
    conn = _connect_db()
    try:
        prod_df = pd.read_sql("SELECT id, name, stock FROM products", conn)
    finally:
        conn.close()

    sales = _load_sales_df(days=30)
    if sales.empty or prod_df.empty:
        return []

    daily = (sales.groupby("product_name")["quantity"].sum() / 30.0).rename("avg_daily")
    merged = prod_df.merge(daily.rename("avg_daily"), left_on="name", right_index=True, how="left").fillna(0)
    merged["expected_consumption"] = merged["avg_daily"] * horizon_days
    merged["days_left"] = merged.apply(lambda r: float('inf') if r["avg_daily"]==0 else r["stock"]/r["avg_daily"], axis=1)
    risk = merged.sort_values(["days_left", "stock"]).head(top_k)

    return [
        {
            "product": row["name"],
            "current_stock": int(row["stock"]),
            "avg_daily": float(row["avg_daily"]),
            "days_left": float(row["days_left"]) if row["days_left"]!=float('inf') else None,
        }
        for _, row in risk.iterrows()
    ]


def push_recommendations(top_n: int = 10) -> List[Dict[str, Any]]:
    """Recommend items to promote: high margin but low recent sales.

    Uses `price` in sales as proxy for margin when available.
    """
    sales = _load_sales_df(days=90)
    conn = _connect_db()
    try:
        prod_df = pd.read_sql("SELECT id, name, stock FROM products", conn)
    finally:
        conn.close()

    if sales.empty or prod_df.empty:
        return []

    recent = sales.groupby("product_name")["quantity"].sum().rename("qty_90")
    avg_price = sales.groupby("product_name")["price"].mean().rename("avg_price")
    merged = prod_df.merge(recent, left_on="name", right_index=True, how="left").merge(avg_price, left_on="name", right_index=True, how="left").fillna(0)
    # Use average realized selling price as a proxy when the product table has no price/cost columns.
    merged["margin_est"] = merged["avg_price"].clip(lower=0)
    merged["score"] = merged["margin_est"] / (1 + merged["qty_90"])  # prioritize high margin low sales
    recs = merged.sort_values("score", ascending=False).head(top_n)

    return [
        {"product": r["name"], "margin_est": float(r["margin_est"]), "qty_90": int(r["qty_90"]) if not pd.isna(r["qty_90"]) else 0}
        for _, r in recs.iterrows()
    ]








def daily_snapshot() -> Dict[str, Any]:
    return {
        "reorder_recommendations": reorder_recommendations(),
        "stockout_risk": stockout_risk(),
        "push_recommendations": push_recommendations(),
        "generated_at": datetime.utcnow().isoformat(),
    }
