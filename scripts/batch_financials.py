#!/usr/bin/env python3
"""Batch pull all core financial/holder/market tables. Direct API + _store_dedup."""
import os, sys, time, json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT); os.chdir(PROJECT)

from dotenv import load_dotenv; load_dotenv('.env')
import tushare as ts
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

from src.db.session import db_session
from src.collectors.base import BaseCollector

# Get base class _store_dedup helper
_store = BaseCollector._store_dedup

# Get stock list
from src.collectors.impl.stock_basic import StockBasicCollector
stocks = StockBasicCollector(os.getenv("TUSHARE_TOKEN")).fetch()
stocks.sort(key=lambda x: x['ts_code'])
target = stocks[:500]
today = date.today().strftime("%Y%m%d")

# ═══════════════════════════════════════════════
# PHASE 1: Date-range capable tables
# ═══════════════════════════════════════════════
print("="*50)
print("PHASE 1: Range-capable tables")
print("="*50)

# Generate month ranges
d = datetime(2020, 1, 1)
e = datetime.strptime(today, "%Y%m%d")
months = []
while d <= e:
    ms = d.strftime("%Y%m") + "01"
    nm = d + relativedelta(months=1)
    me = (nm - timedelta(days=1)).strftime("%Y%m%d")
    if me > today: me = today
    months.append((ms, me))
    d = nm

from src.models.moneyflow import RawMarginTotal
from src.models.market import RawStkFactor, RawStockWeekly, RawStockMonthly
from src.models.index import RawSwDaily
from src.models.ths import RawThsDaily

PHASE1 = {
    "margin_total": (lambda ms,me: pro.margin(start_date=ms, end_date=me), RawMarginTotal, ["trade_date","exchange_id"]),
    "sw_daily": (lambda ms,me: pro.sw_daily(start_date=ms, end_date=me), RawSwDaily, ["ts_code","trade_date"]),
    "ths_daily": (lambda ms,me: pro.ths_daily(start_date=ms, end_date=me), RawThsDaily, ["ts_code","trade_date"]),
}

for name, (fn, model, dedup) in PHASE1.items():
    total = 0
    print(f"🔄 {name} ...", flush=True)
    for i, (ms, me) in enumerate(months):
        try:
            df = fn(ms, me)
            if df is not None and not df.empty:
                recs = df.to_dict("records")
                # store
                written = _store(None, model, recs, dedup)
                total += written
        except:
            pass
        if (i+1) % 10 == 0:
            print(f"  [{ms[:6]}] {total:,d}", flush=True)
        time.sleep(0.35)
    print(f"  ✅ {name}: {total:,d}", flush=True)

# index_dailybasic (trade_date only, iterate days)
from src.models.market import RawIndexDailyBasic
dc = datetime(2020, 1, 1); ib_total = 0; ib_days = 0
print(f"🔄 index_dailybasic ...", flush=True)
while dc <= e:
    if dc.weekday() < 5:
        ds = dc.strftime("%Y%m%d")
        try:
            df = pro.index_dailybasic(trade_date=ds)
            if df is not None and not df.empty:
                recs = df.to_dict("records")
                ib_total += _store(None, RawIndexDailyBasic, recs, ["ts_code","trade_date"])
            ib_days += 1
        except: pass
        if ib_days % 200 == 0:
            print(f"  [{ds}] {ib_total:,d}", flush=True)
    dc += timedelta(days=1)
    time.sleep(0.35)
print(f"  ✅ index_dailybasic: {ib_total:,d}", flush=True)

# cn_ppi
from src.models.macro import RawCnPpi
cp_total = 0
print(f"🔄 cn_ppi ...", flush=True)
try:
    df = pro.cn_ppi(start_m="202001", end_m=today[:6])
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        cp_total = _store(None, RawCnPpi, recs, ["month"])
except: pass
print(f"  ✅ cn_ppi: {cp_total:,d}", flush=True)

# fund_basic
from src.models.fund import RawFundBasic
print(f"🔄 fund_basic ...", flush=True)
try:
    df = pro.fund_basic()
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        fb_total = _store(None, RawFundBasic, recs, ["ts_code"])
        print(f"  ✅ fund_basic: {fb_total:,d}", flush=True)
    else:
        print(f"  ✅ fund_basic: 0", flush=True)
except Exception as exc:
    print(f"  ⚠️ fund_basic: {exc}", flush=True)

# repurchase
from src.models.fundamental import RawRepurchase
print(f"🔄 repurchase ...", flush=True)
try:
    df = pro.repurchase()
    if df is not None and not df.empty:
        recs = df.to_dict("records")
        rp_total = _store(None, RawRepurchase, recs, ["ts_code","ann_date"])
        print(f"  ✅ repurchase: {rp_total:,d}", flush=True)
    else:
        print(f"  ✅ repurchase: 0", flush=True)
except Exception as exc:
    print(f"  ⚠️ repurchase: {exc}", flush=True)

print(f"\n✅ Phase 1 done\n")

# ═══════════════════════════════════════════════
# PHASE 2: Per-stock tables (top 500)
# ═══════════════════════════════════════════════
print("="*50)
print(f"PHASE 2: Per-stock tables ({len(target)} stocks)")
print("="*50)

from src.models.fundamental import RawBalanceSheet, RawCashFlow, RawFinancialIndicators, RawForecast, RawExpress
from src.models.corporate_action import RawDividend
from src.models.market import RawStkHolderNumber
from src.models.fundamental import RawStkHolderTop, RawStkHolderTrade
from src.models.market import RawBlockTrade

PER_TABLE = {
    "balance_sheet": (lambda code: pro.balancesheet(ts_code=code, start_date="20200101", end_date=today), RawBalanceSheet, ["ts_code","end_date","report_type"]),
    "cash_flow": (lambda code: pro.cashflow(ts_code=code, start_date="20200101", end_date=today), RawCashFlow, ["ts_code","end_date","report_type"]),
    "fina_indicator": (lambda code: pro.fina_indicator(ts_code=code, start_date="20200101", end_date=today), RawFinancialIndicators, ["ts_code","end_date"]),
    "forecast": (lambda code: pro.forecast(ts_code=code, start_date="20200101", end_date=today), RawForecast, ["ts_code","ann_date"]),
    "express": (lambda code: pro.express(ts_code=code, start_date="20200101", end_date=today), RawExpress, ["ts_code","ann_date"]),
    "dividend": (lambda code: pro.dividend(ts_code=code), RawDividend, ["ts_code","ex_date"]),
    "stk_holdernumber": (lambda code: pro.stk_holdernumber(ts_code=code, start_date="20200101", end_date=today), RawStkHolderNumber, ["ts_code","trade_date"]),
    "top10_holders": (lambda code: pro.top10_holders(ts_code=code), RawStkHolderTop, ["ts_code","end_date","holder_name"]),
    "stk_holdertrade": (lambda code: pro.stk_holdertrade(ts_code=code, start_date="20200101", end_date=today), RawStkHolderTrade, ["ts_code","ann_date","holder_name"]),
    "block_trade": (lambda code: pro.block_trade(ts_code=code, start_date="20200101", end_date=today), RawBlockTrade, ["ts_code","trade_date","buyer"]),
}

for table_name, (fn, model, dedup) in PER_TABLE.items():
    total = 0
    print(f"🔄 {table_name} ...", flush=True)
    for i, row in enumerate(target):
        code = row["ts_code"]
        try:
            df = fn(code)
            if df is not None and not df.empty:
                recs = df.to_dict("records")
                w = _store(None, model, recs, dedup)
                total += w
        except:
            pass
        if (i+1) % 50 == 0:
            print(f"  [{i+1}/{len(target)}] {total:,d}", flush=True)
        time.sleep(0.35)
    print(f"  ✅ {table_name}: {total:,d}", flush=True)

# stk_factor, weekly, monthly
for name, api_fn, model, dedup in [
    ("stk_factor", lambda code: pro.stk_factor(ts_code=code, start_date="20200101", end_date=today), RawStkFactor, ["ts_code","trade_date"]),
    ("weekly", lambda code: pro.weekly(ts_code=code, start_date="20200101", end_date=today), RawStockWeekly, ["ts_code","trade_date"]),
    ("monthly", lambda code: pro.monthly(ts_code=code, start_date="20200101", end_date=today), RawStockMonthly, ["ts_code","trade_date"]),
]:
    total = 0
    print(f"🔄 {name} ...", flush=True)
    for i, row in enumerate(target):
        code = row["ts_code"]
        try:
            df = api_fn(code)
            if df is not None and not df.empty:
                recs = df.to_dict("records")
                w = _store(None, model, recs, dedup)
                total += w
        except:
            pass
        if (i+1) % 50 == 0:
            print(f"  [{i+1}/{len(target)}] {total:,d}", flush=True)
        time.sleep(0.35)
    print(f"  ✅ {name}: {total:,d}", flush=True)

# fund_portfolio
from src.models.fund import RawFundPortfolio
print("🔄 fund_portfolio ...", flush=True)
fp_total = 0
for i, row in enumerate(target):
    code = row["ts_code"].replace(".SH",".OF").replace(".SZ",".OF")
    try:
        df = pro.fund_portfolio(ts_code=f"000001.OF" if i==0 else code)
        if df is not None and not df.empty:
            recs = df.to_dict("records")
            w = _store(None, RawFundPortfolio, recs, ["ts_code","end_date","symbol"])
            fp_total += w
    except: pass
    if (i+1) % 50 == 0:
        print(f"  [{i+1}/{len(target)}] {fp_total:,d}", flush=True)
    time.sleep(0.35)
print(f"  ✅ fund_portfolio: {fp_total:,d}", flush=True)

print(f"\n🎉 ALL DONE")
