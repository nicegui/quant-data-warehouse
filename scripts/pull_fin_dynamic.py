#!/usr/bin/env python3
"""
一次性任务：动态获取 Tushare API 字段 → 建表 → 按季度拉全量
字段完全对齐 API，不硬编码 fields=
"""
import os, sys, time
from datetime import date
import pandas as pd
import tushare as ts
from sqlalchemy import create_engine, text

# ── Config ──
TOKEN = None
with open('/Users/admin/quant-data-warehouse/.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('TUSHARE_TOKEN='):
            TOKEN = line.split('=', 1)[1].strip().strip("'\"")
            break

if not TOKEN:
    print("ERROR: no token"); sys.exit(1)

QDB = f"postgresql://{os.environ.get('POSTGRES_USER','quant')}:{os.environ.get('POSTGRES_PASSWORD','quant_pass')}@{os.environ.get('POSTGRES_HOST','localhost')}:{os.environ.get('POSTGRES_PORT','5432')}/{os.environ.get('POSTGRES_DB','quantdb')}"
pro = ts.pro_api(TOKEN)
engine = create_engine(QDB, pool_pre_ping=True, pool_size=5)

print(f"Token: {TOKEN[:8]}...")

# ── API → 表名映射 ──
APIS = [
    ('raw_fin_income',     pro.income_vip),
    ('raw_fin_balance',    pro.balancesheet_vip),
    ('raw_fin_cashflow',   pro.cashflow_vip),
    ('raw_fin_indicators', pro.fina_indicator_vip),
]

# ── Step 1: 获取各 API 真实字段 ──
print("\n=== 获取 API 字段 ===")
API_FIELDS = {}
for tbl_name, api in APIS:
    try:
        df = api(ts_code='000001.SZ', end_date='20241231')
        fields = list(df.columns)
        API_FIELDS[tbl_name] = fields
        print(f"  {tbl_name}: {len(fields)} fields")
    except Exception as e:
        print(f"  {tbl_name}: ERROR {e}")

# ── Step 2: DROP & CREATE ──
print("\n=== 建表（完全对齐 API 字段）===")
for tbl_name, api in APIS:
    fields = API_FIELDS[tbl_name]
    
    # Build column definitions
    col_defs = []
    for col in fields:
        col_lower = col.lower()
        if col_lower in ('ts_code', 'end_date', 'ann_date', 'f_ann_date', 
                         'report_type', 'comp_type', 'end_type', 'update_flag'):
            col_defs.append(f'"{col}" VARCHAR(32)')
        elif 'date' in col_lower or 'month' in col_lower or 'quarter' in col_lower:
            col_defs.append(f'"{col}" VARCHAR(16)')
        else:
            col_defs.append(f'"{col}" DOUBLE PRECISION')
    
    with engine.begin() as conn:
        conn.execute(text(f'CREATE TABLE IF NOT EXISTS "{tbl_name}" ({", ".join(col_defs)})'))
        try:
            conn.execute(text(f'ALTER TABLE "{tbl_name}" ADD UNIQUE ("ts_code", "end_date")'))
        except Exception:
            pass  # constraint already exists
    print(f"  {tbl_name}: {len(fields)} cols, UNIQUE(ts_code,end_date) ✅")

# ── Step 3: 按季度拉取 ──
print("\n=== 拉取数据 ===")

# 生成季度列表（最近25个季度）
quarters = []
today = date.today()
for year in range(today.year, 1989, -1):
    for q, ed in [(4, '1231'), (3, '0930'), (2, '0630'), (1, '0331')]:
        if year == today.year and q > ((today.month - 1) // 3 + 1):
            continue
        quarters.append(f'{year}{ed}')
    if len(quarters) >= 25:
        break
quarters = quarters[:25]
print(f"  季度: {quarters[0]} → {quarters[-1]} ({len(quarters)} 季)")

for tbl_name, api in APIS:
    print(f"\n--- {tbl_name} ---")
    total = 0
    for qi, end_date in enumerate(quarters):
        ok = False
        for attempt in range(5):
            try:
                df = api(end_date=end_date)
                if df is None or df.empty:
                    print(f"  {end_date}: 无数据")
                    ok = True
                    break
                
                # 批量 INSERT ON CONFLICT DO NOTHING
                records = df.to_dict('records')
                cols = list(df.columns)
                ph = ', '.join([f':{c}' for c in cols])
                qc = ', '.join([f'"{c}"' for c in cols])
                sql = f'INSERT INTO "{tbl_name}" ({qc}) VALUES ({ph}) ON CONFLICT ("ts_code", "end_date") DO NOTHING'
                
                written = 0
                with engine.begin() as conn:
                    for i in range(0, len(records), 500):
                        batch = records[i:i+500]
                        result = conn.execute(text(sql), batch)
                        written += result.rowcount
                
                total += written
                print(f"  [{qi+1}/{len(quarters)}] {end_date}: +{written} (累计 {total})")
                ok = True
                break
            except Exception as e:
                msg = str(e)
                if '次数' in msg or 'limit' in msg.lower():
                    w = min(30*(attempt+1), 90)
                    print(f"  限流,等{w}s..."); time.sleep(w)
                else:
                    if attempt < 4:
                        print(f"  重试{attempt+1}/5: {msg[:80]}")
                        time.sleep(5)
                    else:
                        print(f"  ❌ {end_date}: {msg[:80]}")
        if ok:
            time.sleep(0.35)

# ── 最终统计 ──
print("\n=== 结果 ===")
for tbl_name, _ in APIS:
    with engine.connect() as conn:
        r = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl_name}"'))
        cnt = r.scalar()
        r2 = conn.execute(text(f'SELECT COUNT(DISTINCT ts_code) FROM "{tbl_name}"'))
        stk = r2.scalar()
        r3 = conn.execute(text(f"SELECT COUNT(*) FROM \"{tbl_name}\" WHERE ts_code='600519.SH'"))
        mt = r3.scalar()
    print(f"  {tbl_name}: {cnt:,} 行, {stk} 只股票, 茅台={mt}")
print("✅ 完成")
