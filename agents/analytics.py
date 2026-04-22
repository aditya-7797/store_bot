from backend.models.apriori_analysis import get_apriori_rules
from tools.inventory_tools import get_all_products


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
