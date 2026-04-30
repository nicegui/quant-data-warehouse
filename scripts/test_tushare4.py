"""Test Tushare with known-good dates"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tushare as ts
pro = ts.pro_api('fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185')

# Try known dates
for date in ['20240102', '20240301', '20250102']:
    print(f"Testing daily {date}...", flush=True)
    try:
        df = pro.daily(trade_date=date)
        print(f"  -> {len(df)} rows", flush=True)
        if len(df) > 0:
            print(f"  -> sample: {df.iloc[0].to_dict()}", flush=True)
            break
    except Exception as e:
        print(f"  -> FAILED: {e}", flush=True)

# Check token info
print("Testing token info...", flush=True)
try:
    df = pro.token_info()
    print(f"  -> {df}", flush=True)
except:
    print("  -> no token_info API", flush=True)
