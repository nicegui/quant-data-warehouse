#!/usr/bin/env python3
"""Pull financial data by quarter - fastest approach, ~25 API calls per table."""
import os, sys, time, logging
from datetime import datetime, date
import pandas as pd
import tushare as ts
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

LOG_FILE = "/tmp/pull_fin_quarterly.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)]
)

def get_token():
    with open("/Users/admin/quant-data-warehouse/.env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("TUSHARE_TOKEN="):
                v = line.split("=", 1)[1].strip().strip("'\"")
                return v
    return None

token = get_token()
if not token:
    logging.error("No token found")
    sys.exit(1)

pro = ts.pro_api(token)

DB_URL = os.environ.get("DB_URL", "postgresql://quant:quant_pass@localhost:5432/quantdb")
engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5)


def bulk_upsert(df, table_name, pk_cols):
    if df.empty:
        return 0
    # Build INSERT statement manually
    cols = list(df.columns)
    placeholders = ", ".join([f":{c}" for c in cols])
    quoted_cols = ", ".join([f'"{c}"' for c in cols])
    
    # Build ON CONFLICT clause
    pk_quoted = ", ".join([f'"{c}"' for c in pk_cols])
    sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders}) ON CONFLICT ({pk_quoted}) DO NOTHING'
    
    records = df.to_dict("records")
    total = 0
    batch_size = 500
    
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            result = conn.execute(text(sql), batch)
            total += result.rowcount
    
    return total


def create_tables():
    """Verify tables exist with correct schema - don't recreate since rebuild script handles that."""
    api_configs = [
        ("raw_fin_income", "income_vip"),
        ("raw_fin_balance", "balancesheet_vip"),
        ("raw_fin_cashflow", "cashflow_vip"),
        ("raw_fin_indicators", "fina_indicator_vip"),
    ]
    
    for table_name, _ in api_configs:
        with engine.connect() as conn:
            cnt = conn.execute(text(f"SELECT count(*) FROM information_schema.columns WHERE table_name = '{table_name}'")).scalar()
        logging.info(f"Table {table_name}: {cnt} columns (expected ~100), ready")
    
    return api_configs


def pull_table(table_name, api_name, max_quarters=25):
    """Pull all data for a financial table by quarter."""
    # Check existing
    existing = 0
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        existing = result.scalar()
    
    logging.info(f"  {table_name}: {existing} existing rows")
    
    # Generate quarter end dates
    quarters = []
    today = date.today()
    for year in range(today.year, 1989, -1):
        for q in [(4, "1231"), (3, "0930"), (2, "0630"), (1, "0331")]:
            qnum, qstr = q
            if year == today.year and qnum > ((today.month - 1) // 3 + 1):
                continue
            quarters.append(f"{year}{qstr}")
    
    quarters = quarters[:max_quarters]
    logging.info(f"  Will process {len(quarters)} quarters")
    
    api_func = getattr(pro, api_name)
    total = 0
    
    for i, end_date in enumerate(quarters):
        # Check if this quarter already fully loaded
        if existing > 0:
            with engine.connect() as conn:
                sql = text(f'SELECT COUNT(*) FROM "{table_name}" WHERE "end_date" = :ed')
                cnt = conn.execute(sql, {"ed": end_date}).scalar()
            # If we have >4500 rows for this quarter, it's complete (~5000 stocks)
            if cnt > 4500:
                logging.info(f"  [{i+1}/{len(quarters)}] {end_date}: {cnt} rows, skip")
                continue
        
        for attempt in range(5):
            try:
                df = api_func(end_date=end_date)
                if df is None or df.empty:
                    logging.info(f"  [{i+1}/{len(quarters)}] {end_date}: empty")
                    break
                
                n = bulk_upsert(df, table_name, ["ts_code", "end_date"])
                total += n
                logging.info(f"  [{i+1}/{len(quarters)}] {end_date}: {n} new rows (cum {total})")
                break
            except Exception as e:
                msg = str(e)
                if "次数" in msg:
                    wait = min(30 * (attempt + 1), 120)
                    logging.warning(f"  [{i+1}/{len(quarters)}] {end_date}: rate limit, wait {wait}s")
                    time.sleep(wait)
                else:
                    logging.warning(f"  [{i+1}/{len(quarters)}] {end_date}: {e}, retry {attempt+1}")
                    time.sleep(10)
        
        time.sleep(0.3)  # small gap
    
    return total


if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("开始按季度拉取财务数据")
    logging.info("=" * 60)
    
    configs = create_tables()
    
    totals = {}
    for table_name, api_name in configs:
        logging.info(f"")
        logging.info(f"=== {table_name} ({api_name}) ===")
        n = pull_table(table_name, api_name)
        totals[table_name] = n
        logging.info(f"  -> +{n} rows")
    
    # Final counts
    logging.info("")
    logging.info("=" * 60)
    logging.info("Complete! Final counts:")
    for table_name, _ in configs:
        with engine.connect() as conn:
            cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
        logging.info(f"  {table_name}: {cnt} rows")
    logging.info("=" * 60)
