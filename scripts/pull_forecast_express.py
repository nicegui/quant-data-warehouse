import sys, os, time
import pandas as pd
import tushare as ts
import psycopg2
from datetime import datetime
from sqlalchemy import create_engine, text

TOKEN = "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185"
ts.set_token(TOKEN)
pro = ts.pro_api()

DB = "postgresql://quant:quant_pass@localhost:5432/quantdb"
engine = create_engine(DB)

LOG = "/tmp/pull_forecast_express.log"

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

# ===== TABLE DEFINITIONS (exact API fields) =====
TABLES = {
    "raw_forecast": [
        ("ts_code", "VARCHAR(16) NOT NULL"),
        ("ann_date", "TIMESTAMPTZ NOT NULL"),
        ("end_date", "TIMESTAMPTZ NOT NULL"),
        ("type", "VARCHAR(20)"),
        ("p_change_min", "DOUBLE PRECISION"),
        ("p_change_max", "DOUBLE PRECISION"),
        ("net_profit_min", "DOUBLE PRECISION"),
        ("net_profit_max", "DOUBLE PRECISION"),
        ("last_parent_net", "DOUBLE PRECISION"),
        ("first_ann_date", "VARCHAR(20)"),
        ("summary", "TEXT"),
        ("change_reason", "TEXT"),
        ("update_flag", "VARCHAR(10)"),
    ],
    "raw_express": [
        ("ts_code", "VARCHAR(16) NOT NULL"),
        ("ann_date", "TIMESTAMPTZ NOT NULL"),
        ("end_date", "TIMESTAMPTZ NOT NULL"),
        ("revenue", "DOUBLE PRECISION"),
        ("operate_profit", "DOUBLE PRECISION"),
        ("total_profit", "DOUBLE PRECISION"),
        ("n_income", "DOUBLE PRECISION"),
        ("total_assets", "DOUBLE PRECISION"),
        ("total_hldr_eqy_exc_min_int", "DOUBLE PRECISION"),
        ("diluted_eps", "DOUBLE PRECISION"),
        ("diluted_roe", "DOUBLE PRECISION"),
        ("yoy_net_profit", "DOUBLE PRECISION"),
        ("bps", "DOUBLE PRECISION"),
        ("open_net_assets", "DOUBLE PRECISION"),
        ("open_bps", "DOUBLE PRECISION"),
        ("perf_summary", "TEXT"),
        ("update_flag", "VARCHAR(10)"),
    ],
}

APIS = {
    "raw_forecast": "forecast_vip",
    "raw_express": "express_vip",
}

# ===== CREATE TABLES =====
log("创建表...")
for tbl_name, cols in TABLES.items():
    col_defs = ", ".join(f'"{c[0]}" {c[1]}' for c in cols)
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {tbl_name} CASCADE"))
        conn.execute(text(f"CREATE TABLE {tbl_name} ({col_defs})"))
        conn.execute(text(f'CREATE UNIQUE INDEX IF NOT EXISTS "idx_{tbl_name}_pk" ON {tbl_name} (ts_code, end_date)'))
    log(f"  {tbl_name}: {len(cols)} 列 ✅")

# ===== PULL DATA (quarter by quarter) =====
QUARTERS = []
for y in range(2001, 2027):
    for q in [3, 6, 9, 12]:
        if y == 2026 and q > 3:
            break
        QUARTERS.append(f"{y}{q:02d}28" if q == 2 else f"{y}{q:02d}30" if q == 6 else f"{y}{q:02d}30" if q == 9 else f"{y}{q:02d}31")

log(f"共 {len(QUARTERS)} 个季度")

for tbl_name, cols in TABLES.items():
    api_name = APIS[tbl_name]
    log(f"\n=== 拉取 {tbl_name} ({api_name}) ===")
    total = 0
    
    for i, q in enumerate(QUARTERS):
        count = 0
        for attempt in range(3):
            try:
                df = getattr(pro, api_name)(end_date=q)
                if df is not None and len(df) > 0:
                    # Convert date fields
                    for col in ['ann_date', 'end_date']:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                    # Clean NaN
                    df = df.where(pd.notnull(df), None)
                    with engine.begin() as conn:
                        conn.execute(text(f"DELETE FROM {tbl_name} WHERE end_date = :q"), {"q": q})
                    df.to_sql(tbl_name, engine, if_exists='append', index=False)
                    count = len(df)
                    total += count
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                else:
                    log(f"  FAIL {q}: {e}")
        
        if (i+1) % 10 == 0:
            log(f"  进度 {i+1}/{len(QUARTERS)} | {tbl_name}: {total} 行")
    
    log(f"  {tbl_name} 完成: {total} 行 ✅")

log("\n=== 全部完成 ===")

# Verify
with engine.connect() as conn:
    for tbl in ["raw_forecast", "raw_express"]:
        r = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
        r2 = conn.execute(text(f"SELECT COUNT(DISTINCT ts_code) FROM {tbl}")).scalar()
        log(f"  {tbl}: {r} 行 | {r2} 只股")
