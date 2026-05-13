# Onboarding Guide: Daily Operations

**For:** New team members, store staff, analytics users  
**Read Time:** 20 minutes  
**Version:** 1.0

---

## Day 1: System Access & Dashboard Tour

### 1.1 Getting Access

**Backend API (FastAPI):**
- URL: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Swagger docs: `http://localhost:8000/docs` (explore API endpoints interactively)

**Frontend Dashboard (Streamlit):**
- URL: `http://localhost:8501`
- No login required (local setup)
- 3 main pages: Dashboard, AI Assistant, Inventory

### 1.2 Dashboard Pages

**Page 1: 📊 Dashboard**
- KPIs: Total Customers, Active Customers, Revenue, Avg Order Value
- Charts: Sales trend, top products, customer segments, churn risk
- Use for: Daily business snapshot, Monday morning briefing

**Page 2: 🤖 AI Assistant**
- Chat interface for natural language queries
- Example: "How many oil bottles in stock?" or "Show customer segmentation"
- Try: Ask it inventory, customer, and forecast questions
- Smart routing: automatically picks right agent (inventory/customer/forecast)

**Page 3: 📦 Inventory**
- Current stock levels for all products
- Search/filter by product name
- Stock visualization chart
- Use for: Daily stock checks, reorder decisions

---

## Day 2: Making Your First Stock Update

### 2.1 Via Dashboard (Easiest)

**Add Stock:**
1. Go to Inventory page
2. Current stock shown in table
3. Use AI Assistant: "Add 10 milk packets"
4. Confirm stock updated

**Sell Items:**
1. AI Assistant: "Sell 3 bread loaves"
2. Check Dashboard to see revenue updated
3. View transaction in "Recent Transactions" table

### 2.2 Via API (For Developers)

**Add Stock:**
```bash
curl -X POST http://localhost:8000/api/inventory/update \
  -H "Content-Type: application/json" \
  -d '{"product_name": "milk", "quantity": 10}'
```

**Record Sale:**
```bash
curl -X POST http://localhost:8000/api/transactions/record \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 101,
    "product_name": "milk",
    "quantity": 2,
    "unit_price": 45.0
  }'
```

---

## Day 3: Understanding Customer Analytics

### 3.1 RFM Segmentation

**What it means:**
- **R**ecency: Days since last purchase (lower is better)
- **F**requency: How many times customer bought (higher is better)
- **M**onetary: Total amount spent (higher is better)

**Segments you'll see:**
- 🏆 Champions: Recent, frequent, high-spend → VIP treatment
- ⭐ Loyal: Decent recent activity, regular spending → cross-sell
- ⚠️ At Risk: Hasn't bought recently, but used to spend → win-back offers
- ❌ Lost: No recent activity → re-engagement campaign

**Where to find it:**
- Dashboard page, scroll down to "Customer Segments" chart
- AI Assistant: "Show customer segmentation summary"

### 3.2 Top Customers

**Use case:** Who should we prioritize for promotions?

**Find it:**
- Dashboard, "Top Customers" card
- AI Assistant: "List top customers"

**Action items:**
- Call top customers for feedback
- Offer loyalty rewards
- Invite to exclusive events

---

## Day 4: Forecasting & Planning

### 4.1 Sales Forecast

**What it does:** Predicts how much of each product will sell next 30 days  
**Powered by:** Prophet time-series model (learns from history)

**How to use it:**
1. AI Assistant: "Forecast milk demand for next 30 days"
2. Response: "Predicted total sales: 250 units"
3. Use this to order from supplier with buffer

**When forecast is wrong:**
- Recent stockouts → forecast might underestimate demand
- Seasonal events → add context to forecast ("accounting for Diwali festival")
- New supplier → need more historical data

### 4.2 Making Reorder Decisions

**Formula (simple):**
```
Reorder Amount = (Forecasted Demand) + (Safety Stock) - (Current Stock)
Safety Stock = 20% of avg monthly demand
```

**Example:**
- Forecast: 250 units milk next 30 days
- Avg monthly: 280 units
- Safety stock: 280 * 0.2 = 56 units
- Current stock: 120 units
- Reorder = 250 + 56 - 120 = 186 units

---

## Day 5: Common Tasks & Shortcuts

### 5.1 Morning Routine (10 minutes)

1. Open Dashboard page
2. Check KPIs: any unusual changes?
3. Scroll to "Low Stock Alert": any products < 20 units?
4. If yes: reorder via AI Assistant or manually

### 5.2 End-of-Day Checklist

1. Record all transactions: "Sell X of Product Y"
2. Physical count spot-check (5 random products)
3. AI Assistant: "What's the current stock?" to verify
4. If any discrepancies > 5 units, escalate to Manager

### 5.3 Weekly Review (Fridays)

1. Run full reconciliation: `python tools/customer_analytics.py --reconcile-full`
2. Check "Weekly Reconciliation Report" in Inventory
3. Review customer segments: any new At-Risk customers?
4. Plan promotions based on segments

---

## FAQ & Troubleshooting

### Q: Stock shows negative! What do I do?
**A:** Don't panic. See SOP_INVENTORY_RECONCILIATION.md, Section 2.2-2.4. Usually a sync issue, fixed in < 10 min.

### Q: AI Assistant doesn't understand my question
**A:** Try simpler phrasing. Instead of "Give me the latest stuff," say "Show recent transactions."  
List of working questions: see dashboard page under "Example Queries."

### Q: Forecast seems way off
**A:** Forecasts use only historical data. If recent events (sale, promo, stockout) happened, manually adjust.  
Ask AI: "Predict rice sales adjusted for 15% discount promotion"

### Q: How do I know which customer to follow up with?
**A:** Dashboard > Customer Segments. Pick an "At Risk" customer, check their spend & last purchase date.

### Q: Can I delete a transaction?
**A:** No. All transactions are immutable for audit trail. If mistake: log new corrective transaction and note in comments.

---

## Important Numbers to Know

| Metric | Threshold | Action |
|--------|-----------|--------|
| Low Stock Alert | < 20 units | Reorder immediately |
| Negative Stock | < 0 | Escalate to Manager |
| Product Variance | > 10% weekly | Investigate, document, fix |
| At-Risk Churn Risk | > 60 days no purchase | Contact customer |
| Top Customer Spend | > ₹10,000 lifetime | VIP program invite |

---

## Contacts

- **Daily Questions:** Ask on Slack #retail-ops
- **AI Assistant Issues:** #copilot-help
- **Database/Backend Issues:** Backend dev (on-call)
- **Escalations:** Store Manager or Operations Lead

---

## Next Steps After This Guide

1. ✅ Complete "Day 1-5" sections above
2. ✅ Read SOP_INVENTORY_RECONCILIATION.md (daily use)
3. ✅ Bookmark TROUBLESHOOTING_GUIDES.md (for when issues happen)
4. ✅ Sign off: your manager confirms you're ready
5. ✅ First week: pair with experienced staff member
