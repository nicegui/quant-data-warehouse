import sys, time, math
import pandas as pd
import tushare as ts
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

TOKEN = "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185"
ts.set_token(TOKEN)
pro = ts.pro_api()

CONN = psycopg2.connect("host=localhost port=5432 dbname=quantdb user=quant password=quant_pass")
CONN.autocommit = False

LOG = "/tmp/pull_fc_express_v2.log"

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

# ===== CREATE TABLES (if not exist) =====
log("创建表...")
cur = CONN.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_forecast (
        ts_code VARCHAR(16) NOT NULL,
        ann_date TIMESTAMPTZ NOT NULL,
        end_date TIMESTAMPTZ NOT NULL,
        type VARCHAR(20),
        p_change_min DOUBLE PRECISION,
        p_change_max DOUBLE PRECISION,
        net_profit_min DOUBLE PRECISION,
        net_profit_max DOUBLE PRECISION,
        last_parent_net DOUBLE PRECISION,
        first_ann_date VARCHAR(20),
        summary TEXT,
        change_reason TEXT,
        update_flag VARCHAR(10)
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_express (
        ts_code VARCHAR(16) NOT NULL,
        ann_date TIMESTAMPTZ NOT NULL,
        end_date TIMESTAMPTZ NOT NULL,
        revenue DOUBLE PRECISION,
        operate_profit DOUBLE PRECISION,
        total_profit DOUBLE PRECISION,
        n_income DOUBLE PRECISION,
        total_assets DOUBLE PRECISION,
        total_hldr_eqy_exc_min_int DOUBLE PRECISION,
        diluted_eps DOUBLE PRECISION,
        diluted_roe DOUBLE PRECISION,
        yoy_net_profit DOUBLE PRECISION,
        bps DOUBLE PRECISION,
        open_net_assets DOUBLE PRECISION,
        open_bps DOUBLE PRECISION,
        perf_summary TEXT,
        update_flag VARCHAR(10)
    )
""")
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_forecast_pk ON raw_forecast (ts_code, end_date)")
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_express_pk ON raw_express (ts_code, end_date)")
CONN.commit()
log("表 OK")

# ===== QUARTERS =====
QUARTERS = []
for y in range(2001, 2027):
    for m in [3, 6, 9, 12]:
        if y == 2026 and m > 3:
            break
        last_day = 31 if m != 2 else 28
        QUARTERS.append(f"{y}{m:02d}{last_day}")

log(f"共 {len(QUARTERS)} 个季度")

# ===== PULL =====
for api_name, tbl in [("forecast_vip", "raw_forecast"), ("express_vip", "raw_express")]:
    log(f"{'='*50}")
    log(f"开始: {tbl} ({api_name})")
    total = 0
    cur2 = CONN.cursor()
    cur2.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}' ORDER BY ordinal_position")
    cols = [c[0] for c in cur2.fetchall()]
    log(f"  表列: {len(cols)}")
    
    for i, q in enumerate(QUARTERS):
        ok = False
        for attempt in range(3):
            try:
                df = getattr(pro, api_name)(end_date=q)
                if df is not None and len(df) > 0:
                    # Only keep columns that exist in table
                    df = df[[c for c in df.columns if c in cols]]
                    # Convert dates
                    for col in ['ann_date', 'end_date']:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                    # NaN -> None
                    rows = df.where(pd.notnull(df), None).values.tolist()
                    # INSERT ON CONFLICT DO NOTHING
                    cur = CONN.cursor()
                    execute_values(cur,
                        f'INSERT INTO {tbl} ({",".join(df.columns)}) VALUES %s ON CONFLICT (ts_code, end_date) DO NOTHING',
                        [tuple(r) for r in rows],
                        page_size=1000)
                    CONN.commit()
                    total += len(rows)
                    ok = True
                else:
                    ok = True  # No data for this quarter, that's fine
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(3)
                else:
                    log(f"  FAIL {q}: {str(e)[:100]}")
        
        if (i+1) % 15 == 0:
            log(f"  [{i+1}/{len(QUARTERS)}] {tbl}: {total} 行")
    
    log(f"  {tbl} 完成: {total} 行")

# Final verify
cur = CONN.cursor()
for tbl in ["raw_forecast", "raw_express"]:
    cur.execute(f"SELECT COUNT(*), COUNT(DISTINCT ts_code), MIN(end_date), MAX(end_date) FROM {tbl}")
    cnt, stocks, dmin, dmax = cur.fetchone()
    log(f"FINAL {tbl}: {cnt} 行 | {stocks} 只股 | {dmin} ~ {dmax}")
CONN.close()
log("DONE")
