"""Apriori analysis utilities for market basket insights."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from tools.db import get_connection


def _fetch_sales_baskets() -> pd.DataFrame:
    """Return sales line items with transaction and product names."""
    conn = get_connection()
    query = """
        SELECT s.transaction_id, p.name AS product_name
        FROM sales s
        JOIN products p ON p.id = s.product_id
        WHERE s.transaction_id IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_apriori_rules(
    min_support: float = 0.02,
    min_confidence: float = 0.25,
    min_lift: float = 1.0,
    top_n: int = 20,
) -> Dict[str, Any]:
    """Generate Apriori association rules and return serializable payload."""
    sales_df = _fetch_sales_baskets()

    if sales_df.empty:
        return {
            "summary": {
                "transactions": 0,
                "distinct_products": 0,
                "frequent_itemsets": 0,
                "rules": 0,
            },
            "rules": [],
        }

    basket = (
        sales_df.assign(value=1)
        .pivot_table(
            index="transaction_id",
            columns="product_name",
            values="value",
            aggfunc="max",
            fill_value=0,
        )
        .astype(bool)
    )

    frequent_itemsets = apriori(basket, min_support=min_support, use_colnames=True)

    if frequent_itemsets.empty:
        return {
            "summary": {
                "transactions": int(basket.shape[0]),
                "distinct_products": int(basket.shape[1]),
                "frequent_itemsets": 0,
                "rules": 0,
            },
            "rules": [],
        }

    rules_df = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

    if rules_df.empty:
        return {
            "summary": {
                "transactions": int(basket.shape[0]),
                "distinct_products": int(basket.shape[1]),
                "frequent_itemsets": int(len(frequent_itemsets)),
                "rules": 0,
            },
            "rules": [],
        }

    rules_df = rules_df[rules_df["lift"] >= min_lift].copy()

    if rules_df.empty:
        return {
            "summary": {
                "transactions": int(basket.shape[0]),
                "distinct_products": int(basket.shape[1]),
                "frequent_itemsets": int(len(frequent_itemsets)),
                "rules": 0,
            },
            "rules": [],
        }

    rules_df["antecedents"] = rules_df["antecedents"].apply(lambda x: sorted(list(x)))
    rules_df["consequents"] = rules_df["consequents"].apply(lambda x: sorted(list(x)))
    rules_df = rules_df.sort_values(["lift", "confidence", "support"], ascending=False).head(top_n)

    payload_rules: List[Dict[str, Any]] = []
    for _, row in rules_df.iterrows():
        payload_rules.append(
            {
                "antecedents": row["antecedents"],
                "consequents": row["consequents"],
                "support": round(float(row["support"]), 4),
                "confidence": round(float(row["confidence"]), 4),
                "lift": round(float(row["lift"]), 4),
                "leverage": round(float(row["leverage"]), 4),
                "conviction": round(float(row["conviction"]), 4) if row["conviction"] != float("inf") else None,
            }
        )

    return {
        "summary": {
            "transactions": int(basket.shape[0]),
            "distinct_products": int(basket.shape[1]),
            "frequent_itemsets": int(len(frequent_itemsets)),
            "rules": int(len(payload_rules)),
        },
        "rules": payload_rules,
    }
