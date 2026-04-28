"""全量拉取 A 股日线，按天拉取（每交易日返回全市场股票）"""
import os, sys, time
from datetime import datetime, timedelta, date

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                k, _, v = line.partition('=')
                os.environ[k.strip()] = v.strip()

import tushare as ts
import psycopg2
from psycopg2.extras import execute_values

conn = psycopg2.connect(host='localhost', port=5432, dbname='quantdb', user='quant', password='quant_pass')
cur = conn.cursor()

token = os.environ.get('TUSHARE_TOKEN', '')
ts.set_token(token)
pro = ts.pro_api()

# 获取交易日历，只拉交易日
cal = pro.trade_cal(start_date='19901201', end_date='20260430')
trading_days = sorted(cal[cal['is_open'] == 1]['cal_date'].tolist())
print(f"📅 共 {len(trading_days)} 个交易日")

# 检查已有的交易日
cur.execute("SELECT DISTINCT trade_date::text FROM raw_stock_daily")
existing = set(r[0] for r in cur.fetchall() if r[0])
print(f"📊 已有 {len(existing)} 个交易日的数据")

to_fetch = [d for d in trading_days if d not in existing]
print(f"🔍 需要拉取 {len(to_fetch)} 天")

INSERT_SQL = """
    INSERT INTO raw_stock_daily 
    (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount)
    VALUES %s
    ON CONFLICT (ts_code, trade_date) DO NOTHING
"""

total_inserted = 0
total_days = 0
total_errors = 0

# 分批提交，每 N 天一次
BATCH_COMMIT = 10

for i, day in enumerate(to_fetch):
    try:
        df = pro.daily(trade_date=day)
        if df is None or len(df) == 0:
            continue

        rows = []
        for _, r in df.iterrows():
            rows.append((
                r['ts_code'], r['trade_date'],
                float(r.get('open', 0)), float(r.get('high', 0)),
                float(r.get('low', 0)), float(r.get('close', 0)),
                float(r.get('pre_close', 0)), float(r.get('change', 0)),
                float(r.get('pct_chg', 0)), float(r.get('vol', 0)),
                float(r.get('amount', 0))
            ))

        execute_values(cur, INSERT_SQL, rows, page_size=2000)
        
        total_inserted += len(rows)
        total_days += 1

        if total_days % BATCH_COMMIT == 0:
            conn.commit()
            elapsed = time.time() - start_time if 'start_time' in dir() or True else 0

        print(f"  ✅ [{i+1}/{len(to_fetch)}] {day}: {len(rows)} 行 (累计 {total_inserted:,})")
        time.sleep(0.3)

    except Exception as e:
        conn.rollback()
        total_errors += 1
        print(f"  ❌ [{i+1}/{len(to_fetch)}] {day}: {e}")
        time.sleep(2)

conn.commit()
cur.execute("SELECT count(*) FROM raw_stock_daily")
final = cur.fetchone()[0]
cur.close()
conn.close()

print(f"\n{'='*60}")
print(f"✅ 完成！")
print(f"   拉取天数: {total_days}")
print(f"   新插入行: {total_inserted:,}")
print(f"   总行数:   {final:,}")
print(f"   错误天数: {total_errors}")
