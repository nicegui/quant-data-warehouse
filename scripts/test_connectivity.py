"""Quick connectivity test"""
import os, sys
TOKEN = os.environ.get('TUSHARE_TOKEN', '')
if not TOKEN:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TUSHARE_TOKEN='):
                TOKEN = line.split('=', 1)[1].strip("'\"")
                break
print(f'Token: {TOKEN[:8]}...{TOKEN[-4:]}')

import tushare as ts
ts.set_token(TOKEN)
pro = ts.pro_api()

df = pro.stock_basic(fields='ts_code,symbol,name')
print(f'stock_basic: {len(df)} rows')

df2 = pro.daily_basic(trade_date='20240102')
print(f'daily_basic 20240102: {len(df2) if df2 is not None else 0} rows')

df3 = pro.concept_detail(id='TS000001')
print(f'concept_detail TS000001: {len(df3) if df3 is not None else 0} rows')

# Test DB
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb")
r = engine.execute(text("SELECT count(*) FROM ref_stock_basic"))
print(f'DB ref_stock_basic: {r.scalar()} rows')
engine.dispose()

print('ALL CHECKS PASSED')
