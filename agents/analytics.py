from backend.models.apriori_analysis import get_apriori_rules
from tools.inventory_tools import get_all_products
from tools.customer_analytics import customer_summary_payload

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


def analytics_agent(state: dict) -> dict:
    query = state.get("query", "")

    q = query.lower()
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
