from backend.models.apriori_analysis import get_apriori_rules
import math
import re
from tools.inventory_tools import get_all_products
from tools.customer_analytics import customer_summary_payload, recommend_products_for_high_value_customers
from tools.db import get_connection

SEGMENT_KEYWORDS = [
    "customer",
    "customers",
    "segment",
    "segmentation",
    "rfm",
    "top customers",
    "top customer",
    "churn",
    "lifetime value",
    "ltv",
    "customer segment",
    "which customers",
    "loyal",
    "high value",
    "low value",
    "recency",
    "frequency",
    "monetary",
    "cluster",
]

TOP_CUSTOMER_KEYWORDS = [
    "top customers",
    "top customer",
    "high value",
    "high-value",
    "best customers",
    "best customer",
    "most valuable",
    "customers",
]


def _resolve_product_from_query(query: str) -> str | None:
    """Resolve the best matching product from query text using catalog names."""
    q = query.lower()
    product_names = [name for name, _ in get_all_products()]

    # 1) Exact product name match in query
    exact_matches = [name for name in product_names if name in q]
    if exact_matches:
        return sorted(exact_matches, key=len, reverse=True)[0]

    # 2) Token overlap match (helps map 'bread' -> 'bread loaf')
    best_name = None
    best_score = 0
    for name in product_names:
        tokens = [t for t in name.split() if len(t) >= 3]
        score = sum(1 for t in tokens if t in q)
        if score > best_score:
            best_score = score
            best_name = name

    return best_name if best_score > 0 else None


def _extract_price_change_fraction(query: str) -> float | None:
    """Extract price change from query as fraction (e.g. +0.05, -0.10)."""
    q = query.lower()
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", q)
    if not match:
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:percent|percentage)", q)
    if not match:
        return None

    value = float(match.group(1)) / 100.0
    if value == 0:
        return 0.0

    # Direction words can override unsigned values.
    if value > 0:
        if any(k in q for k in ["decrease", "reduce", "drop", "lower"]):
            value = -abs(value)
        elif any(k in q for k in ["increase", "raise", "up", "hike"]):
            value = abs(value)
    return value


def _estimate_price_elasticity(product: str) -> tuple[float | None, str]:
    """Estimate log-log elasticity from historical sales rows for a product."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT s.price, s.quantity
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE lower(p.name) = lower(?)
              AND s.price IS NOT NULL
              AND s.price > 0
              AND s.quantity IS NOT NULL
              AND s.quantity > 0
            """,
            (product,),
        ).fetchall()
    finally:
        conn.close()

    if len(rows) < 15:
        return None, "insufficient_rows"

    x = [math.log(float(r[0])) for r in rows]
    y = [math.log(float(r[1])) for r in rows]
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    var_x = sum((v - mean_x) ** 2 for v in x)
    if var_x <= 1e-12:
        return None, "insufficient_price_variation"

    cov_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    slope = cov_xy / var_x
    return float(slope), "ok"


def _simulate_price_change(product: str, price_change_fraction: float) -> dict:
    """Simulate revenue impact for a product using real sales and estimated elasticity."""
    conn = get_connection()
    try:
        recent_row = conn.execute(
            """
            SELECT
                AVG(s.price) AS avg_price,
                SUM(s.quantity) AS total_qty,
                COUNT(*) AS row_count
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE lower(p.name) = lower(?)
              AND s.price IS NOT NULL
              AND s.price > 0
              AND datetime(s.created_at) >= datetime('now', '-30 days')
            """,
            (product,),
        ).fetchone()

        all_row = conn.execute(
            """
            SELECT
                AVG(s.price) AS avg_price,
                SUM(s.quantity) AS total_qty,
                COUNT(*) AS row_count
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE lower(p.name) = lower(?)
              AND s.price IS NOT NULL
              AND s.price > 0
            """,
            (product,),
        ).fetchone()
    finally:
        conn.close()

    source = "last_30_days"
    avg_price = float(recent_row[0]) if recent_row and recent_row[0] is not None else 0.0
    base_qty = float(recent_row[1]) if recent_row and recent_row[1] is not None else 0.0
    if avg_price <= 0 or base_qty <= 0:
        source = "all_time"
        avg_price = float(all_row[0]) if all_row and all_row[0] is not None else 0.0
        base_qty = float(all_row[1]) if all_row and all_row[1] is not None else 0.0

    if avg_price <= 0 or base_qty <= 0:
        return {"status": "no_sales_data"}

    elasticity, elasticity_status = _estimate_price_elasticity(product)
    used_default_elasticity = False
    if elasticity is None:
        # Data-safe fallback: hold quantity constant when elasticity is not identifiable.
        elasticity = 0.0
        used_default_elasticity = True

    volume_change_fraction = float(elasticity) * float(price_change_fraction)
    projected_qty = max(0.0, base_qty * (1.0 + volume_change_fraction))
    projected_price = avg_price * (1.0 + price_change_fraction)

    current_revenue = base_qty * avg_price
    projected_revenue = projected_qty * projected_price

    return {
        "status": "ok",
        "source": source,
        "avg_price": avg_price,
        "base_qty": base_qty,
        "current_revenue": current_revenue,
        "projected_price": projected_price,
        "projected_qty": projected_qty,
        "projected_revenue": projected_revenue,
        "price_change_fraction": price_change_fraction,
        "volume_change_fraction": volume_change_fraction,
        "revenue_change_fraction": (projected_revenue / current_revenue - 1.0) if current_revenue > 0 else 0.0,
        "elasticity": elasticity,
        "elasticity_status": elasticity_status,
        "used_default_elasticity": used_default_elasticity,
    }


def analytics_agent(state: dict) -> dict:
    query = state.get("query", "")

    q = query.lower()
    wants_price_scenario = (
        "price" in q
        and any(k in q for k in ["what if", "increase", "decrease", "raise", "reduce", "%", "percent"])
    )
    wants_customer_recommendations = (
        any(k in q for k in ["recommend", "recommendation", "suggest", "products for", "what should"])
        and any(k in q for k in ["customer", "customers", "high value", "high-value", "vip"])
    )
    wants_segment_summary = any(
        k in q
        for k in [
            "segment",
            "segmentation",
            "rfm",
            "churn",
            "lifetime value",
            "ltv",
            "recency",
            "frequency",
            "monetary",
            "cluster",
        ]
    )
    wants_top_customers = any(k in q for k in TOP_CUSTOMER_KEYWORDS)

    if wants_price_scenario:
        product = _resolve_product_from_query(query)
        if not product:
            state["response"] = "I couldn't identify the product for price simulation. Try: 'What if I increase bread loaf price by 5%?'"
            return state

        pct = _extract_price_change_fraction(query)
        if pct is None:
            state["response"] = "Please include a price change percentage, for example: 'increase bread loaf price by 5%'."
            return state

        sim = _simulate_price_change(product, pct)
        if sim.get("status") != "ok":
            state["response"] = f"I couldn't find enough priced sales data for '{product}' to run this simulation."
            return state

        direction = "increase" if pct >= 0 else "decrease"
        lines = [
            f"Price-change simulation for {product}:",
            f"- Scenario: {direction} price by {abs(pct) * 100:.1f}%",
            f"- Baseline source: {sim.get('source').replace('_', ' ')}",
            f"- Current avg unit price: ₹{sim.get('avg_price', 0.0):.2f}",
            f"- Baseline units: {sim.get('base_qty', 0.0):.0f}",
            f"- Baseline revenue: ₹{sim.get('current_revenue', 0.0):.2f}",
            f"- Projected unit price: ₹{sim.get('projected_price', 0.0):.2f}",
            f"- Projected units: {sim.get('projected_qty', 0.0):.0f}",
            f"- Projected revenue: ₹{sim.get('projected_revenue', 0.0):.2f}",
            f"- Revenue impact: {sim.get('revenue_change_fraction', 0.0) * 100:.2f}%",
        ]

        if sim.get("used_default_elasticity"):
            lines.append("- Demand response model: not enough price variation, so quantity was held constant.")
        else:
            lines.append(f"- Demand response model: estimated price elasticity = {sim.get('elasticity', 0.0):.3f}")

        state["response"] = "\n".join(lines)
        return state

    if wants_customer_recommendations:
        try:
            rec_payload = recommend_products_for_high_value_customers(top_n=5)
        except Exception:
            state["response"] = "I couldn't compute high-value customer recommendations right now. Please try again later."
            return state

        if rec_payload.get("status") != "ok":
            state["response"] = rec_payload.get(
                "message",
                "I couldn't find enough data to recommend products for high-value customers.",
            )
            return state

        rec_df = rec_payload.get("recommendations")
        if rec_df is None or getattr(rec_df, "empty", True):
            state["response"] = "No recommendation candidates were found for high-value customers in current data."
            return state

        hv_count = int(rec_payload.get("high_value_customer_count", 0))
        lines = [
            f"Recommended products for high-value customers:"
        ]
        for _, row in rec_df.iterrows():
            name = str(row.get("product_name", "Unknown product"))
            buyers = int(row.get("distinct_customers", 0))
            orders = int(row.get("order_count", 0))
            units = int(row.get("total_units", 0))
            penetration = float(row.get("customer_penetration_pct", 0.0))
            lines.append(
                f"- {name}: bought by {buyers} high-value customers ({penetration:.1f}%), orders={orders}, units={units}"
            )

        state["response"] = "\n".join(lines)
        return state

    # If this looks like a customer analytics question, use customer analytics
    if wants_segment_summary or wants_top_customers:
        try:
            payload = customer_summary_payload()
        except Exception:
            state["response"] = "I couldn't load customer analytics right now. Please try again later."
            return state

        segment_counts = payload.get("segment_counts")
        top_customers = payload.get("top_customers")
        kmeans_stats = payload.get("kmeans_stats")

        if wants_segment_summary:
            lines = ["Customer segmentation summary:"]

            if isinstance(segment_counts, dict) or not getattr(segment_counts, "empty", True):
                try:
                    # segment_counts may be a DataFrame; handle both
                    if hasattr(segment_counts, "to_dict"):
                        seg_df = segment_counts
                        if not seg_df.empty:
                            for _, row in seg_df.iterrows():
                                seg = row.get("segment") if "segment" in row.index else row.get(0)
                                cnt = row.get("count") if "count" in row.index else row.get(1)
                                lines.append(f"- {seg}: {int(cnt)} customers")
                    else:
                        lines.append("- No segment counts available")
                except Exception:
                    lines.append("- No segment counts available")
            else:
                lines.append("- No segment counts available")

            if kmeans_stats is not None and hasattr(kmeans_stats, "to_dict"):
                try:
                    k_df = kmeans_stats
                    if not k_df.empty:
                        lines.append("")
                        lines.append("Cluster summaries (sample):")
                        for _, r in k_df.head(3).iterrows():
                            label = r.get("cluster_label", str(r.get("cluster", "")))
                            size = int(r.get("cluster_size", 0)) if "cluster_size" in r.index else 0
                            avg_spent = float(r.get("total_spent_rupees", 0.0)) if "total_spent_rupees" in r.index else 0.0
                            lines.append(f"- {label}: size={size}, avg_spent=₹{avg_spent:.0f}")
                except Exception:
                    pass

            lines.append("")
            lines.append("Recommended actions:")
            lines.append("- Target high-value customers with loyalty offers and bulk discounts.")
            lines.append("- Re-engage recent but low-frequency customers with cross-sell bundles.")
            lines.append("- Monitor high-churn segments for retention campaigns.")

            state["response"] = "\n".join(lines)
            return state

        lines = ["Top customers by spend:"]
        if top_customers is not None and hasattr(top_customers, "to_dict"):
            try:
                top_df = top_customers
                if not top_df.empty:
                    for _, r in top_df.head(5).iterrows():
                        cid = int(r.get("customer_id", 0))
                        spent = float(r.get("total_spent_rupees", 0.0)) if "total_spent_rupees" in r.index else float(r.get("total_spent_rupees", 0.0))
                        lines.append(f"- Customer {cid}: ₹{spent:.2f}")
                else:
                    lines.append("- No customer spend data available")
            except Exception:
                lines.append("- No customer spend data available")
        else:
            lines.append("- No customer spend data available")

        state["response"] = "\n".join(lines)
        return state

    product = _resolve_product_from_query(query)
    if not product:
        state["response"] = (
            "I couldn't identify the product for recommendation. "
            "Please ask like: 'What can I sell with bread loaf?'"
        )
        return state

    analysis = get_apriori_rules(min_support=0.02, min_confidence=0.2, min_lift=1.0, top_n=300)
    rules = analysis.get("rules", [])

    # Find rules where selected product appears in antecedents.
    matches = [r for r in rules if product in r.get("antecedents", [])]

    if not matches:
        state["response"] = (
            f"No strong basket recommendations found for '{product}' at current thresholds. "
            "Try lowering support/confidence in Analytics page."
        )
        return state

    # Deduplicate by recommended product name and keep strongest rule for each item.
    best_by_item: dict[str, dict] = {}
    for rule in matches:
        for item in rule.get("consequents", []):
            existing = best_by_item.get(item)
            current_score = (rule.get("confidence", 0), rule.get("lift", 0), rule.get("support", 0))
            if not existing:
                best_by_item[item] = rule
                continue
            existing_score = (
                existing.get("confidence", 0),
                existing.get("lift", 0),
                existing.get("support", 0),
            )
            if current_score > existing_score:
                best_by_item[item] = rule

    ranked_items = sorted(
        best_by_item.items(),
        key=lambda kv: (
            kv[1].get("confidence", 0),
            kv[1].get("lift", 0),
            kv[1].get("support", 0),
        ),
        reverse=True,
    )[:3]

    lines = [f"Top products to sell with {product}:"]
    for item, rule in ranked_items:
        lines.append(
            f"- {item} (confidence: {rule.get('confidence', 0):.2f}, lift: {rule.get('lift', 0):.2f})"
        )

    state["response"] = "\n".join(lines)
    return state
