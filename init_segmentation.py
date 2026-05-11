#!/usr/bin/env python
"""
Initialize customer segmentation fix:
1. Patch build_product_price_map() to use fallback pricing
2. Seed product prices into the database
"""
import subprocess
import sys

print("=" * 60)
print("FIXING CUSTOMER SEGMENTATION DATA QUALITY")
print("=" * 60)

# Step 1: Patch the price map function
print("\n[1/2] Patching build_product_price_map()...")
try:
    result = subprocess.run([sys.executable, "patch_prices.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️  Warning: {result.stderr}")
except Exception as e:
    print(f"❌ Error: {e}")

# Step 2: Seed prices
print("\n[2/2] Seeding product prices...")
try:
    from tools.seed_prices import seed_product_prices
    seed_product_prices()
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ INITIALIZATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Restart the FastAPI backend: python backend/main.py")
print("2. Restart Streamlit: streamlit run frontend/dashboard.py")
print("3. Go to Customers page to see updated RFM/KMeans plots")
print("=" * 60)
