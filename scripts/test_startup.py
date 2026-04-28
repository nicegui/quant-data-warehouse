"""Minimal startup test"""
import os, sys, time, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s %(message)s')
log = logging.getLogger('TEST')
print("PRINT: script started", flush=True)
log.info("log: script started")

# Read token
TOKEN = os.environ.get("TUSHARE_TOKEN", "")
if not TOKEN:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    print(f"Reading token from: {env_path}", flush=True)
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TUSHARE_TOKEN='):
                TOKEN = line.split('=', 1)[1].strip("'\"")
                break

print(f"Token: {TOKEN[:8]}...{TOKEN[-4:]}", flush=True)

import tushare as ts
ts.set_token(TOKEN)

from sqlalchemy import create_engine, text
DB_URL = "postgresql://quant:quant_pass@localhost:5432/quantdb"
engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=3, max_overflow=5)

with engine.connect() as conn:
    r = conn.execute(text("SELECT count(*) FROM ref_stock_basic"))
    print(f"DB: {r.scalar()} rows", flush=True)

# Test stock_basic API
pro = ts.pro_api()
df = pro.stock_basic(fields='ts_code,symbol,name')
print(f"API stock_basic: {len(df)} rows", flush=True)

# Test daily_basic
df = pro.daily_basic(trade_date='20240102')
print(f"API daily_basic 20240102: {len(df) if df is not None else 0} rows", flush=True)

print("ALL STARTUP CHECKS PASSED", flush=True)
