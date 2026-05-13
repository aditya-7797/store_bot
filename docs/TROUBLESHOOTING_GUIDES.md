# Troubleshooting Guides: Common Issues & Fixes

**Last Updated:** May 2026  
**Version:** 1.0

---

## Quick Diagnosis Flow

```
Issue Reported
    ↓
[Is it API/Backend?] → Go to Section 1
    ↓
[Is it Database?] → Go to Section 2
    ↓
[Is it Dashboard/UI?] → Go to Section 3
    ↓
[Is it Forecasting?] → Go to Section 4
    ↓
[Is it Sync/Integration?] → Go to Section 5
```

---

## Section 1: API & Backend Issues

### 1.1 "Cannot connect to backend"

**Symptom:** Dashboard shows "Connection refused" or "Failed to get response from AI agent"

**Check:**
```bash
# Is backend running?
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "database": "connected", "ai_agents": "active"}
```

**Fix:**
1. If no response, backend is down
2. Start backend: `python run_backend.py`
3. Wait 5-10 seconds for startup
4. Retry

**Prevention:**
- Add to startup script: auto-restart on crash

---

### 1.2 "Failed to get response from AI agent"

**Symptom:** Query submitted successfully, but AI Assistant shows error

**Check:**
```bash
# Test routing
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how many milk"}'

# Check logs
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

**Common Causes & Fixes:**

| Cause | Check | Fix |
|-------|-------|-----|
| Agent crashes | Check backend logs for exception | Restart backend, report to dev team |
| Invalid query | Query doesn't match any intent | Rephrase query using example templates |
| Missing data | RFM/forecast files not loaded | Ensure data files exist in `/data/` and root |
| Timeout | Query takes > 30 seconds | Simplify query, split into smaller asks |

---

### 1.3 "Stock update not working"

**Symptom:** "Add 10 milk" says success, but stock doesn't change

**Check:**
```bash
# Verify in database directly
sqlite3 inventory.db "SELECT * FROM products WHERE name='milk';"

# Check API logs for errors
tail -f /tmp/backend.log  # or check console output
```

**Fixes:**

1. **Not in database yet:**
   - Add product first: "Add milk to inventory"
   - Or use direct SQL: `INSERT INTO products (name, stock) VALUES ('milk', 0);`

2. **Name mismatch (critical):**
   - Product stored as "Milk" (capital M)
   - Query used "milk" (lowercase)
   - Fix: Use exact capitalization or make query case-insensitive
   - Workaround: `UPDATE products SET name=LOWER(name);` (normalize all names)

3. **Duplicate products:**
   - Run: `python tools/inventory_tools.py cleanup_duplicates()`
   - This merges "milk", "Milk", "MILK" into one entry

---

## Section 2: Database Issues

### 2.1 "Database locked" / "Cannot acquire lock"

**Symptom:** Operations fail with SQLite lock error

**Cause:** Multiple processes writing to database simultaneously

**Immediate Fix:**
```bash
# Stop backend
pkill -f "python run_backend.py"
pkill -f "streamlit run"

# Wait 10 seconds

# Restart backend
python run_backend.py

# Restart dashboard
streamlit run frontend/dashboard.py
```

**Permanent Fix:**
- Use connection pooling (add to `backend/config.py`)
- Or upgrade to PostgreSQL for concurrent access

---

### 2.2 "Data corruption / inconsistent state"

**Symptom:** Queries return garbage, negative stocks everywhere, calculations wrong

**Diagnosis:**
```bash
# Check database integrity
sqlite3 inventory.db "PRAGMA integrity_check;"
# Response: either "ok" or list of errors

# Check transaction log for anomalies
sqlite3 inventory.db "SELECT COUNT(*) as duplicates FROM (SELECT transaction_id FROM sales GROUP BY transaction_id HAVING COUNT(*) > 1);"
```

**Recovery:**

1. **Automatic (fast):**
   ```bash
   python tools/customer_analytics.py --rebuild-rfm
   ```

2. **Manual (if above fails):**
   ```bash
   # Backup current database
   cp inventory.db inventory.db.backup
   
   # Drop and rebuild tables
   python initialize_db.py  # Re-creates schema
   
   # Restore from backup (carefully)
   # or re-seed from data CSVs
   python seed.py
   ```

3. **Last resort:**
   - Restore from last known-good backup (if available)
   - Manually re-enter critical data from transaction logs

---

### 2.3 "Transactions not appearing in analytics"

**Symptom:** Made sales, but RFM and forecasts don't update

**Check:**
```bash
# Are transactions in database?
sqlite3 inventory.db "SELECT COUNT(*) FROM sales;"

# Are they appearing in CSV?
wc -l data/customer_transactions.csv

# Check if values are NULL
sqlite3 inventory.db "SELECT * FROM sales WHERE product_id IS NULL OR quantity IS NULL LIMIT 5;"
```

**Fixes:**

1. **Transactions incomplete:**
   - Ensure `customer_id`, `product_id`, `quantity` are not NULL
   - Re-record transaction with all fields

2. **CSV out of sync:**
   ```bash
   # Force sync
   python -c "from tools.customer_analytics import append_customer_transaction; \
   append_customer_transaction({'transaction_id': 9999, 'customer_id': 1, 'product_id': 1, 'quantity': 5})"
   ```

3. **Cache stale:**
   - Restart Streamlit: `Ctrl+C`, then `streamlit run frontend/dashboard.py`

---

## Section 3: Dashboard & UI Issues

### 3.1 "Dashboard page loads but no data shows"

**Symptom:** All charts/tables are empty or show "No data available"

**Check:**
```bash
# Is data loading in background?
curl http://localhost:8000/api/inventory/products | head -20

# Check Streamlit logs in console
# Look for errors like "KeyError", "AttributeError"
```

**Fixes:**

1. **API not responding:**
   - Verify backend is running (Section 1.1)
   - Check API health: `curl http://localhost:8000/health`

2. **Data files missing:**
   ```bash
   # Check required files
   ls -la data/  # Should have CSV files
   ls -la *.csv  # Root-level CSVs
   ```
   - If missing, restore from backup or re-seed

3. **Cache issue:**
   - Hard refresh: `Ctrl+Shift+R` (clear browser cache)
   - Restart Streamlit

### 3.2 "Charts render but look wrong"

**Symptom:** Axes labels wrong, data points out of range, colors weird

**Cause:** Usually data type mismatch or NaN values

**Fix:**
```bash
# Inspect raw data
curl http://localhost:8000/api/customers/summary | python -m json.tool | head -50

# If NaN or null: check compute function
# Example: rfm calculation might have division by zero
```

**Workaround:**
- Restart dashboard to clear any cached computations
- Manually verify a few data points in database

---

### 3.3 "Chat history disappears after refresh"

**Symptom:** AI Assistant chat clears when page reloads

**Cause:** Streamlit session state is not persisted

**Expected Behavior:** This is normal for now (stateless session).

**Workaround:**
- Save important conversations manually
- Or wait for database-backed chat history (future feature)

---

## Section 4: Forecasting Issues

### 4.1 "Forecast seems completely wrong"

**Symptom:** Predicted values are way off (e.g., predicts 10 units when always 100+)

**Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Insufficient history | < 30 days of data | Wait for more data, use rule-based forecast |
| Structural break | Recent promotion/stockout | Manually adjust or use different model |
| Seasonality | Repeating pattern not captured | Run Prophet with `yearly_seasonality=True` |
| Outliers | Single huge sale skews model | Remove outlier, retrain |

**Steps:**

1. Check data:
   ```bash
   sqlite3 inventory.db "SELECT date(created_at), COUNT(*) FROM sales GROUP BY date(created_at) ORDER BY date DESC LIMIT 30;"
   ```

2. Run forecast with debug:
   ```bash
   python product_wise_prophet_forecasting.py --verbose
   ```

3. Inspect model fit:
   - Check plot output for obvious issues (trend reversed, huge confidence bounds)
   - If bad, consider external factors

---

### 4.2 "Forecast not updating"

**Symptom:** Same forecast result despite new sales data

**Check:**
```bash
# When was forecast last run?
ls -la product_wise_prophet_forecast_next_30_days.csv
stat product_wise_prophet_forecast_next_30_days.csv  # Check timestamp

# Is new sales data in database?
sqlite3 inventory.db "SELECT MAX(created_at) FROM sales;"
```

**Fixes:**

1. **Forecast is stale:**
   ```bash
   python product_wise_prophet_forecasting.py
   ```

2. **Set up scheduled forecast:**
   - Add cron job: `0 2 * * * python product_wise_prophet_forecasting.py` (runs daily at 2 AM)

---

## Section 5: Sync & Integration Issues

### 5.1 "Negative stock suddenly appears"

**See:** SOP_INVENTORY_RECONCILIATION.md, Section 2

**Quick fix:**
```bash
python tools/customer_analytics.py --reconcile-full
```

---

### 5.2 "Data is duplicated / not in sync"

**Symptom:** Same transaction appears twice, or CSV and database have different counts

**Diagnosis:**
```bash
# Check for duplicate transactions
sqlite3 inventory.db "SELECT transaction_id, COUNT(*) as cnt FROM sales GROUP BY transaction_id HAVING cnt > 1;"

# Compare totals
echo "Sales DB:" && sqlite3 inventory.db "SELECT COUNT(*) FROM sales;" && \
echo "Customer CSV:" && wc -l data/customer_transactions.csv
```

**Fixes:**

1. **Duplicate in DB:**
   ```bash
   # Remove duplicates (keep first occurrence)
   sqlite3 inventory.db "DELETE FROM sales WHERE rowid NOT IN (SELECT MIN(rowid) FROM sales GROUP BY transaction_id);"
   ```

2. **Sync CSV to DB:**
   ```bash
   python tools/customer_analytics.py --sync-csv-to-db
   ```

---

### 5.3 "RFM/Customer segmentation not updating"

**Symptom:** Customer segments stuck at old values, new customers not appearing

**Fix:**
```bash
python tools/customer_analytics.py --rebuild-rfm
# or
python -c "from tools.customer_analytics import customer_summary_payload; print(customer_summary_payload())"
```

**Prevention:**
- Schedule daily rebuild: `0 3 * * * python tools/customer_analytics.py --rebuild-rfm`

---

## Emergency Restart Procedure

**Use when:** Multiple issues, unclear root cause

```bash
# Stop everything
pkill -f "python"
pkill -f "streamlit"

# Wait
sleep 5

# Clear cache
rm -rf __pycache__ .streamlit/

# Rebuild database (preserve data)
python tools/customer_analytics.py --rebuild-rfm

# Restart backend
python run_backend.py &

# Wait for backend to start
sleep 10

# Restart dashboard
streamlit run frontend/dashboard.py
```

---

## When to Escalate

| Issue | Self-Fix Possible | Escalate To |
|-------|------------------|------------|
| Stock mismatch < 10 units | Yes | Manager after documenting |
| API returns 500 error | Maybe (restart) | Backend Dev |
| Database locked > 5 min | No | Database Admin |
| Data corruption detected | No | Senior Dev + Backup Admin |
| Forecast consistently wrong | No | Data Science Lead |
| Unknown error in logs | No | Backend Dev (with logs) |

---

## Useful Commands Reference

```bash
# Health checks
curl http://localhost:8000/health

# View current stock
sqlite3 inventory.db "SELECT name, stock FROM products ORDER BY stock DESC;"

# Recent sales
sqlite3 inventory.db "SELECT * FROM sales ORDER BY created_at DESC LIMIT 20;"

# Rebuild all analytics
python tools/customer_analytics.py --rebuild-rfm

# Check for sync issues
python -c "from tools.customer_analytics import load_sales_history; print(load_sales_history().shape)"

# Run reconciliation
python tools/customer_analytics.py --reconcile-full
```

---

## Still Stuck?

1. **Check logs:**
   - Backend console: look for red errors
   - Streamlit console: look for "Traceback"
   - Database: `sqlite3 inventory.db "SELECT * FROM sqlite_master;"`

2. **Google the error message** (seriously, copy the full error)

3. **Ask on Slack:** #support with:
   - Exact error message
   - What you were trying to do
   - What you see vs. what you expected
   - OS and Python version

4. **Escalate:** Attach latest logs (`backend.log`, `/tmp/streamlit.log`)
