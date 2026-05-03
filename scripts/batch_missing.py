#!/usr/bin/env python3
"""批量回补 5 张核心表的历史数据.

用法:
    python3 scripts/batch_missing.py                    # 回补全部 5 张表
    python3 scripts/batch_missing.py margin_total       # 只回补指定表
    python3 scripts/batch_missing.py --days 30          # 仅回补最近 30 天
    python3 scripts/batch_missing.py --since 20200101   # 从指定日期开始

表:
  margin_total   — 融资融券总量 (3 行/日, SSE+SZSE+BSE)
  margin_detail  — 融资融券个股明细 (~4,400 行/日)
  moneyflow      — 个股资金流向 (~5,200 行/日)
  daily_basic    — 每日基本面指标 (~5,500 行/日)
  express        — 业绩快报 (按 end_date, ~2,000 行/次)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import tushare as ts
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.engine import get_engine
from sqlalchemy import text

TOKEN = os.getenv("TUSHARE_TOKEN", "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185")

# 表配置: (collector 名, checkpoint_key, api_name, fetch_params 工厂)
TABLES = {
    "margin_total": {
        "checkpoint_key": "trade_date",
        "api": "margin",
        "date_source": "trade_cal",  # 用交易日历
        "batch_size": 30,  # 每次 30 个交易日
        "params_fn": lambda date: {"trade_date": date},
    },
    "margin_detail": {
        "checkpoint_key": "trade_date",
        "api": "margin_detail",
        "date_source": "trade_cal",
        "batch_size": 20,
        "params_fn": lambda date: {"trade_date": date},
    },
    "moneyflow": {
        "checkpoint_key": "trade_date",
        "api": "moneyflow",
        "date_source": "trade_cal",
        "batch_size": 20,
        "params_fn": lambda date: {"trade_date": date},
    },
    "daily_basic": {
        "checkpoint_key": "trade_date",
        "api": "daily_basic",
        "date_source": "trade_cal",
        "batch_size": 20,
        "params_fn": lambda date: {"trade_date": date},
    },
    "express": {
        "checkpoint_key": "end_date",
        "api": "express",
        "date_source": "end_dates",  # 报告期，非交易日
        "batch_size": 10,
        "params_fn": lambda date: {"end_date": date},
    },
    "stock_st": {
        "checkpoint_key": "trade_date",
        "api": "stock_st",
        "date_source": "trade_cal",
        "batch_size": 30,
        "params_fn": lambda date: {"trade_date": date},
    },
    "stock_hsgt": {
        "checkpoint_key": "trade_date",
        "api": "stock_hsgt",
        "date_source": "trade_cal",
        "batch_size": 20,
        "params_fn": lambda date: {"trade_date": date},  # fetch 内部自动遍历 4 类型
    },
    "stk_limit": {
        "checkpoint_key": "trade_date",
        "api": "stk_limit",
        "date_source": "trade_cal",
        "batch_size": 30,
        "params_fn": lambda date: {"trade_date": date},
    },
    "ggt_daily": {
        "checkpoint_key": "trade_date",
        "api": "ggt_daily",
        "date_source": "trade_cal",
        "batch_size": 30,
        "params_fn": lambda date: {"trade_date": date},
    },
    "ggt_monthly": {
        "checkpoint_key": "month",
        "api": "ggt_monthly",
        "date_source": "months",
        "batch_size": 3,  # 20/min 限速，3个月一次足够
        "params_fn": lambda date: {"month": date},
    },
    "income": {
        "checkpoint_key": "period",
        "api": "income_vip",
        "date_source": "end_dates",
        "batch_size": 5,
        "params_fn": lambda date: {"period": date},
        "db_date_col": "end_date",
    },
    "balance_sheet": {
        "checkpoint_key": "period",
        "api": "balancesheet_vip",
        "date_source": "end_dates",
        "batch_size": 5,
        "params_fn": lambda date: {"period": date},
        "db_date_col": "end_date",
    },
}


def get_existing_dates(engine, table_name: str, date_col: str) -> set[str]:
    """获取表中已有的日期."""
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT DISTINCT {date_col} FROM {table_name}")
        )
        return {str(row[0])[:8] for row in result if row[0]}


def get_trade_dates(pro, since: str) -> list[str]:
    """获取所有交易日."""
    df = pro.trade_cal(exchange="SSE", start_date=since, end_date=datetime.now().strftime("%Y%m%d"))
    return sorted(df[df["is_open"] == 1]["cal_date"].tolist())


def get_end_dates(pro, since: str) -> list[str]:
    """获取所有财报报告期 (express 用)."""
    from datetime import date as dt_date
    end_dates = set()
    year = int(since[:4])
    current_year = dt_date.today().year
    for y in range(year, current_year + 1):
        for md in ["0331", "0630", "0930", "1231"]:
            d = f"{y}{md}"
            if d >= since and d <= dt_date.today().strftime("%Y%m%d"):
                end_dates.add(d)
    return sorted(end_dates)


def get_months(since: str) -> list[str]:
    """获取所有月份 (YYYYMM) — ggt_monthly 等月度表用."""
    from datetime import date as dt_date
    start_ym = since[:6]
    today = dt_date.today()
    months = []
    y, m = int(start_ym[:4]), int(start_ym[4:6])
    end_ym = today.strftime("%Y%m")
    while True:
        ym = f"{y}{m:02d}"
        if ym > end_ym:
            break
        months.append(ym)
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def backfill_table(table_name: str, config: dict, pro, engine, since: str, max_days: int = 0):
    """回补单张表."""
    table = f"raw_{table_name}"
    date_col = config["checkpoint_key"]
    api_name = config["api"]

    print(f"\n{'='*60}")
    print(f"📊 {table_name} ({api_name})")
    print(f"{'='*60}")

    # 1. 获取目标日期列表
    if config["date_source"] == "end_dates":
        target_dates = get_end_dates(pro, since)
    elif config["date_source"] == "months":
        target_dates = get_months(since)
    else:
        target_dates = get_trade_dates(pro, since)

    if max_days > 0:
        target_dates = target_dates[-max_days:]

    print(f"   目标日期范围: {target_dates[0]} ~ {target_dates[-1]} ({len(target_dates)} 天)")

    # 2. 获取已有日期 (date_col 用于 DB 查询，可能与 checkpoint_key 不同)
    db_col = config.get("db_date_col", date_col)
    existing = get_existing_dates(engine, table, db_col)
    missing = [d for d in target_dates if d not in existing]
    print(f"   已有: {len(existing)} 天, 缺失: {len(missing)} 天")

    if not missing:
        print("   ✅ 数据完整, 跳过")
        return {"table": table_name, "fetched": 0, "written": 0, "errors": 0}

    # 3. 分批回补
    batch_size = config["batch_size"]
    total_fetched = 0
    total_written = 0
    total_errors = 0

    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]
        batch_fetched = 0
        batch_written = 0

        for date_str in batch:
            try:
                if api_name == "stock_hsgt":
                    # stock_hsgt 必须传 type, 自动遍历 4 种
                    records = []
                    for tp in ("HK_SZ", "SZ_HK", "HK_SH", "SH_HK"):
                        df = pro.stock_hsgt(trade_date=date_str, type=tp)
                        if df is not None and not df.empty:
                            records.extend(df.to_dict(orient="records"))
                else:
                    if date_col == "period":
                        params = {"period": date_str}
                    elif date_col == "month":
                        params = {"month": date_str}
                    elif date_col == "trade_date":
                        params = {"trade_date": date_str}
                    else:
                        params = {"end_date": date_str}
                    api = getattr(pro, api_name)
                    df = api(**params)
                    if df is None or df.empty:
                        continue
                    records = df.to_dict(orient="records")
                batch_fetched += len(records)

                # UPSERT 写入
                written = upsert_records(engine, table, records, date_col)
                batch_written += written

            except Exception as e:
                print(f"   ❌ {date_str}: {e}")
                total_errors += 1
                time.sleep(2)
                continue

            # Rate limit: ~60 calls/min for Tushare free tier, we're on premium
            time.sleep(0.15)

        total_fetched += batch_fetched
        total_written += batch_written
        pct = min(100, (i + len(batch)) * 100 // len(missing))
        print(f"   [{pct:3d}%] {batch[0]}~{batch[-1]} | fetch={batch_fetched} write={batch_written} | "
              f"累计 fetch={total_fetched} write={total_written} err={total_errors}")

        # Batch 间稍息
        if i + batch_size < len(missing):
            time.sleep(0.5)

    print(f"   ✅ 完成: fetched={total_fetched} written={total_written} errors={total_errors}")
    return {"table": table_name, "fetched": total_fetched, "written": total_written, "errors": total_errors}


def upsert_records(engine, table: str, records: list[dict], date_col: str) -> int:
    """使用 INSERT ... ON CONFLICT 批量写入."""
    if not records:
        return 0

    # 过滤掉 id 和 timestamp 字段
    skip_cols = {"id", "created_at", "updated_at"}
    cols = [k for k in records[0].keys() if k not in skip_cols]

    # 构建值
    values = []
    params = {}
    for i, rec in enumerate(records):
        row_vals = []
        for col in cols:
            key = f"{col}_{i}"
            # 确保 trade_date 是 yyyymmdd 格式
            val = rec.get(col)
            if date_col == col and val and len(str(val)) > 8:
                val = str(val)[:10].replace("-", "")
            elif isinstance(val, float) and (val != val):  # NaN
                val = None
            params[key] = val
            row_vals.append(f":{key}")
        values.append(f"({', '.join(row_vals)})")

    col_list = ", ".join(cols)
    values_str = ", ".join(values)

    # 唯一约束: trade_date 类表用 (trade_date, ts_code) 或 (trade_date, exchange_id)
    # 对于 margin_total: (trade_date, exchange_id)
    # 对于 margin_detail/moneyflow/daily_basic: (trade_date, ts_code)
    # 对于 express: (ts_code, end_date, ann_date)
    unique_cols = _get_unique_cols(table)

    update_cols = [c for c in cols if c not in unique_cols]
    if update_cols:
        update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES {values_str} "
            f"ON CONFLICT ({', '.join(unique_cols)}) DO UPDATE SET {update_clause}"
        )
    else:
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES {values_str} "
            f"ON CONFLICT ({', '.join(unique_cols)}) DO NOTHING"
        )

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            conn.commit()
            count = result.rowcount
            # ON CONFLICT DO NOTHING returns 0 for skipped rows; count affected
            return count if count > 0 else len(records)  # approximate
    except Exception as e:
        # Fallback: try without ON CONFLICT (table might not have constraint)
        try:
            sql_simple = f"INSERT INTO {table} ({col_list}) VALUES {values_str}"
            with engine.connect() as conn:
                result = conn.execute(text(sql_simple), params)
                conn.commit()
                return len(records)
        except Exception:
            pass
        return 0


def _get_unique_cols(table: str) -> list[str]:
    if "margin_total" in table:
        return ["trade_date", "exchange_id"]
    elif "express" in table:
        return ["ts_code", "end_date", "ann_date"]
    elif "income" in table:
        return ["ts_code", "end_date", "report_type"]
    elif "balance_sheet" in table:
        return ["ts_code", "end_date", "report_type"]
    elif "margin_detail" in table:
        return ["trade_date", "ts_code"]
    elif "moneyflow" in table:
        return ["trade_date", "ts_code"]
    elif "daily_basic" in table:
        return ["trade_date", "ts_code"]
    elif "stock_st" in table:
        return ["trade_date", "ts_code"]
    elif "stock_hsgt" in table:
        return ["trade_date", "ts_code", "type"]
    elif "stk_limit" in table:
        return ["trade_date", "ts_code"]
    elif "ggt_daily" in table:
        return ["trade_date"]
    elif "ggt_monthly" in table:
        return ["month"]
    return ["trade_date"]


def main():
    parser = argparse.ArgumentParser(description="批量回补 Tushare 历史数据")
    parser.add_argument("tables", nargs="*", default=list(TABLES.keys()),
                        help="要回补的表名")
    parser.add_argument("--since", default="20200101", help="起始日期 (默认 2020-01-01)")
    parser.add_argument("--days", type=int, default=0, help="仅回补最近 N 天")
    args = parser.parse_args()

    # 验证表名
    invalid = [t for t in args.tables if t not in TABLES]
    if invalid:
        print(f"❌ 未知表: {invalid}")
        print(f"   可用: {list(TABLES.keys())}")
        sys.exit(1)

    print(f"🔧 Tushare 批量回补")
    print(f"   表: {', '.join(args.tables)}")
    print(f"   起始: {args.since}")
    if args.days:
        print(f"   限最近 {args.days} 天")

    pro = ts.pro_api(TOKEN)
    engine = get_engine()

    results = {}
    for table_name in args.tables:
        config = TABLES[table_name]
        result = backfill_table(table_name, config, pro, engine, args.since, args.days)
        results[table_name] = result

    # 汇总
    print(f"\n{'='*60}")
    print(f"📋 汇总")
    print(f"{'='*60}")
    total_f = total_w = total_e = 0
    for t, r in results.items():
        print(f"  {t:20s}  fetch={r['fetched']:>10,d}  write={r['written']:>10,d}  err={r['errors']}")
        total_f += r["fetched"]
        total_w += r["written"]
        total_e += r["errors"]
    print(f"  {'─'*50}")
    print(f"  {'合计':20s}  fetch={total_f:>10,d}  write={total_w:>10,d}  err={total_e}")


if __name__ == "__main__":
    main()
