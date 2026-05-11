import traceback
try:
    from tools.customer_analytics import customer_summary_payload
    payload = customer_summary_payload()
    print("SUCCESS: Payload loaded")
    print(f"Keys: {list(payload.keys())}")
    print(f"RFM shape: {payload['rfm'].shape if hasattr(payload.get('rfm'), 'shape') else 'N/A'}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
