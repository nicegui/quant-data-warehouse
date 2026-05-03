#!/usr/bin/env python3
"""Batch historical pull V2 — strategy-aware per API capability.

Strategy per collector:
  - cb_daily:      date range → pull by month (~30 calls for 5 years)
  - fut_daily:     date range → pull by month (~30 calls)
  - moneyflow_hsgt: date range → pull by month (~30 calls)
  - fund_daily:    trade_date only → iterate days (~1600 calls, ~9 min)
  - fund_nav:      nav_date only → iterate days (~1600 calls)
  - hk_daily:      10 calls/day limit → pull last 10 days only (best effort)
  - fund_flow:     AKShare per-stock → CSI 300 components (~300 stocks)

Run: python3 scripts/batch_historical_pull_v2.py [--skip-fund-flow]
"""
import os, sys, time, argparse
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(".env")

TOKEN = os.getenv("TUSHARE_TOKEN")
START = "20200101"  # pull from 2020-01-01


def month_ranges(start: str, end: str) -> list[tuple[str, str]]:
    """Generate (start_date, end_date) pairs for each month."""
    d = datetime.strptime(start[:6], "%Y%m")
    e = datetime.strptime(end, "%Y%m%d")
    ranges = []
    while d <= e:
        m_start = d.strftime("%Y%m") + "01"
        next_month = d + relativedelta(months=1)
        m_end = (next_month - timedelta(days=1)).strftime("%Y%m%d")
        if m_end > end:
            m_end = end
        ranges.append((m_start, m_end))
        d = next_month
    return ranges


def trading_dates(start: str, end: str) -> list[str]:
    """All weekdays from start to end."""
    d = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    dates = []
    while d <= e:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return dates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fund-flow", action="store_true")
    args = parser.parse_args()

    today = date.today().strftime("%Y%m%d")
    print(f"📅 Pull range: {START} → {today}")
    print()

    totals = {}

    # ═══════════════════════════════════════
    # Group A: Date range support → monthly batches
    # ═══════════════════════════════════════

    from src.collectors.impl.cb_daily import CbDailyCollector
    from src.collectors.impl.futures import FuturesCollector
    from src.collectors.impl.moneyflow_hsgt import MoneyflowHsgtCollector

    range_collectors = [
        ("cb_daily", CbDailyCollector(TOKEN)),
        ("fut_daily", FuturesCollector(TOKEN)),
        ("moneyflow_hsgt", MoneyflowHsgtCollector(TOKEN)),
    ]

    months = month_ranges(START, today)
    print(f"📦 Group A (date range): {len(months)} months × 3 tables")

    for name, collector in range_collectors:
        written_total = 0
        print(f"\n🔄 {name} ...")
        for i, (m_start, m_end) in enumerate(months, 1):
            try:
                # Checkpoint-aware: only fetch if we don't already have up to m_end
                ck = collector.get_checkpoint_date()
                if ck and ck >= m_end:
                    continue

                result = collector.run(start_date=m_start, end_date=m_end)
                w = result.get("written", 0)
                written_total += w
                status = f"+{w}" if w else "skip"
                if i % 6 == 0 or w > 0:
                    print(f"  {m_start[:6]}: {status:>6s}  (total: {written_total})")
            except Exception as e:
                print(f"  {m_start[:6]}: ERROR - {e}")
            time.sleep(0.4)

        totals[name] = written_total
        print(f"  ✅ {name}: {written_total} rows total")

    # ═══════════════════════════════════════
    # Group B: trade_date only → daily iteration
    # ═══════════════════════════════════════
    from src.collectors.impl.fund import FundCollector

    dates = trading_dates(START, today)
    print(f"\n📦 Group B (daily iteration): {len(dates)} days × 1 table (fund_daily)")
    
    fund_c = FundCollector(TOKEN)
    fund_written = 0
    
    for i, d in enumerate(dates, 1):
        try:
            result = fund_c.run(trade_date=d)
            w = result.get("written", 0)
            fund_written += w
            pct = i / len(dates) * 100
            if i % 200 == 0 or (w > 0 and w % 2000 == 0):
                print(f"  [{i}/{len(dates)} {pct:.0f}%] {d}: +{w} (total: {fund_written})")
        except Exception as e:
            print(f"  {d}: ERROR - {e}")
        time.sleep(0.35)
    
    totals["fund_daily"] = fund_written
    print(f"  ✅ fund_daily: {fund_written} rows total")

    # ═══════════════════════════════════════
    # Group C: fund_nav — nav_date iteration  
    # ═══════════════════════════════════════
    from src.collectors.impl.fund_nav import FundNavCollector

    print(f"\n📦 Group C (daily iteration): {len(dates)} days × fund_nav")
    
    nav_c = FundNavCollector(TOKEN)
    nav_written = 0
    
    for i, d in enumerate(dates, 1):
        try:
            result = nav_c.run(nav_date=d)
            w = result.get("written", 0)
            nav_written += w
            if i % 200 == 0 or (w > 0 and w % 2000 == 0):
                print(f"  [{i}/{len(dates)} {i/len(dates)*100:.0f}%] {d}: +{w} (total: {nav_written})")
        except Exception as e:
            print(f"  {d}: ERROR - {e}")
        time.sleep(0.35)
    
    totals["fund_nav"] = nav_written
    print(f"  ✅ fund_nav: {nav_written} rows total")

    # ═══════════════════════════════════════
    # Group D: hk_daily — 10 calls/day max, pull last 10 days
    # ═══════════════════════════════════════
    from src.collectors.impl.hk_daily import HkDailyCollector

    recent_dates = trading_dates(
        (datetime.now() - timedelta(days=14)).strftime("%Y%m%d"),
        today
    )[-10:]
    
    print(f"\n📦 Group D (hk_daily, 10 calls/day): last {len(recent_dates)} days")
    
    hk_c = HkDailyCollector(TOKEN)
    hk_written = 0
    
    for d in recent_dates:
        try:
            result = hk_c.run(trade_date=d)
            w = result.get("written", 0)
            hk_written += w
            print(f"  {d}: +{w}")
        except Exception as e:
            print(f"  {d}: ERROR - {e}")
        time.sleep(0.5)
    
    totals["hk_daily"] = hk_written
    print(f"  ✅ hk_daily: {hk_written} rows (limited by API quota)")

    # ═══════════════════════════════════════
    # Group E: fund_flow — AKShare, CSI 300 components
    # ═══════════════════════════════════════
    if not args.skip_fund_flow:
        from src.collectors.impl.fund_flow import FundFlowCollector
        from src.collectors.impl.stock_basic import StockBasicCollector

        print(f"\n📦 Group E: fund_flow — CSI 300 components")
        
        sb = StockBasicCollector(TOKEN)
        stocks = sb.fetch()
        print(f"  Total listed: {len(stocks)}")

        # CSI 300 members can be identified by index, but for simplicity
        # pull top 300 by code order (earliest codes = large caps)
        stock_list = [(r["ts_code"], r["name"]) for r in stocks 
                      if r.get("list_status") == "L"]
        stock_list.sort(key=lambda x: x[0])
        target = stock_list[:300]
        print(f"  Target: {len(target)} stocks")

        ff = FundFlowCollector()
        ff_written = 0
        
        for i, (code, name) in enumerate(target, 1):
            mkt = "sh" if code.endswith(".SH") else "sz"
            symbol = code.split(".")[0]
            try:
                raw = ff.fetch(stock=symbol, market=mkt)
                validated = ff.validate(raw)
                written = ff.store_raw(validated)
                ff_written += written
                if i % 50 == 0:
                    print(f"  [{i}/{len(target)}] {code} {name}: +{written} (total: {ff_written})")
            except Exception as e:
                print(f"  [{i}] {code}: ERROR - {e}")
            time.sleep(0.6)  # rate limit for AKShare

        totals["fund_flow"] = ff_written
        print(f"  ✅ fund_flow: {ff_written} rows across {len(target)} stocks")

    # ═══════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════
    print("\n" + "="*60)
    print("📊 INGESTION SUMMARY")
    print("="*60)
    for name, rows in totals.items():
        print(f"  {name:20s}: {rows:>10,d} rows")
    print(f"  {'TOTAL':20s}: {sum(totals.values()):>10,d} rows")


if __name__ == "__main__":
    main()
