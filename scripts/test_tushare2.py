"""Test Tushare API"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config.settings import settings

token = settings.tushare.token
import tushare as ts
pro = ts.pro_api(token)

print("Testing stock_basic...")
try:
    df = pro.stock_basic()
    print(f'stock_basic: {len(df)} rows, cols={list(df.columns)}')
except Exception as e:
    print(f'stock_basic FAILED: {e}')

print("Testing daily (latest)...")
try:
    df = pro.daily(trade_date='20260428')
    print(f'daily 20260428: {len(df)} rows')
except Exception as e:
    print(f'daily FAILED: {e}')

print("Testing daily (known date)...")
try:
    df = pro.daily(trade_date='20260427')
    print(f'daily 20260427: {len(df)} rows')
except Exception as e:
    print(f'daily FAILED: {e}')

print("Testing daily (20240102)...")
try:
    df = pro.daily(trade_date='20240102')
    print(f'daily 20240102: {len(df)} rows')
except Exception as e:
    print(f'daily FAILED: {e}')
