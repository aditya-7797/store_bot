from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FILE = DATA_DIR / "customer_transactions.csv"

if not FILE.exists():
    print("No customer_transactions.csv found")
    raise SystemExit(1)

print(f"Loading {FILE}")
df = pd.read_csv(FILE, dtype=str)
if df.empty:
    print("File empty")
    raise SystemExit(0)

# Ensure columns
expected = ["transaction_id","customer_id","product_id","quantity","purchase_date","price"]
for col in expected:
    if col not in df.columns:
        df[col] = ""

# compute max numeric transaction id
numeric_tx = pd.to_numeric(df["transaction_id"], errors="coerce")
max_tx = int(numeric_tx.max()) if not numeric_tx.isna().all() else 1000
next_tx = max_tx + 1

changed = 0
# Rows needing normalization: non-numeric transaction_id or starting with 'TX-'
mask_non_numeric = numeric_tx.isna()
for idx in df[mask_non_numeric].index:
    df.at[idx, "transaction_id"] = str(next_tx)
    next_tx += 1
    changed += 1

# Normalize purchase_date to YYYY-MM-DD if possible
for idx in df.index:
    try:
        dt = pd.to_datetime(df.at[idx, "purchase_date"], errors="coerce")
        if not pd.isna(dt):
            df.at[idx, "purchase_date"] = dt.strftime("%Y-%m-%d")
    except Exception:
        pass

# Clear price column to match historical blank prices
if "price" in df.columns:
    df["price"] = ""

# Save backup
backup = FILE.with_suffix('.bak')
FILE.rename(backup)
print(f"Backup written to {backup}")

# Write normalized file
df.to_csv(FILE, index=False)
print(f"Wrote normalized transactions to {FILE}. Rows changed: {changed}")
