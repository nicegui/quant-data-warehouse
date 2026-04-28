"""Pull broker_recommend + cyq_chips — single script, real execution."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tushare as ts
import pandas as pd
from sqlalchemy import create_engine, text

TOKEN = "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185"
ENGINE = create_engine("postgresql://quant:quant_pass@localhost:5432/quantdb")
ts.set_token(TOKEN)
pro = ts.pro_api()

def db_exec(sql):
    with ENGINE.begin() as conn:
        conn.execute(text(sql))

def bulk_insert(table, df, pk_cols):
    if df is None or len(df) == 0:
        return 0
    cols = list(df.columns)
    placeholders = ", ".join([f":{c}" for c in cols])
    col_list = ", ".join(cols)
    pk_clause = ", ".join(pk_cols)
    update_clause = ", ".join([f"{c}=EXCLUDED.{c}" for c in cols if c not in pk_cols])
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT ({pk_clause}) DO UPDATE SET {update_clause}"
    records = df.where(pd.notnull(df), None).to_dict('records')
    with ENGINE.begin() as conn:
        result = conn.execute(text(sql), records)
    return len(records)

# ============================================================
# 1. broker_recommend
# ============================================================
print("Creating raw_broker_recommend...", flush=True)
db_exec("DROP TABLE IF EXISTS raw_broker_recommend CASCADE")
db_exec("""
CREATE TABLE raw_broker_recommend (
    month       varchar(6),
    broker      varchar(200),
    ts_code     varchar(20),
    name        varchar(200),
    created_at  timestamp DEFAULT now()
)
""")
db_exec("CREATE UNIQUE INDEX ON raw_broker_recommend (month, broker, ts_code)")

print("Pulling broker_recommend...", flush=True)
total = 0
for year in range(2019, 2027):
    for month in range(1, 13):
        ym = f"{year}{month:02d}"
        for attempt in range(3):
            try:
                df = pro.broker_recommend(month=ym)
                if df is not None and len(df) > 0:
                    n = bulk_insert('raw_broker_recommend', df, ['month', 'broker', 'ts_code'])
                    total += n
                break
            except Exception as e:
                if '每分钟最多访问' in str(e):
                    time.sleep(60)
                else:
                    time.sleep(2)
        if total % 1000 == 0:
            print(f"  broker_recommend: {total} rows ({ym})", flush=True)
print(f"  broker_recommend DONE: {total} rows", flush=True)

# ============================================================
# 2. cyq_chips
# ============================================================
print("Creating raw_cyq_chips...", flush=True)
db_exec("DROP TABLE IF EXISTS raw_cyq_chips CASCADE")
db_exec("""
CREATE TABLE raw_cyq_chips (
    ts_code     varchar(20),
    trade_date  varchar(8),
    price       double precision,
    percent     double precision,
    created_at  timestamp DEFAULT now()
)
""")
db_exec("CREATE UNIQUE INDEX ON raw_cyq_chips (ts_code, trade_date, price)")

# Get active stocks
with ENGINE.begin() as conn:
    stocks = [r[0] for r in conn.execute(text(
        "SELECT ts_code FROM ref_stock_basic WHERE delist_date IS NULL"
    )).fetchall()]
print(f"  {len(stocks)} stocks to process", flush=True)

# Get recent trade dates
import datetime
dates = []
d = datetime.date(2020, 1, 1)
end = datetime.date(2026, 4, 27)
while d <= end:
    if d.weekday() < 5:  # Mon-Fri
        dates.append(d.strftime('%Y%m%d'))
    d += datetime.timedelta(days=1)
print(f"  ~{len(dates)} trade dates. Pulling latest year first...", flush=True)

# Only pull 2025-2026 for now (most relevant)
dates = [d for d in dates if d >= '20250101']
total2 = 0
proc = 0
for ts_code in stocks:
    for td in dates:
        for attempt in range(3):
            try:
                df = pro.cyq_chips(ts_code=ts_code, trade_date=td)
                if df is not None and len(df) > 0:
                    n = bulk_insert('raw_cyq_chips', df, ['ts_code', 'trade_date', 'price'])
                    total2 += n
                break
            except Exception as e:
                if '每分钟最多访问' in str(e):
                    time.sleep(65)
                elif '服务不可用' in str(e):
                    time.sleep(5)
                else:
                    time.sleep(1)
    proc += 1
    if proc % 100 == 0:
        print(f"  cyq_chips: {proc}/{len(stocks)} stocks, {total2} rows", flush=True)
print(f"  cyq_chips DONE: {total2} rows", flush=True)

print("\n=== ALL DONE ===", flush=True)
