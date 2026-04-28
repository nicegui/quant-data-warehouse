"""Test direct insert into various tables"""
import os, sys, time
TOKEN = os.environ.get("TUSHARE_TOKEN", "")
if not TOKEN:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TUSHARE_TOKEN='):
                TOKEN = line.split('=', 1)[1].strip("'\"")
                break

import tushare as ts
ts.set_token(TOKEN)
pro = ts.pro_api()

from sqlalchemy import create_engine, text
DB_URL = "postgresql://quant:quant_pass@localhost:5432/quantdb"
engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=3)

print("Test 1: Direct SQL INSERT into raw_daily_basic")
with engine.begin() as conn:
    try:
        conn.execute(text("""
            INSERT INTO raw_daily_basic (ts_code, trade_date, close, turnover_rate, pe, total_mv)
            VALUES ('000001.SZ', '20240102', 10.5, 0.5, 20.0, 100000000)
            ON CONFLICT (ts_code, trade_date) DO NOTHING
        """))
        print("  ✅ INSERT OK")
    except Exception as e:
        print(f"  ❌ {e}")

print("\nTest 2: Check column types")
with engine.connect() as conn:
    r = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name='raw_daily_basic'
        ORDER BY ordinal_position
    """))
    for row in r:
        print(f"  {row[0]:20s} {row[1]:20s} nullable={row[2]}")

print("\nTest 3: Check table owner")
with engine.connect() as conn:
    r = conn.execute(text("""
        SELECT tableowner FROM pg_tables WHERE tablename = 'raw_daily_basic'
    """))
    print(f"  Owner: {r.scalar()}")

print("\nTest 4: try inserting data from API")
df = pro.daily_basic(trade_date='20240102')
print(f"  API returned {len(df)} rows")
print(f"  Columns: {list(df.columns)[:8]}...")

# Try insert
df_small = df.head(3)
n = 0
for _, row in df_small.iterrows():
    cols = []
    vals = []
    for c in ['ts_code', 'trade_date', 'close', 'turnover_rate', 'pe', 'total_mv']:
        if c in row and row[c] is not None:
            cols.append(f'"{c}"')
            v = row[c]
            if isinstance(v, str) and len(v) == 8 and v.isdigit():
                vals.append(f"'{v[:4]}-{v[4:6]}-{v[6:8]}'::timestamptz")
            elif isinstance(v, str):
                vals.append(f"'{v}'")
            else:
                vals.append(str(v))
    sql = f'INSERT INTO raw_daily_basic ({", ".join(cols)}) VALUES ({", ".join(vals)}) ON CONFLICT DO NOTHING'
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        n += 1
    except Exception as e:
        print(f"  ❌ row insert: {e}")
        print(f"     SQL: {sql[:200]}...")
print(f"  Inserted {n} rows")

print("\nDONE")
