# SOP: Inventory Update & Reconciliation

**Ownership:** Operations Manager  
**Last Updated:** May 2026  
**Version:** 1.0

---

## Overview

This SOP defines how to update inventory, handle stock discrepancies, and reconcile database against physical counts.

---

## 1. Normal Stock Update Process

### 1.1 Adding Stock (Receiving)

**When:** New goods arrive from supplier  
**System:** Use `/api/inventory/update` endpoint or AI Assistant

**Steps:**
1. Physical count items received
2. Verify supplier invoice matches count
3. Use natural language: "Add 50 milk packets"
   - OR use API: `POST /api/inventory/update` with `{"product_name": "milk", "quantity": 50}`
4. System updates SQLite `products.stock` table
5. Verify confirmation message shows new stock level
6. Take photo of receipt and attach to transaction log

**Guardrails:**
- Maximum single add: 500 units (prevents fat-finger errors)
- If larger, split into multiple adds
- Always require approval from Manager if supplier is new

### 1.2 Reducing Stock (Sales/Damage)

**When:** Items sold or damaged  
**System:** Use POS system or `/api/transactions/record` endpoint

**Steps:**
1. Customer transaction or damage report identifies quantity
2. Use natural language: "Sell 3 bread loaves"
   - OR use API: `POST /api/transactions/record` with customer_id and quantity
3. System checks: is stock sufficient?
   - If YES: deduct and log transaction
   - If NO: block sale and alert Manager
4. Update `customer_transactions.csv` immediately
5. Record reason: sale/damage/return/test

**Guardrails:**
- Cannot sell more than available stock
- All sales linked to customer_id for analytics
- Damage entries require Manager approval

---

## 2. Handling Negative Stock (Critical Issue)

**Root Cause:** Usually late database sync, duplicate transactions, or API retry failures.

### 2.1 Detection

**Signs:**
- Dashboard shows negative stock for a product
- API returns: `stock: -5`
- Alert email: "Negative Stock Detected"

### 2.2 Immediate Actions

**Within 5 minutes:**
1. DO NOT accept new sales for this product
2. Check timestamp of last sync job: `SELECT * FROM system_logs WHERE event='sync' ORDER BY created_at DESC LIMIT 1;`
3. Check for duplicate transactions: `SELECT transaction_id, COUNT(*) FROM sales GROUP BY transaction_id HAVING COUNT(*) > 1;`
4. If duplicates found, note the `transaction_id`

### 2.3 Root Cause Analysis

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Duplicate transactions | API retry without idempotency | Delete one duplicate entry, re-run reconciliation |
| Stock lower than expected | Late sync from POS | Run manual sync, compare timestamps |
| Intermittent negatives | Network timeout | Check API logs for 504/timeout errors |
| Bulk negatives across products | Database corruption | Restore from last backup, then reconcile |

### 2.4 Remediation Steps

**Step 1: Audit Trail**
```sql
-- Check all transactions for this product in last 24 hours
SELECT transaction_id, product_id, quantity, created_at 
FROM sales 
WHERE product_id = ? 
ORDER BY created_at DESC;

-- Compare against customer_transactions.csv
```

**Step 2: Reconciliation**
```python
# Run from terminal
python -m tools.customer_analytics rebuild_rfm
# This recomputes all aggregates from source of truth
```

**Step 3: Manual Fix (if needed)**
```sql
-- Only if audit confirms error
UPDATE products 
SET stock = (SELECT SUM(quantity) FROM inventory_log WHERE product_id = ?) 
WHERE id = ?;
```

**Step 4: Verification**
```bash
# Restart backend to clear any cached state
python run_backend.py
# Confirm stock is now positive in dashboard
```

### 2.5 Prevention

- Enable idempotency: use `transaction_id` in API calls, reject duplicates
- Add sync job validation: `count(transactions before) == count(transactions after)`
- Set up alerts: trigger if stock < 0 for ANY product
- Daily reconciliation cron: runs at 2 AM, auto-fixes small discrepancies

---

## 3. Daily Reconciliation

**When:** End of day (6 PM)  
**Owner:** Store Manager  
**Time:** ~15 minutes

**Steps:**

1. **Run automated reconciliation:**
   ```bash
   python tools/customer_analytics.py --reconcile-daily
   ```

2. **Review report:**
   - Check for discrepancies > 5 units
   - Flag any new negative stocks
   - Log any manual adjustments

3. **Physical spot check (sampling):**
   - Randomly pick 5 products
   - Count physical stock
   - Compare to system
   - If mismatch > 10%, escalate

4. **Approve and close day:**
   - Document any adjustments
   - Sign off on report
   - Archive to `/archive/reconciliation/{YYYY-MM-DD}.log`

**Report Location:** `Dashboard > Inventory > Daily Reconciliation Report`

---

## 4. Weekly Deep Reconciliation

**When:** Every Sunday 10 AM  
**Owner:** Operations Manager  
**Time:** ~1 hour

**Steps:**

1. **Full physical count:**
   - All products counted by 2 people (independent)
   - Results recorded in spreadsheet

2. **System pull:**
   ```bash
   python -c "from tools.inventory_tools import get_all_products; import json; \
   print(json.dumps([{'name': n, 'stock': s} for n, s in get_all_products()], indent=2))"
   ```

3. **Reconcile differences:**
   - Identify variances
   - For each variance > 2 units:
     - Root cause (missing transaction, damage, theft)
     - Corrective action
     - Who caused it (data-driven improvement)

4. **Adjust system to physical count:**
   - Only if difference cannot be explained
   - Document reason in audit trail
   - Update `products.stock` via API

5. **Store results:**
   - Save as `/archive/weekly_reconciliation/{YYYY-W##}.csv`
   - Trend analysis: identify high-variance products

---

## 5. Escalation & Approval

| Scenario | Approval Needed | Time Limit |
|----------|-----------------|-----------|
| Add > 200 units | Manager | 30 min |
| Negative stock | Operations Manager | 5 min |
| Variance > 10% in weekly count | Finance + Operations | 2 hours |
| Recurring product issues | Senior Manager | 24 hours |

---

## 6. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Sell 5 items" fails but stock shows 10 | Database not synced | Wait 30s, retry. If persists, restart backend |
| Negative stock appears suddenly | Duplicate transaction | Run reconciliation, check for transaction_id duplicates |
| Stock changes but no transaction record | API call without logging | Check API logs, manually add transaction entry |
| Forecast uses stale stock | Cache not cleared | Restart Streamlit: `Ctrl+C`, re-run `streamlit run frontend/dashboard.py` |

---

## 7. Tools & Commands

```bash
# Check current stock for a product
python -c "from tools.inventory_tools import get_stock; print(get_stock('milk'))"

# Run full reconciliation
python tools/customer_analytics.py --reconcile-full

# Check system health
curl http://localhost:8000/health

# View recent transactions
sqlite3 inventory.db "SELECT * FROM sales ORDER BY created_at DESC LIMIT 10;"
```

---

## 8. Contacts & Escalation

- **Daily Issues:** Store Manager (on-site)
- **Sync/API Issues:** Backend Dev Team (Slack: #backend-support)
- **Data Discrepancies:** Analytics Lead
- **Emergency (Negative Stock):** Operations Manager (on-call)
