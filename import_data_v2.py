"""
Quant Data Import Script v2
Direct imports using Tushare Pro API → PostgreSQL.
Simpler approach: use pd.to_sql with if_exists='append', skip-on-error.
"""

import os
import sys
import time
import datetime
from pathlib import Path
import calendar
import uuid

import pandas as pd
import tushare as ts
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from db.engine import get_engine

token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

CALL_COUNT = 0
RATE_LIMIT = 100

def rate_limit():
    global CALL_COUNT
    CALL_COUNT += 1
    if CALL_COUNT >= RATE_LIMIT:
        print(f"  [rate limit] sleeping 1s after {CALL_COUNT} calls...")
        time.sleep(1)
        CALL_COUNT = 0

def count_rows(engine, table):
    with engine.connect() as conn:
        r = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return r.scalar()

def insert_df(engine, table, df, batch_size=500):
    """Insert DataFrame into table with error handling."""
    if df is None or df.empty:
        return 0
    total = 0
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start+batch_size]
        # Remove columns not in the DB table
        with engine.connect() as conn:
            db_cols = set(c[0] for c in conn.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            )))
        keep_cols = [c for c in batch.columns if c in db_cols]
        batch = batch[keep_cols]
        
        for attempt in range(3):
            try:
                with engine.begin() as conn:
                    batch.to_sql(table, conn, if_exists='append', index=False)
                total += len(batch)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                else:
                    # Row-by-row fallback
                    for idx, (_, row) in enumerate(batch.iterrows()):
                        try:
                            with engine.begin() as conn:
                                pd.DataFrame([row]).to_sql(table, conn, if_exists='append', index=False)
                            total += 1
                        except Exception:
                            pass
    return total


# ═══════════════════════════════════════════
# Module 1: trade_cal → ref_trade_cal
# ═══════════════════════════════════════════
def import_trade_cal(engine):
    print("\n=== Module 1: ref_trade_cal (SSE Trade Calendar 1990-2026) ===")
    df = pro.trade_cal(exchange='SSE', start_date='19900101', end_date='20261231',
                       fields='exchange,cal_date,is_open,pretrade_date')
    rate_limit()
    print(f"  Fetched {len(df)} rows")
    df['cal_date'] = pd.to_datetime(df['cal_date'])
    df['pretrade_date'] = pd.to_datetime(df['pretrade_date'])
    rows = insert_df(engine, 'ref_trade_cal', df)
    print(f"  ✅ ref_trade_cal: {rows} rows written (total: {count_rows(engine, 'ref_trade_cal')})")


# ═══════════════════════════════════════════
# Module 2: stock_basic
# ═══════════════════════════════════════════
def import_stock_basic(engine):
    print("\n=== Module 2: ref_stock_basic + asset ===")
    
    # Fetch all stocks
    dfs = []
    for status in ['L', 'D']:
        df = pro.stock_basic(exchange='', list_status=status,
                             fields='ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs')
        rate_limit()
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset='ts_code')
    print(f"  Fetched {len(df)} stocks")
    
    # Convert dates
    for col in ['list_date', 'delist_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Insert ref_stock_basic directly
    df_stock = df[['ts_code', 'symbol', 'name', 'area', 'industry', 'market', 'list_date', 'delist_date', 'is_hs']].copy()
    
    # Create asset records
    now = datetime.datetime.now()
    asset_rows = []
    for _, row in df.iterrows():
        ts_c = str(row['ts_code'])
        exchange = ''
        if ts_c.endswith('.SZ'): exchange = 'SZSE'
        elif ts_c.endswith('.SH'): exchange = 'SSE'
        elif ts_c.endswith('.BJ'): exchange = 'BSE'
        aid = uuid.uuid4()
        vfrom = row.get('list_date') or now
        vto = row.get('delist_date') or datetime.datetime(2099, 12, 31)
        asset_rows.append([aid, row['symbol'], exchange, 'stock', row['name'], '', ts_c, 'active', vfrom, vto, None])
    
    # Insert asset in batches
    asset_df = pd.DataFrame(asset_rows, columns=['id', 'symbol', 'exchange', 'asset_type', 'name', 'isin', 'source_id', 'status', 'valid_from', 'valid_to', 'extra'])
    
    # Insert ref_stock_basic (has unique on ts_code, so ON CONFLICT works naturally)
    print(f"  Inserting ref_stock_basic ({len(df_stock)} rows)...")
    r1 = insert_df(engine, 'ref_stock_basic', df_stock)
    print(f"  ✅ ref_stock_basic: {r1} rows (total: {count_rows(engine, 'ref_stock_basic')})")
    
    print(f"  Inserting asset ({len(asset_df)} rows)...")
    r2 = insert_df(engine, 'asset', asset_df)
    print(f"  ✅ asset: {r2} rows (total: {count_rows(engine, 'asset')})")


# ═══════════════════════════════════════════
# Module 3: daily_basic
# ═══════════════════════════════════════════
def import_daily_basic(engine):
    print("\n=== Module 3: raw_daily_basic (PE/PB/换手率) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4:
                continue
            last_day = calendar.monthrange(year, month)[1]
            sd = f"{year}{month:02d}01"
            ed = f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.daily_basic(ts_code='', trade_date='',
                                     start_date=sd, end_date=ed,
                                     fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_mv,circ_mv,total_share,float_share,free_share')
                rate_limit()
                if df is not None and not df.empty:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    rows = insert_df(engine, 'raw_daily_basic', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_daily_basic: {total} rows (total: {count_rows(engine, 'raw_daily_basic')})")


# ═══════════════════════════════════════════
# Module 4: index_daily
# ═══════════════════════════════════════════
def import_index_daily(engine):
    print("\n=== Module 4: raw_index_daily (9 major indices) ===")
    indices = {
        '000001.SH': '上证指数', '399001.SZ': '深证成指', '399006.SZ': '创业板指',
        '000688.SH': '科创50', '000300.SH': '沪深300', '000016.SH': '上证50',
        '000905.SH': '中证500', '000852.SH': '中证1000', '399303.SZ': '国证2000',
    }
    total = 0
    for code, name in indices.items():
        try:
            df = pro.index_daily(ts_code=code, start_date='20240101', end_date='20260430',
                                 fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
            rate_limit()
            if df is not None and not df.empty:
                rows = insert_df(engine, 'raw_index_daily', df)
                total += rows
                print(f"  {name}: {len(df)} -> {rows}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  {name}: ERROR {e}")
    print(f"  ✅ raw_index_daily: {total} rows (total: {count_rows(engine, 'raw_index_daily')})")


# ═══════════════════════════════════════════
# Module 5: moneyflow
# ═══════════════════════════════════════════
def import_moneyflow(engine):
    print("\n=== Module 5: raw_moneyflow (个股资金流向) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.moneyflow(trade_date='', start_date=sd, end_date=ed,
                                   fields='ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,net_mf_vol,net_mf_amount')
                rate_limit()
                if df is not None and not df.empty:
                    rows = insert_df(engine, 'raw_moneyflow', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_moneyflow: {total} rows (total: {count_rows(engine, 'raw_moneyflow')})")


# ═══════════════════════════════════════════
# Module 6: moneyflow_mkt_dc
# ═══════════════════════════════════════════
def import_moneyflow_mkt(engine):
    print("\n=== Module 6: raw_moneyflow_mkt_dc (大盘资金流) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.moneyflow_mkt_dc(start_date=sd, end_date=ed,
                                          fields='trade_date,s_d_value,m_d_value,l_d_value,el_d_value,net_main,net_main_pct')
                rate_limit()
                if df is not None and not df.empty:
                    rows = insert_df(engine, 'raw_moneyflow_mkt_dc', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_moneyflow_mkt_dc: {total} rows (total: {count_rows(engine, 'raw_moneyflow_mkt_dc')})")


# ═══════════════════════════════════════════
# Module 7: top_inst
# ═══════════════════════════════════════════
def import_top_inst(engine):
    print("\n=== Module 7: raw_top_inst (龙虎榜机构) ===")
    total = 0
    for year in [2024, 2025]:
        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.top_inst(trade_date='', start_date=sd, end_date=ed,
                                  fields='trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy,side,reason')
                rate_limit()
                if df is not None and not df.empty:
                    rows = insert_df(engine, 'raw_top_inst', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_top_inst: {total} rows (total: {count_rows(engine, 'raw_top_inst')})")


# ═══════════════════════════════════════════
# Module 8: margin
# ═══════════════════════════════════════════
def import_margin(engine):
    print("\n=== Module 8: raw_margin_detail (融资融券) ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.margin(start_date=sd, end_date=ed,
                                fields='trade_date,ts_code,name,rzye,rzmre,rzche,rqye,rqmcl,rzrqye')
                rate_limit()
                if df is not None and not df.empty:
                    rows = insert_df(engine, 'raw_margin_detail', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_margin_detail: {total} rows (total: {count_rows(engine, 'raw_margin_detail')})")


# ═══════════════════════════════════════════
# Module 9: shibor
# ═══════════════════════════════════════════
def import_shibor(engine):
    print("\n=== Module 9: raw_shibor (2020-2026) ===")
    total = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.shibor(start_date=sd, end_date=ed,
                                fields='date,on_rate,on_bid,w1_rate,w1_bid,w2_rate,w2_bid,m1_rate,m3_rate,m6_rate,m9_rate,y1_rate')
                rate_limit()
                if df is not None and not df.empty:
                    rows = insert_df(engine, 'raw_shibor', df)
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_shibor: {total} rows (total: {count_rows(engine, 'raw_shibor')})")


# ═══════════════════════════════════════════
# Module 10: Macro
# ═══════════════════════════════════════════
def import_macro(engine):
    print("\n=== Module 10: Macro ===")
    
    print("  CPI...")
    cpi_total = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cpi(start_period=period, end_period=period,
                             fields='month,nt_val,nt_yoy,nt_mom,nt_accu')
                rate_limit()
                if df is not None and not df.empty:
                    cpi_total += insert_df(engine, 'raw_cn_cpi', df)
                time.sleep(0.2)
            except: pass
    print(f"    CPI: {cpi_total}")
    
    print("  GDP...")
    gdp_total = 0
    for year in range(2020, 2027):
        for q in range(1, 5):
            if year == 2026 and q > 1: continue
            quarter = f"{year}q{q}"
            try:
                df = pro.cn_gdp(quarter=quarter, fields='quarter,gdp,gdp_yoy,pi,pi_yoy,si,si_yoy,ti,ti_yoy')
                rate_limit()
                if df is not None and not df.empty:
                    gdp_total += insert_df(engine, 'raw_cn_gdp', df)
                time.sleep(0.2)
            except: pass
    print(f"    GDP: {gdp_total}")
    
    print("  PMI...")
    pmi_total = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cn_pmi(start_period=period, end_period=period,
                                fields='month,pmi,pmi_yoy,pmi_month')
                rate_limit()
                if df is not None and not df.empty:
                    pmi_total += insert_df(engine, 'raw_cn_pmi', df)
                time.sleep(0.2)
            except: pass
    print(f"    PMI: {pmi_total}")
    
    print("  Money Supply...")
    ms_total = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cn_m(start_period=period, end_period=period,
                              fields='month,m0,m0_yoy,m1,m1_yoy,m2,m2_yoy')
                rate_limit()
                if df is not None and not df.empty:
                    ms_total += insert_df(engine, 'raw_cn_money_supply', df)
                time.sleep(0.2)
            except: pass
    print(f"    Money Supply: {ms_total}")
    
    totals = {k: count_rows(engine, k) for k in ['raw_cn_cpi', 'raw_cn_gdp', 'raw_cn_pmi', 'raw_cn_money_supply']}
    print(f"  ✅ Macro totals: {totals}")


# ═══════════════════════════════════════════
# Module 11: consultations
# ═══════════════════════════════════════════
def import_consultations(engine):
    print("\n=== Module 11: raw_consultation (快讯) ===")
    total = 0
    today = datetime.date.today()
    for days_ago in range(30):
        d = today - datetime.timedelta(days=days_ago)
        ds = d.strftime('%Y%m%d')
        try:
            df = pro.news(src='', start_date=ds, end_date=ds,
                          fields='datetime,content,title,channels')
            rate_limit()
            if df is not None and not df.empty:
                df = df.rename(columns={'datetime': 'pub_time', 'channels': 'source'})
                df['news_id'] = [f"news_{ds}_{i}" for i in range(len(df))]
                df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                cols = ['news_id', 'title', 'content', 'source', 'pub_time']
                keep = [c for c in cols if c in df.columns]
                rows = insert_df(engine, 'raw_consultation', df[keep])
                total += rows
                print(f"  {ds}: {len(df)} -> {rows}")
            time.sleep(0.3)
        except: pass
    print(f"  ✅ raw_consultation: {total} rows (total: {count_rows(engine, 'raw_consultation')})")


# ═══════════════════════════════════════════
# Module 12: major_news
# ═══════════════════════════════════════════
def import_major_news(engine):
    print("\n=== Module 12: raw_major_news (重大新闻) ===")
    total = 0
    for year in [2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.major_news(start_date=sd, end_date=ed,
                                    fields='datetime,content,title,channels')
                rate_limit()
                if df is not None and not df.empty:
                    df = df.rename(columns={'datetime': 'pub_time', 'channels': 'source'})
                    df['news_id'] = [f"major_{year}{month:02d}_{i}" for i in range(len(df))]
                    df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                    cols = ['news_id', 'title', 'content', 'source', 'pub_time']
                    keep = [c for c in cols if c in df.columns]
                    rows = insert_df(engine, 'raw_major_news', df[keep])
                    total += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: {e}")
    print(f"  ✅ raw_major_news: {total} rows (total: {count_rows(engine, 'raw_major_news')})")


# ═══════════════════════════════════════════
# Module 13: concept
# ═══════════════════════════════════════════
def import_concept(engine):
    print("\n=== Module 13: ref_concept + ref_concept_detail ===")
    
    print("  Concept list...")
    try:
        df = pro.concept()
        rate_limit()
        if df is not None and not df.empty:
            df = df.rename(columns={'code': 'code', 'name': 'name', 'src': 'src'})
            r = insert_df(engine, 'ref_concept', df)
            print(f"  ref_concept: {r} rows (total: {count_rows(engine, 'ref_concept')})")
    except Exception as e:
        print(f"  concept list: {e}")
    
    print("  Concept details (first 200)...")
    with engine.connect() as conn:
        codes = [r[0] for r in conn.execute(text("SELECT code FROM ref_concept LIMIT 200"))]
    
    total = 0
    for code in codes:
        try:
            df = pro.concept_detail(id=code, fields='code,name,ts_code,ts_name,weight')
            rate_limit()
            if df is not None and not df.empty:
                df = df.rename(columns={'code': 'concept_code', 'name': 'concept_name', 'ts_name': 'name'})
                total += insert_df(engine, 'ref_concept_detail', df)
            time.sleep(0.2)
        except: pass
    print(f"  ✅ ref_concept_detail: {total} rows (total: {count_rows(engine, 'ref_concept_detail')})")


# ═══════════════════════════════════════════
# Module 14: adj_factor
# ═══════════════════════════════════════════
def import_adj_factor(engine):
    print("\n=== Module 14: ref_adj_factor (first 200 stocks, full history) ===")
    with engine.connect() as conn:
        codes = [r[0] for r in conn.execute(text("SELECT ts_code FROM ref_stock_basic LIMIT 200"))]
    
    total = 0
    for i, ts_code in enumerate(codes):
        try:
            df = pro.adj_factor(ts_code=ts_code, fields='ts_code,trade_date,adj_factor')
            rate_limit()
            if df is not None and not df.empty:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                total += insert_df(engine, 'ref_adj_factor', df)
            if i % 20 == 0 and i > 0:
                print(f"  {i}/{len(codes)} processed...")
            time.sleep(0.1)
        except Exception as e:
            print(f"  {ts_code}: {e}")
    print(f"  ✅ ref_adj_factor: {total} rows (total: {count_rows(engine, 'ref_adj_factor')})")


# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════
if __name__ == '__main__':
    engine = get_engine()
    print("=" * 60)
    print("Quant Data Import v2 - Starting")
    print(f"Time: {datetime.datetime.now()}")
    print("=" * 60)
    
    import_trade_cal(engine)
    import_stock_basic(engine)
    import_daily_basic(engine)
    import_index_daily(engine)
    import_moneyflow(engine)
    import_moneyflow_mkt(engine)
    import_top_inst(engine)
    import_margin(engine)
    import_shibor(engine)
    import_macro(engine)
    import_consultations(engine)
    import_major_news(engine)
    import_concept(engine)
    import_adj_factor(engine)
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    with engine.connect() as conn:
        r = conn.execute(text("SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' ORDER BY n_live_tup DESC"))
        for row in r:
            print(f"  {row[0]:40s} {row[1]}")
    print(f"\nDone: {datetime.datetime.now()}")
