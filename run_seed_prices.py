#!/usr/bin/env python
"""Initialize segmentation fix: seed product prices into database."""

if __name__ == "__main__":
    try:
        from tools.seed_prices import seed_product_prices
        seed_product_prices()
        print("\n✅ Prices seeded successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
