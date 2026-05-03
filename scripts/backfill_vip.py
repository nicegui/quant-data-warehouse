#!/usr/bin/env python3
"""Memory-efficient bulk backfill for VIP financial statement tables.

Unlike batch_missing.py which loads entire DataFrames into memory,
this processes in 1000-row chunks, reuses DB connections, and
explicitly frees memory after each period.

Usage:
  python3 -u scripts/backfill_vip.py income_vip --since 20140101
  python3 -u scripts/backfill_vip.py balancesheet_vip --since 20140101
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from datetime import datetime

import tushare as ts
from psycopg2 import connect
from psycopg2.extras import execute_values

CHUNK_SIZE = 1000  # rows per INSERT batch
HTTP_TIMEOUT = 120

TABLES = {
    "income_vip": {
        "table": "raw_income",
        "conflict": "ts_code, end_date, report_type",
    },
    "balancesheet_vip": {
        "table": "raw_balance_sheet",
        "conflict": "ts_code, end_date, report_type",
    },
    "cashflow_vip": {
        "table": "raw_cashflow",
        "conflict": "ts_code, end_date, report_type",
    },
    "forecast_vip": {
        "table": "raw_forecast",
        "conflict": "ts_code, end_date",
    },
    "express_vip": {
        "table": "raw_express",
        "conflict": "ts_code, end_date, ann_date",
    },
    "dividend_vip": {
        "table": "raw_dividend",
        "conflict": "ts_code, end_date, div_proc",
    },
    "fina_indicator_vip": {
        "table": "raw_fina_indicator",
        "conflict": "ts_code, end_date, ann_date",
    },
    "fina_audit_vip": {
        "table": "raw_fina_audit",
        "conflict": "ts_code, end_date",
    },
    "disclosure_date": {
        "table": "raw_disclosure_date",
        "conflict": "ts_code, end_date",
        "api": "disclosure_date",
        "param_name": "end_date",
    },
}

STR_FIELDS = {"ts_code", "ann_date", "f_ann_date", "end_date",
              "report_type", "comp_type", "end_type", "update_flag",
              # dividend / non-financial
              "div_proc", "record_date", "ex_date", "pay_date",
              "div_listdate", "imp_ann_date", "base_date",
              # forecast
              "type", "first_ann_date",
              # express
              "perf_summary",
              # disclosure / non-financial
              "pre_date", "actual_date", "modify_date",
}

# Fallback mapping for API functions
API_FUNCS = {
    "income_vip": "income_vip",
    "balancesheet_vip": "balancesheet_vip",
    "cashflow_vip": "cashflow_vip",
    "forecast_vip": "forecast_vip",
    "express_vip": "express_vip",
    "dividend_vip": "dividend_vip",
}

DSN = "host=127.0.0.1 dbname=quantdb user=quant password=quant_pass"


def get_periods(since: str) -> list[str]:
    """Generate all report periods (YYYYMMDD)."""
    periods = []
    year_start = int(since[:4])
    year_end = datetime.now().year
    for y in range(year_start, year_end + 2):
        for md in ["0331", "0630", "0930", "1231"]:
            p = f"{y}{md}"
            if p >= since and p <= datetime.now().strftime("%Y%m%d"):
                periods.append(p)
    return periods


def safe_float(v):
    """Convert to float, return None for NaN/inf."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if f != f else f  # NaN check
    except (ValueError, TypeError):
        return None


def backfill(api_name: str, config: dict, pro, since: str):
    table = config["table"]
    conflict = config["conflict"]

    periods = get_periods(since)
    print(f"📊 {api_name} → {table}  ({len(periods)} periods from {periods[0]})")

    # Check existing
    conn = connect(DSN)
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT DISTINCT end_date FROM {table}")
        existing = {str(r[0])[:8] for r in cur.fetchall() if r[0]}
    except Exception:
        existing = set()
    cur.close()
    conn.close()

    missing = [p for p in periods if p not in existing]
    print(f"   existing={len(existing)}  missing={len(missing)}")

    api_func = getattr(pro, api_name, None)
    if api_func is None:
        fn_name = API_FUNCS.get(api_name, api_name)
        api_func = getattr(pro, fn_name, None)
    if api_func is None:
        print(f"❌ Unknown API: {api_name}")
        return

    total_rows = 0
    conn = connect(DSN)

    for i, period in enumerate(missing):
        t0 = time.time()
        try:
            param_name = config.get("param_name", "period")
            df = api_func(**{param_name: period})
            if df is None or df.empty:
                print(f"  [{i+1}/{len(missing)}] {period}: empty ({time.time()-t0:.0f}s)")
                time.sleep(0.5)
                continue

            n_fetched = len(df)
            n_written = 0

            # Process in chunks to limit memory
            for start in range(0, n_fetched, CHUNK_SIZE):
                end = min(start + CHUNK_SIZE, n_fetched)
                chunk = df.iloc[start:end]
                recs = []

                for _, row in chunk.iterrows():
                    rec = {}
                    for k in chunk.columns:
                        v = row[k]
                        if k in STR_FIELDS:
                            rec[k] = v
                        else:
                            rec[k] = safe_float(v)
                    rec["raw_json"] = json.dumps(
                        {k: (None if safe_float(row[k]) != safe_float(row[k]) else row[k])
                         for k in chunk.columns},
                        ensure_ascii=False, default=str,
                    )
                    recs.append(rec)

                cols = list(recs[0].keys())
                quoted = ", ".join(f'"{c}"' for c in cols)
                sql = (
                    f'INSERT INTO {table} ({quoted}) VALUES %s '
                    f"ON CONFLICT ({conflict}) DO NOTHING"
                )

                cur = conn.cursor()
                execute_values(cur, sql, [[r[c] for c in cols] for r in recs], page_size=500)
                n = cur.rowcount
                conn.commit()
                cur.close()
                n_written += n

                # Free chunk memory
                del recs, chunk

            total_rows += n_written
            elapsed = time.time() - t0
            mem_mb = _get_mem_mb()
            print(f"  [{i+1}/{len(missing)}] {period}: {n_fetched:,}→{n_written} in {elapsed:.0f}s | {mem_mb:.0f}MB",
                  flush=True)

            # Explicit cleanup
            del df
            gc.collect()

        except Exception as e:
            print(f"  [{i+1}/{len(missing)}] {period}: ERROR {e}")
            conn.rollback()

        time.sleep(0.5)

    conn.close()
    print(f"✅ {api_name}: {total_rows:,} total new rows\n")


def _get_mem_mb():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("api", choices=list(TABLES))
    parser.add_argument("--since", default="20140101")
    args = parser.parse_args()

    token = os.getenv(
        "TUSHARE_TOKEN",
        "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185",
    )
    pro = ts.pro_api(token, timeout=HTTP_TIMEOUT)

    config = TABLES[args.api]
    backfill(args.api, config, pro, args.since)


if __name__ == "__main__":
    main()
