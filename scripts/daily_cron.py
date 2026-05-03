#!/usr/bin/env python3
"""日频数据自动拉取 — 每交易日下午 5:00 运行.

拉取所有日频表最新数据:
  stock_daily, moneyflow, moneyflow_mkt_dc, hsgt_top10, ggt_top10,
  margin_detail, margin_total, daily_basic, stock_st, stock_hsgt

使用 UPSERT + ON CONFLICT 避免重复。
"""

from __future__ import annotations

import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone

import tushare as ts
from psycopg2 import connect
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("daily_cron")

TOKEN = os.getenv(
    "TUSHARE_TOKEN",
    "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185",
)
DB_DSN = "host=127.0.0.1 dbname=quantdb user=quant password=quant_pass"
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai


def is_trading_day(pro, date_str: str) -> bool:
    df = pro.trade_cal(exchange="SSE", start_date=date_str, end_date=date_str)
    if df is not None and not df.empty:
        return int(df.iloc[0]["is_open"]) == 1
    return False


def bulk_upsert(
    table: str,
    records: list[dict],
    conflict_cols: list[str],
) -> int:
    """PostgreSQL UPSERT — single-round-trip bulk insert."""
    if not records:
        return 0
    cols = list(records[0].keys())
    quoted = ", ".join(f'"{c}"' for c in cols)
    conflict = ", ".join(f'"{c}"' for c in conflict_cols)
    sql = (
        f'INSERT INTO "{table}" ({quoted}) VALUES %s '
        f"ON CONFLICT ({conflict}) DO NOTHING"
    )
    values = [[rec.get(c) for c in cols] for rec in records]
    try:
        conn = connect(DB_DSN)
        cur = conn.cursor()
        execute_values(cur, sql, values, page_size=1000)
        n = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return n
    except Exception as e:
        log.error("  upsert %s: %s", table, e)
        return 0


def fetch_daily(pro, today: str):
    """Run all daily collectors for a single trading day."""
    conn = connect(DB_DSN)

    # ── 1. stock_daily ──────────────────────────────
    log.info("  stock_daily …")
    df = pro.daily(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_stock_daily", recs, ["ts_code", "trade_date"])
        log.info("    %d new / %d fetched", n, len(recs))
    else:
        log.info("    0 rows")

    # ── 2. daily_basic ──────────────────────────────
    log.info("  daily_basic …")
    df = pro.daily_basic(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_daily_basic", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 3. moneyflow ────────────────────────────────
    log.info("  moneyflow …")
    df = pro.moneyflow(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_moneyflow", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 4. moneyflow_mkt_dc (大盘资金) ──────────────
    log.info("  moneyflow_mkt_dc …")
    df = pro.moneyflow_mkt_dc(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_moneyflow_mkt_dc", recs, ["trade_date"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 5. hsgt_top10 ───────────────────────────────
    log.info("  hsgt_top10 …")
    df = pro.hsgt_top10(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_hsgt_top10", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 6. ggt_top10 ────────────────────────────────
    log.info("  ggt_top10 …")
    df = pro.ggt_top10(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_ggt_top10", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 7. margin_detail ────────────────────────────
    log.info("  margin_detail …")
    df = pro.margin_detail(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_margin_detail", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 8. margin (总量) ────────────────────────────
    log.info("  margin …")
    df = pro.margin(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_margin_total", recs, ["trade_date", "exchange_id"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 9. stock_st ─────────────────────────────────
    log.info("  stock_st …")
    df = pro.stock_st(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_stock_st", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 10. stock_hsgt (4 types) ────────────────────
    log.info("  stock_hsgt …")
    total_fetched = 0
    total_new = 0
    for tp in ("HK_SZ", "SZ_HK", "HK_SH", "SH_HK"):
        df = pro.stock_hsgt(trade_date=today, type=tp)
        if df is not None and not df.empty:
            recs = df.to_dict("records")
            n = bulk_upsert("raw_stock_hsgt", recs, ["trade_date", "ts_code", "type"])
            total_fetched += len(recs)
            total_new += n
        time.sleep(0.15)
    log.info("    %d new / %d fetched", total_new, total_fetched)

    # ── 11. stk_limit ────────────────────────────────
    log.info("  stk_limit …")
    df = pro.stk_limit(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_stk_limit", recs, ["trade_date", "ts_code"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 12. ggt_daily ────────────────────────────────
    log.info("  ggt_daily …")
    df = pro.ggt_daily(trade_date=today)
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        n = bulk_upsert("raw_ggt_daily", recs, ["trade_date"])
        log.info("    %d new / %d fetched", n, len(recs))

    # ── 13. income_vip (最近四个报告期) ─────────────
    log.info("  income_vip …")
    ym = int(today[:6])
    year, month = ym // 100, ym % 100
    periods = []
    for offset in range(4):
        p_end = ((3 * (offset + 1)) % 12) or 12
        if p_end > month:
            py = year - 1
        else:
            py = year
        periods.append(f"{py}{p_end:02d}{'31' if p_end == 12 else '30'}")
    periods = sorted(set(periods))
    for period in periods:
        df = pro.income_vip(period=period)
        if df is not None and not df.empty:
            recs = df.to_dict("records")
            n = bulk_upsert("raw_income", recs, ["ts_code", "end_date", "report_type"])
            log.info("    period=%s: %d new / %d fetched", period, n, len(recs))
        time.sleep(0.3)

    # ── 14. balancesheet_vip (最近四个报告期) ────────
    log.info("  balancesheet_vip …")
    for period in periods:
        df = pro.balancesheet_vip(period=period)
        if df is not None and not df.empty:
            recs = df.to_dict("records")
            n = bulk_upsert("raw_balance_sheet", recs, ["ts_code", "end_date", "report_type"])
            log.info("    period=%s: %d new / %d fetched", period, n, len(recs))
        time.sleep(0.3)

    # ── 15. cashflow_vip (最近四个报告期) ────────────
    log.info("  cashflow_vip …")
    for period in periods:
        df = pro.cashflow_vip(period=period)
        if df is not None and not df.empty:
            recs = df.to_dict("records")
            n = bulk_upsert("raw_cashflow", recs, ["ts_code", "end_date", "report_type"])
            log.info("    period=%s: %d new / %d fetched", period, n, len(recs))
        time.sleep(0.3)

    conn.close()


def main():
    today = datetime.now(TZ).strftime("%Y%m%d")
    log.info("=" * 60)
    log.info("日频数据拉取 — %s", today)
    log.info("=" * 60)

    pro = ts.pro_api(TOKEN)

    # 检查交易日
    if not is_trading_day(pro, today):
        log.info("⏭  %s 非交易日，跳过", today)
        return

    log.info("✅ %s 是交易日，开始拉取", today)
    fetch_daily(pro, today)
    log.info("🎉 完成")


if __name__ == "__main__":
    main()
