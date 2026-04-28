"""
Pull raw_hsgt_top10 only — all missing dates with rate limiting.
"""
import sys, time, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db.engine import get_engine
from sqlalchemy import text
import tushare as ts
import pandas as pd

# Read token from .env
env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
token = None
with open(env_file) as f:
    for line in f:
        if line.startswith('TUSHARE_TOKEN='):
            token = line.split('=', 1)[1].strip().strip('"').strip("'")
            break
if not token:
    print("ERROR: No TUSHARE_TOKEN found in .env", flush=True)
    sys.exit(1)
pro = ts.pro_api(token)

engine = get_engine()

# Get existing dates
with engine.connect() as conn:
    r = conn.execute(text("SELECT DISTINCT trade_date::date FROM raw_hsgt_top10 ORDER BY 1"))
    existing = {row[0] for row in r.fetchall()}
    print(f"Existing hsgt dates: {len(existing)}", flush=True)

# Get trade calendar
with engine.connect() as conn:
    r = conn.execute(text("SELECT cal_date FROM ref_trade_cal WHERE is_open=true AND cal_date >= '2014-11-17' AND cal_date <= '2026-04-27' ORDER BY cal_date"))
    all_dates = [row[0] for row in r.fetchall()]
    print(f"Total trade dates: {len(all_dates)}", flush=True)

missing = [d for d in all_dates if d not in existing]
print(f"Missing dates: {len(missing)}", flush=True)

if not missing:
    print("HSGT already complete!", flush=True)
    sys.exit(0)

total = len(missing)
rate_limit = 150
interval = 60.0 / rate_limit
inserted = 0
skipped = 0

cols = ['trade_date', 'ts_code', 'name', 'close', 'change', 'rank', 'market_type',
        'amount', 'net_amount', 'buy', 'sell']

for i, d in enumerate(missing):
    date_str = d.strftime('%Y%m%d')
    success = False
    for attempt in range(3):
        try:
            df = pro.hsgt_top10(trade_date=date_str)
            if df is not None and len(df) > 0:
                df['trade_date'] = pd.Timestamp(d)
                df = df[[c for c in cols if c in df.columns]]
                with engine.begin() as conn:
                    for _, row in df.iterrows():
                        vals = {c: (None if pd.isna(row.get(c)) else row.get(c)) for c in cols if c in df.columns}
                        placeholders = ', '.join(f':{c}' for c in vals)
                        col_names = ', '.join(vals.keys())
                        conn.execute(
                            text(f"INSERT INTO raw_hsgt_top10 ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"),
                            vals
                        )
                inserted += len(df)
            success = True
            break
        except Exception as e:
            err = str(e)[:120]
            if '200' in err or 'limit' in err or '访问次数' in err or '次数' in err:
                time.sleep(10 * (attempt + 1))
            else:
                break

    if not success:
        skipped += 1

    if i % 200 == 0:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT count(*) FROM raw_hsgt_top10"))
            total_rows = r.scalar()
        print(f"[{d.strftime('%Y-%m-%d')}] progress: {i}/{total} days | {total_rows} rows | +{inserted} new | {skipped} skipped", flush=True)

    time.sleep(interval)

with engine.connect() as conn:
    r = conn.execute(text("SELECT count(*), min(trade_date), max(trade_date) FROM raw_hsgt_top10"))
    cnt, mn, mx = r.fetchone()
    print(f"\nDONE! hsgt_top10: {cnt} rows | {mn} ~ {mx}", flush=True)
