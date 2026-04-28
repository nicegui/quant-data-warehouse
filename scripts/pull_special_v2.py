#!/usr/bin/env python3
"""拉取 Tushare 特色数据: report_rc, cyq_perf, cyq_chips, broker_recommend
简洁版：直连 psycopg2，有错就打印"""
import sys, os, time
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import execute_values

# Token
env_path = os.path.expanduser('~/quant-data-warehouse/.env')
token = None
with open(env_path) as f:
    for line in f:
        if line.startswith('TUSHARE_TOKEN='):
            token = line.strip().split('=', 1)[1].strip()
            break
ts.set_token(token)
pro = ts.pro_api()

def db():
    return psycopg2.connect("host=localhost port=5432 dbname=quantdb user=quant password=quant_pass")

def do_insert(cur, table, df, pk_cols):
    """Direct INSERT with ON CONFLICT, returns count"""
    if df is None or df.empty:
        return 0
    # Get table columns
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' ORDER BY ordinal_position")
    table_cols = [r[0] for r in cur.fetchall()]
    common = [c for c in df.columns if c in table_cols]
    if not common:
        return 0
    
    rows = []
    for _, r in df.iterrows():
        rows.append(tuple(None if pd.isna(r[c]) else r[c] for c in common))
    
    sql = f"INSERT INTO {table} ({', '.join(common)}) VALUES %s ON CONFLICT ({', '.join(pk_cols)}) DO NOTHING"
    execute_values(cur, sql, rows, page_size=1000)
    return len(rows)

def ensure_table(table, df, pk_cols):
    """Create table if needed"""
    conn = db()
    cur = conn.cursor()
    cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='{table}')")
    exists = cur.fetchone()[0]
    
    if not exists:
        col_defs = []
        for c in df.columns:
            if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
                t = 'text'
            elif pd.api.types.is_integer_dtype(df[c]):
                t = 'bigint'
            elif pd.api.types.is_float_dtype(df[c]):
                t = 'float'
            else:
                t = 'text'
            col_defs.append(f'"{c}" {t}')
        cur.execute(f"CREATE TABLE {table} ({', '.join(col_defs)})")
        if pk_cols:
            cur.execute(f"ALTER TABLE {table} ADD CONSTRAINT uq_{table} UNIQUE ({', '.join(pk_cols)})")
        conn.commit()
        print(f"[{table}] CREATED: {len(col_defs)} cols")
    cur.close()
    conn.close()
    return exists

total_counts = {}

# ============================================================
# 1. report_rc
# ============================================================
print("\n1/4: report_rc")
df_sample = pro.report_rc(start_date='20260401', end_date='20260424', limit=3)
ensure_table('raw_report_rc', df_sample, ['ts_code', 'report_date', 'org_name'])

total = 0
conn = db()
for year in range(2010, 2027):
    for q in [('0101','0331'), ('0401','0630'), ('0701','0930'), ('1001','1231')]:
        sd, ed = q
        if year == 2026 and int(sd[:2]) > 4:
            break
        try:
            df = pro.report_rc(start_date=f'{year}{sd}', end_date=f'{year}{ed}', limit=5000)
        except:
            continue
        if df is None or df.empty:
            continue
        cur = conn.cursor()
        try:
            do_insert(cur, 'raw_report_rc', df, ['ts_code', 'report_date', 'org_name'])
            conn.commit()
        except Exception as e:
            conn.rollback()
            if year >= 2020:
                print(f"  [{year}{sd}] ERR: {e}")
        cur.close()
        time.sleep(0.3)
    if year % 3 == 0:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_report_rc")
        total = cur.fetchone()[0]
        cur.close()
        print(f"  [{year}] total: {total}")
conn.close()

cur = db().cursor()
cur.execute("SELECT COUNT(*) FROM raw_report_rc")
total_counts['report_rc'] = cur.fetchone()[0]
cur.close()
print(f"[report_rc] DONE: {total_counts['report_rc']}")

# ============================================================
# 2-3. cyq_perf + cyq_chips  
# ============================================================
# Get stock list
conn = db()
stocks = pd.read_sql("SELECT ts_code FROM ref_stock_basic WHERE delist_date IS NULL", conn)
conn.close()
stock_codes = stocks['ts_code'].tolist()
print(f"\nStock list: {len(stock_codes)} stocks")

for api_name, table_name, pk in [
    ('cyq_perf', 'raw_cyq_perf', ['ts_code', 'trade_date']),
    ('cyq_chips', 'raw_cyq_chips', ['ts_code', 'trade_date', 'price']),
]:
    print(f"\n{'='*40}\n{api_name}")
    fn = getattr(pro, api_name)
    df_sample = fn(ts_code='000001.SZ', start_date='20260401', end_date='20260424', limit=3) if api_name == 'cyq_chips' else fn(ts_code='000001.SZ', start_date='20260401', end_date='20260424')
    ensure_table(table_name, df_sample, pk)
    
    total = 0
    conn = db()
    for i, code in enumerate(stock_codes):
        try:
            if api_name == 'cyq_chips':
                df = fn(ts_code=code, start_date='20250401', end_date='20260427')
            else:
                df = fn(ts_code=code, start_date='20250401', end_date='20260427')
        except:
            continue
        if df is None or df.empty:
            continue
        cur = conn.cursor()
        try:
            do_insert(cur, table_name, df, pk)
            conn.commit()
        except Exception as e:
            conn.rollback()
            if i < 10:
                print(f"  [{code}] ERR: {e}")
        cur.close()
        if (i+1) % 500 == 0:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cur.fetchone()[0]
            cur.close()
            print(f"  [{i+1}/{len(stock_codes)}] {total}")
        time.sleep(0.25)
    
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_counts[api_name] = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"[{api_name}] DONE: {total_counts[api_name]}")

# ============================================================
# 4. broker_recommend
# ============================================================
print(f"\n{'='*40}\nbroker_recommend")
df_sample = pro.broker_recommend(month='202604')
ensure_table('raw_broker_recommend', df_sample, ['month', 'broker', 'ts_code'])

total = 0
conn = db()
for year in range(2010, 2027):
    for month in range(1, 13):
        m = f'{year}{month:02d}'
        if m > '202604':
            break
        try:
            df = pro.broker_recommend(month=m)
        except:
            continue
        if df is None or df.empty:
            continue
        cur = conn.cursor()
        try:
            do_insert(cur, 'raw_broker_recommend', df, ['month', 'broker', 'ts_code'])
            conn.commit()
        except Exception as e:
            conn.rollback()
        cur.close()
        time.sleep(0.3)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM raw_broker_recommend")
    total = cur.fetchone()[0]
    cur.close()
    print(f"  [{year}] total: {total}")
conn.close()

cur = db().cursor()
cur.execute("SELECT COUNT(*) FROM raw_broker_recommend")
total_counts['broker_recommend'] = cur.fetchone()[0]
cur.close()

print(f"\n{'='*60}")
for k, v in total_counts.items():
    print(f"  {k}: {v}")
print(f"{'='*60}")
