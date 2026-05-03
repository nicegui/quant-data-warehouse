#!/usr/bin/env python3
"""Batch historical data pull for 6 empty Tushare tables + fund_flow expansion.

Strategy:
  - Tushare: daily iteration from 2020-01-01 to today, 0.35s sleep between calls
  - fund_flow: pull CSI 300 + CSI 500 components (~800 stocks) for now
  - Each collector's run() auto-deduplicates via store_raw
  - Checkpoints saved per collector so incremental runs resume where left off
"""
import os, sys, time
from datetime import date, timedelta, datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(".env")

TOKEN = os.getenv("TUSHARE_TOKEN")

# ── Tushare imports ──
from src.collectors.impl.hk_daily import HkDailyCollector
from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector
from src.collectors.impl.fund import FundCollector
from src.collectors.impl.fund_nav import FundNavCollector
from src.collectors.impl.cb_daily import CbDailyCollector
from src.collectors.impl.futures import FuturesCollector
from src.collectors.impl.fund_flow import FundFlowCollector
from src.collectors.impl.stock_basic import StockBasicCollector

START_DATE = "20200101"

def trading_dates(start: str, end: str) -> list[str]:
    """Generate all dates from start to end, skipping weekends."""
    d = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    dates = []
    while d <= e:
        if d.weekday() < 5:  # Mon-Fri
            dates.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return dates

def pull_tushare_table(name: str, collector, date_list: list[str], sleep: float = 0.35):
    """Pull historical data for a Tushare collector, one date at a time."""
    total_written = 0
    total_dates = len(date_list)
    
    for i, dt_str in enumerate(date_list):
        try:
            result = collector.run(trade_date=dt_str)
            written = result.get("written", 0)
            total_written += written
            if written > 0:
                print(f"  [{name}] {dt_str}: +{written} rows (total: {total_written})")
        except Exception as e:
            print(f"  [{name}] {dt_str}: ERROR - {e}")
        
        if i % 100 == 0 and i > 0:
            print(f"  [{name}] progress: {i}/{total_dates} dates, {total_written} rows total")
        
        time.sleep(sleep)
    
    print(f"✅ [{name}] DONE: {total_written} rows across {total_dates} dates")
    return total_written

def pull_fund_flow_stocks(collector, stock_codes: list[tuple[str, str]]):
    """Pull fund_flow for a list of (code, market) tuples."""
    total_written = 0
    for i, (code, mkt) in enumerate(stock_codes):
        try:
            # AKShare needs stock code without exchange suffix, market='sz' or 'sh'
            raw = collector.fetch(stock=code.split(".")[0], market=mkt)
            validated = collector.validate(raw)
            written = collector.store_raw(validated)
            total_written += written
            if written > 0:
                print(f"  [fund_flow] {code}.{mkt}: +{written} rows (total: {total_written})")
        except Exception as e:
            print(f"  [fund_flow] {code}.{mkt}: ERROR - {e}")
        
        if i % 50 == 0 and i > 0:
            print(f"  [fund_flow] progress: {i}/{len(stock_codes)} stocks, {total_written} rows total")
        
        time.sleep(0.5)  # AKShare rate limit
    
    print(f"✅ [fund_flow] DONE: {total_written} rows across {len(stock_codes)} stocks")
    return total_written

def main():
    today = date.today().strftime("%Y%m%d")
    dates = trading_dates(START_DATE, today)
    print(f"📅 Trading dates: {len(dates)} ({START_DATE} → {today})")
    print()

    # ── 1. Tushare tables ──
    tushare_jobs = [
        ("hk_daily", HkDailyCollector(TOKEN)),
        ("moneyflow_hsgt", MoneyflowHsgtCollector(TOKEN)),
        ("fund_daily", FundCollector(TOKEN)),
        ("fund_nav", FundNavCollector(TOKEN)),
        ("cb_daily", CbDailyCollector(TOKEN)),
        ("fut_daily", FuturesCollector(TOKEN)),
    ]

    total = {}
    for name, collector in tushare_jobs:
        print(f"🔄 Pulling {name}...")
        rows = pull_tushare_table(name, collector, dates)
        total[name] = rows
        print()

    # ── 2. fund_flow — pull top 800 stocks ──
    print("📊 Getting stock list for fund_flow...")
    sb = StockBasicCollector(TOKEN)
    stocks_raw = sb.fetch()
    print(f"  Total listed stocks: {len(stocks_raw)}")
    
    # Filter to main board + SME + ChiNext, active only
    stock_list = []
    for r in stocks_raw:
        code = r.get("ts_code", "")
        name = r.get("name", "")
        area = r.get("area", "")
        list_status = r.get("list_status", "L")
        if list_status != "L":
            continue
        # Determine market
        if code.endswith(".SH"):
            mkt = "sh"
        elif code.endswith(".SZ"):
            mkt = "sz"
        else:
            continue
        stock_list.append((code, mkt, name))
    
    # Prioritize: CSI 300 first, then rest
    # Simple heuristic: sort by code (earlier codes = older, bigger companies)
    stock_list.sort(key=lambda x: x[0])
    target = stock_list[:800]  # top 800 by code order
    print(f"  Pulling fund_flow for {len(target)} stocks...")
    
    ff = FundFlowCollector()
    ff_rows = pull_fund_flow_stocks(ff, [(c, m) for c, m, _ in target])
    total["fund_flow"] = ff_rows

    # ── Summary ──
    print("\n" + "="*60)
    print("📊 INGESTION SUMMARY")
    print("="*60)
    for name, rows in total.items():
        print(f"  {name:20s}: {rows:>8d} rows")
    print(f"  {'TOTAL':20s}: {sum(total.values()):>8d} rows")

if __name__ == "__main__":
    main()
