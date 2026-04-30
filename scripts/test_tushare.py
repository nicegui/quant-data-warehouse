"""Minimal Tushare connectivity test"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config.settings import settings

# Load token
token = settings.tushare.token
print(f'Token loaded: {token[:8]}...{token[-4:]}')

import tushare as ts
ts.set_token(token)
pro = ts.pro_api()

# Simple API call
df = pro.stock_basic(fields='ts_code,symbol,name', limit=5)
print(f'stock_basic rows: {len(df)}')
print(df.head(3))
print('TUSHARE OK')
