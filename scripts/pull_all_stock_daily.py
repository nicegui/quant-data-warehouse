"""续传拉取 A 股日线行情，从指定月份开始"""
import os, sys, time
from datetime import datetime, date

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

# 生成月份范围，从 1996-06 开始（之前已拉到 1996-05）
def month_ranges(start_year=1996, start_month=6, end_year=2026, end_month=4):
    ranges = []
    y, m = start_year, start_month
    while (y < end_year) or (y == end_year and m <= end_month):
        s = date(y, m, 1)
        e = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        ranges.append((s.strftime('%Y%m%d'), e.strftime('%Y%m%d'), f"{y}{m:02d}"))
        m += 1
        if m > 12:
            m = 1; y += 1
    return ranges

ranges = month_ranges()
total = len(ranges)
print(f"📅 续传 {total} 个月: {ranges[0][2]} → {ranges[-1][2]}")

cur.execute("SELECT count(*) FROM raw_stock_daily")
print(f"📊 当前行数: {cur.fetchone()[0]:,}")

INSERT_SQL = """
    INSERT INTO raw_stock_daily 
    (ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount)
    VALUES %s
    ON CONFLICT (ts_code, trade_date) DO NOTHING
"""

total_inserted = 0
total_errors = 0

for i, (start_str, end_str, label) in enumerate(ranges):
    try:
        df = pro.daily(start_date=start_str, end_date=end_str)
        if df is None or len(df) == 0:
            print(f"  [{i+1}/{total}] {label}: 无数据")
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

        execute_values(cur, INSERT_SQL, rows, page_size=1000)
        conn.commit()
        total_inserted += len(rows)
        print(f"  ✅ [{i+1}/{total}] {label}: +{len(rows)} 行 (累计 {total_inserted:,})")
        time.sleep(0.35)

    except Exception as e:
        conn.rollback()
        total_errors += 1
        print(f"  ❌ [{i+1}/{total}] {label}: {e}")
        time.sleep(2)

cur.close(); conn.close()
print(f"\n✅ 续传完成！新插入: {total_inserted:,}, 错误: {total_errors} 个月")
