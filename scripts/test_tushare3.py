"""Minimal Tushare test"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tushare as ts
pro = ts.pro_api('fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185')

print(f"tushare version: {ts.__version__}", flush=True)
print(f"Python: {sys.version}", flush=True)

# Quick test - just one stock
print("Testing single stock daily...", flush=True)
t0 = time.time()
try:
    df = pro.daily(ts_code='000001.SZ', start_date='20260420', end_date='20260428')
    elapsed = time.time() - t0
    print(f'daily single stock ({elapsed:.1f}s): {len(df)} rows', flush=True)
    if len(df) > 0:
        print(df.head(2), flush=True)
except Exception as e:
    elapsed = time.time() - t0
    print(f'daily FAILED ({elapsed:.1f}s): {e}', flush=True)

# Try daily with trade_date
print("Testing daily by date...", flush=True)
t0 = time.time()
try:
    df = pro.daily(trade_date='20260428')
    elapsed = time.time() - t0
    print(f'daily 20260428 ({elapsed:.1f}s): {len(df)} rows', flush=True)
except Exception as e:
    elapsed = time.time() - t0
    print(f'daily 20260428 FAILED ({elapsed:.1f}s): {e}', flush=True)
