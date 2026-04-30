"""Debug Tushare API responses"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tushare as ts

# Direct API call to see raw response
pro = ts.pro_api('fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185')

# Try to get the underlying HTTP client
print(f"tushare version: {ts.__version__}", flush=True)

# Check what the token level is
try:
    result = pro.query('token_info')
    print(f"token_info result: {result}", flush=True)
except Exception as e:
    print(f"token_info err: {e}", flush=True)

# Try with explicit error checking
try:
    df = pro.daily(trade_date='20240102')
    print(f"daily 20240102 type: {type(df)}, empty: {df.empty}, len: {len(df)}", flush=True)
    if hasattr(df, 'error'):
        print(f"  error field: {df.error}", flush=True)
    if not df.empty:
        print(df.head(2).to_dict(), flush=True)
except Exception as e:
    print(f"daily 20240102: {type(e).__name__}: {e}", flush=True)

# Try index_daily instead (might be cheaper/free)
try:
    df = pro.index_daily(trade_date='20240102')
    print(f"index_daily 20240102: {len(df)} rows", flush=True)
except Exception as e:
    print(f"index_daily: {e}", flush=True)

# Try trade_cal
try:
    df = pro.trade_cal(start_date='20260425', end_date='20260430')
    print(f"trade_cal April 25-30: {len(df)} rows", flush=True)
    if not df.empty:
        print(df.to_dict(), flush=True)
except Exception as e:
    print(f"trade_cal: {e}", flush=True)

# Try daily with no params (latest)
try:
    df = pro.daily()
    print(f"daily (no params): {len(df)} rows", flush=True)
    if not df.empty:
        print(df.head(2).to_dict(), flush=True)
except Exception as e:
    print(f"daily (no params): {e}", flush=True)
