"""批量拉取所有缺失数据：stk_limit, moneyflow, macro, futures, fund"""
import json
from src.config.settings import settings
import tushare as ts
ts.set_token(settings.tushare.token)
pro = ts.pro_api()

from src.db.session import db_session
from src.models.sentiment import RawStkLimit
from src.models.moneyflow import RawMoneyflow, RawHsgtTop10, RawGgtTop10, RawMarginDetail
from src.models.macro import RawCnCpi, RawCnPmi, RawCnGdp, RawCnMoneySupply, RawShibor
from src.models.futures import RawFutDaily
from src.models.fund import RawFundDaily

def _f(v):
    if v is None or v == '': return None
    try: return float(v)
    except: return None

def safe_str(v):
    if v is None: return ''
    return str(v)

td = "20260427"

# === 1. stk_limit ===
print("=== stk_limit ===")
try:
    df = pro.stk_limit(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawStkLimit).filter_by(
                ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date)
            ).first()
            if not existing:
                session.add(RawStkLimit(
                    trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code),
                    pre_close=_f(row.get('pre_close')), up_limit=_f(row.get('up_limit')),
                    down_limit=_f(row.get('down_limit')),
                    raw_json=json.dumps(dict(row), ensure_ascii=False, default=str),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 2. moneyflow ===
print("\n=== moneyflow ===")
try:
    df = pro.moneyflow(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawMoneyflow).filter_by(
                ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date)
            ).first()
            if not existing:
                session.add(RawMoneyflow(
                    ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date),
                    buy_sm_vol=_f(row.get('buy_sm_vol')), buy_sm_amount=_f(row.get('buy_sm_amount')),
                    sell_sm_vol=_f(row.get('sell_sm_vol')), sell_sm_amount=_f(row.get('sell_sm_amount')),
                    buy_md_vol=_f(row.get('buy_md_vol')), buy_md_amount=_f(row.get('buy_md_amount')),
                    sell_md_vol=_f(row.get('sell_md_vol')), sell_md_amount=_f(row.get('sell_md_amount')),
                    buy_lg_vol=_f(row.get('buy_lg_vol')), buy_lg_amount=_f(row.get('buy_lg_amount')),
                    sell_lg_vol=_f(row.get('sell_lg_vol')), sell_lg_amount=_f(row.get('sell_lg_amount')),
                    buy_elg_vol=_f(row.get('buy_elg_vol')), buy_elg_amount=_f(row.get('buy_elg_amount')),
                    sell_elg_vol=_f(row.get('sell_elg_vol')), sell_elg_amount=_f(row.get('sell_elg_amount')),
                    net_mf_vol=_f(row.get('net_mf_vol')), net_mf_amount=_f(row.get('net_mf_amount')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 3. hsgt_top10 ===
print("\n=== hsgt_top10 ===")
try:
    df = pro.hsgt_top10(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawHsgtTop10).filter_by(
                trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code)
            ).first()
            if not existing:
                session.add(RawHsgtTop10(
                    trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code),
                    name=safe_str(row.get('name')), close=_f(row.get('close')),
                    pct_change=_f(row.get('pct_change')), rank=safe_str(row.get('rank')),
                    buy_amount=_f(row.get('buy_amount')), sell_amount=_f(row.get('sell_amount')),
                    net_amount=_f(row.get('net_amount')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 4. ggt_top10 ===
print("\n=== ggt_top10 ===")
try:
    df = pro.ggt_top10(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawGgtTop10).filter_by(
                trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code)
            ).first()
            if not existing:
                session.add(RawGgtTop10(
                    trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code),
                    name=safe_str(row.get('name')), close=_f(row.get('close')),
                    pct_change=_f(row.get('pct_change')), rank=safe_str(row.get('rank')),
                    buy_amount=_f(row.get('buy_amount')), sell_amount=_f(row.get('sell_amount')),
                    net_amount=_f(row.get('net_amount')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 5. margin_detail ===
print("\n=== margin_detail ===")
try:
    df = pro.margin_detail(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawMarginDetail).filter_by(
                trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code)
            ).first()
            if not existing:
                session.add(RawMarginDetail(
                    trade_date=safe_str(row.trade_date), ts_code=safe_str(row.ts_code),
                    name=safe_str(row.get('name')),
                    rzye=_f(row.get('rzye')), rzmre=_f(row.get('rzmre')),
                    rzche=_f(row.get('rzche')), rqye=_f(row.get('rqye')),
                    rqmcl=_f(row.get('rqmcl')), rzrqye=_f(row.get('rzrqye')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 6. 宏观数据 ===
print("\n=== 宏观: CPI ===")
try:
    df = pro.cn_cpi()
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawCnCpi).filter_by(month=safe_str(row.month)).first()
            if not existing:
                session.add(RawCnCpi(
                    month=safe_str(row.month), nt_val=_f(row.get('nt_val')),
                    nt_yoy=_f(row.get('nt_yoy')), nt_mom=_f(row.get('nt_mom')),
                    nt_accu=_f(row.get('nt_accu')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 宏观: PMI ===")
try:
    df = pro.cn_pmi()
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawCnPmi).filter_by(month=safe_str(row.month)).first()
            if not existing:
                session.add(RawCnPmi(month=safe_str(row.month), pmi=_f(row.get('pmi'))))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 宏观: GDP ===")
try:
    df = pro.cn_gdp()
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawCnGdp).filter_by(quarter=safe_str(row.quarter)).first()
            if not existing:
                session.add(RawCnGdp(quarter=safe_str(row.quarter), gdp=_f(row.get('gdp')), gdp_yoy=_f(row.get('gdp_yoy'))))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 宏观: M2 ===")
try:
    df = pro.cn_m()
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawCnMoneySupply).filter_by(month=safe_str(row.month)).first()
            if not existing:
                session.add(RawCnMoneySupply(month=safe_str(row.month), m2=_f(row.get('m2')), m2_yoy=_f(row.get('m2_yoy'))))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== 宏观: Shibor ===")
try:
    df = pro.shibor(start_date='20250101')
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawShibor).filter_by(date=safe_str(row.date)).first()
            if not existing:
                session.add(RawShibor(
                    date=safe_str(row.date), on_rate=_f(row.get('on')), on_bid=_f(row.get('on_bid')),
                    w1_rate=_f(row.get('1w')), w1_bid=_f(row.get('1w_bid')),
                    w2_rate=_f(row.get('2w')),  m1_rate=_f(row.get('1m')),
                    m3_rate=_f(row.get('3m')), m6_rate=_f(row.get('6m')),
                    m9_rate=_f(row.get('9m')), y1_rate=_f(row.get('1y')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 7. 期货 ===
print("\n=== futures ===")
try:
    df = pro.fut_daily(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawFutDaily).filter_by(
                ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date)
            ).first()
            if not existing:
                session.add(RawFutDaily(
                    ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date),
                    pre_close=_f(row.get('pre_close')), pre_settle=_f(row.get('pre_settle')),
                    open=_f(row.get('open')), high=_f(row.get('high')), low=_f(row.get('low')),
                    close=_f(row.get('close')), settle=_f(row.get('settle')),
                    change1=_f(row.get('change1')), change2=_f(row.get('change2')),
                    vol=_f(row.get('vol')), amount=_f(row.get('amount')),
                    oi=_f(row.get('oi')), oi_chg=_f(row.get('oi_chg')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

# === 8. 基金/ETF ===
print("\n=== fund ===")
try:
    df = pro.fund_daily(trade_date=td)
    print(f"Fetched: {len(df)}")
    written = 0
    with db_session() as session:
        for _, row in df.iterrows():
            existing = session.query(RawFundDaily).filter_by(
                ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date)
            ).first()
            if not existing:
                session.add(RawFundDaily(
                    ts_code=safe_str(row.ts_code), trade_date=safe_str(row.trade_date),
                    open=_f(row.get('open')), high=_f(row.get('high')), low=_f(row.get('low')),
                    close=_f(row.get('close')), pre_close=_f(row.get('pre_close')),
                    change=_f(row.get('change')), pct_chg=_f(row.get('pct_chg')),
                    vol=_f(row.get('vol')), amount=_f(row.get('amount')),
                ))
                written += 1
    print(f"Written: {written}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== ALL DONE ===")
