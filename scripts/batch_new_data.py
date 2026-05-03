"""批量拉取新数据源落库 — 一次性导入"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=== 1. Tushare: bak_daily + stk_account_old ===")
from src.collectors.impl.bak_daily import BakDailyCollector
from src.collectors.impl.stk_account_old import StkAccountOldCollector

c = BakDailyCollector(os.getenv("TUSHARE_TOKEN"))
r = c.run()
print(f"  bak_daily: fetched={r['fetched']} written={r['written']} {r['status']}")

c2 = StkAccountOldCollector(os.getenv("TUSHARE_TOKEN"))
r2 = c2.run()
print(f"  stk_account_old: fetched={r2['fetched']} written={r2['written']} {r2['status']}")

print("\n=== 2. AKShare: cb_jsl + analyst ===")
time.sleep(1)
from src.collectors.impl.cb_jsl import CbJslCollector
from src.collectors.impl.analyst import AnalystCollector

c3 = CbJslCollector()
r3 = c3.run()
print(f"  cb_jsl: fetched={r3['fetched']} written={r3['written']} {r3['status']}")

time.sleep(0.5)
c4 = AnalystCollector()
r4 = c4.run(year="2025")
print(f"  analyst: fetched={r4['fetched']} written={r4['written']} {r4['status']}")

print("\n=== 3. AKShare: fund_flow + index_cons + hsgt_individual ===")
time.sleep(1)
from src.collectors.impl.fund_flow import FundFlowCollector
from src.collectors.impl.index_cons import IndexConsCollector
from src.collectors.impl.hsgt_individual import HsgtIndividualCollector

# Fund flow for a major stock
c5 = FundFlowCollector()
r5 = c5.run(stock="000001", market="sz")
print(f"  fund_flow (000001): fetched={r5['fetched']} written={r5['written']} {r5['status']}")

time.sleep(0.5)
# Index cons for major indices
c6 = IndexConsCollector()
for idx in ["000300", "000905", "000016"]:
    r6 = c6.run(index_code=idx)
    print(f"  index_cons ({idx}): fetched={r6['fetched']} written={r6['written']} {r6['status']}")
    time.sleep(0.5)

time.sleep(0.5)
# HSGT individual for a few stocks
c7 = HsgtIndividualCollector()
for sym in ["600519", "000858", "601318"]:
    r7 = c7.run(symbol=sym)
    print(f"  hsgt_individual ({sym}): fetched={r7['fetched']} written={r7['written']} {r7['status']}")
    time.sleep(0.3)

print("\n=== 4. AKShare: foreign_futures ===")
time.sleep(1)
from src.collectors.impl.foreign_futures import ForeignFuturesCollector

c8 = ForeignFuturesCollector()
futures_syms = ["GC", "SI", "HG", "NG", "CL", "OIL"]
futures_names = {"GC": "黄金", "SI": "白银", "HG": "铜", "NG": "天然气", "CL": "WTI", "OIL": "布伦特"}
for sym in futures_syms:
    r8 = c8.run(symbol=sym)
    print(f"  foreign_futures ({sym} {futures_names[sym]}): fetched={r8['fetched']} written={r8['written']} {r8['status']}")
    time.sleep(0.3)

print("\n=== DONE ===")
