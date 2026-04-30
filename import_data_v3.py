"""
Quant Data Import v3 - Using PostgreSQL COPY for fast, type-safe inserts.
"""

import sys, os, time, datetime, uuid, json, calendar
import pandas as pd
import tushare as ts
from sqlalchemy import text
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from db.engine import get_engine

engine = get_engine()
pro = ts.pro_api(os.getenv('TUSHARE_TOKEN'))
CALL_COUNT = 0

def rl():
    global CALL_COUNT
    CALL_COUNT += 1
    if CALL_COUNT >= 100:
        print("  [rate limit] sleeping 1s...")
        time.sleep(1)
        CALL_COUNT = 0

def copy_into(conn, table, df, batch=5000):
    """COPY-based insert with type handling."""
    if df is None or df.empty:
        return 0
    
    db_cols = set(r[0] for r in conn.execute(text(
        f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")))
    keep = [c for c in df.columns if c in db_cols]
    if not keep:
        return 0
    df = df[keep]
    
    raw_conn = conn.connection.driver_connection
    cursor = raw_conn.cursor()
    total = 0
    
    for start in range(0, len(df), batch):
        chunk = df.iloc[start:start+batch]
        buf = StringIO()
        for _, row in chunk.iterrows():
            vals = []
            for c in chunk.columns:
                v = row[c]
                if pd.isna(v) or v is None:
                    vals.append('\\N')
                elif isinstance(v, bool):
                    vals.append('t' if v else 'f')
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                elif isinstance(v, (datetime.datetime, pd.Timestamp)):
                    vals.append(pd.Timestamp(v).strftime('%Y-%m-%d %H:%M:%S'))
                elif isinstance(v, uuid.UUID):
                    vals.append(str(v))
                else:
                    s = str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
                    vals.append(s)
            buf.write('\t'.join(vals) + '\n')
        buf.seek(0)
        try:
            cursor.copy_from(buf, table, columns=list(chunk.columns), sep='\t', null='\\N')
            total += len(chunk)
        except Exception as e:
            print(f"  [WARN] COPY failed: {str(e)[:120]}")
    return total

def count_rows(table):
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


# ═══════════════════════════════════════════
# Module 3: daily_basic
# ═══════════════════════════════════════════
def import_daily_basic():
    print("\n=== Module 3: raw_daily_basic ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4:
                continue
            last_day = calendar.monthrange(year, month)[1]
            sd = f"{year}{month:02d}01"
            ed = f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.daily_basic(ts_code='', trade_date='', start_date=sd, end_date=ed,
                                     fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_mv,circ_mv,total_share,float_share,free_share')
                rl()
                if df is not None and not df.empty:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_daily_basic', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
                time.sleep(0.3)
    print(f"  ✅ raw_daily_basic: {total} rows (total: {count_rows('raw_daily_basic')})")


# ═══════════════════════════════════════════
# Module 4: index_daily
# ═══════════════════════════════════════════
def import_index_daily():
    print("\n=== Module 4: raw_index_daily ===")
    indices = [
        '000001.SH', '399001.SZ', '399006.SZ', '000688.SH',
        '000300.SH', '000016.SH', '000905.SH', '000852.SH', '399303.SZ'
    ]
    names = ['上证指数','深证成指','创业板指','科创50','沪深300','上证50','中证500','中证1000','国证2000']
    total = 0
    for code, name in zip(indices, names):
        try:
            df = pro.index_daily(ts_code=code, start_date='20240101', end_date='20260430',
                                 fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
            rl()
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    r = copy_into(conn, 'raw_index_daily', df)
                total += r
                print(f"  {name}: {len(df)} -> {r}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  {name}: ERROR {e}")
    print(f"  ✅ raw_index_daily: {total} rows (total: {count_rows('raw_index_daily')})")


# ═══════════════════════════════════════════
# Module 5: moneyflow
# ═══════════════════════════════════════════
def import_moneyflow():
    print("\n=== Module 5: raw_moneyflow ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.moneyflow(trade_date='', start_date=sd, end_date=ed,
                                   fields='ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,net_mf_vol,net_mf_amount')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_moneyflow', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_moneyflow: {total} rows (total: {count_rows('raw_moneyflow')})")


# ═══════════════════════════════════════════
# Module 6: moneyflow_mkt_dc
# ═══════════════════════════════════════════
def import_moneyflow_mkt():
    print("\n=== Module 6: raw_moneyflow_mkt_dc ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.moneyflow_mkt_dc(start_date=sd, end_date=ed,
                                          fields='trade_date,s_d_value,m_d_value,l_d_value,el_d_value,net_main,net_main_pct')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_moneyflow_mkt_dc', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_moneyflow_mkt_dc: {total} rows (total: {count_rows('raw_moneyflow_mkt_dc')})")


# ═══════════════════════════════════════════
# Module 7: top_inst
# ═══════════════════════════════════════════
def import_top_inst():
    print("\n=== Module 7: raw_top_inst ===")
    total = 0
    for year in [2024, 2025]:
        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.top_inst(trade_date='', start_date=sd, end_date=ed,
                                  fields='trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy,side,reason')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_top_inst', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_top_inst: {total} rows (total: {count_rows('raw_top_inst')})")


# ═══════════════════════════════════════════
# Module 8: margin
# ═══════════════════════════════════════════
def import_margin():
    print("\n=== Module 8: raw_margin_detail ===")
    total = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.margin(start_date=sd, end_date=ed,
                                fields='trade_date,ts_code,name,rzye,rzmre,rzche,rqye,rqmcl,rzrqye')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_margin_detail', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_margin_detail: {total} rows (total: {count_rows('raw_margin_detail')})")


# ═══════════════════════════════════════════
# Module 9: shibor
# ═══════════════════════════════════════════
def import_shibor():
    print("\n=== Module 9: raw_shibor ===")
    total = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.shibor(start_date=sd, end_date=ed,
                                fields='date,on_rate,on_bid,w1_rate,w1_bid,w2_rate,w2_bid,m1_rate,m3_rate,m6_rate,m9_rate,y1_rate')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_shibor', df)
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    print(f"  ✅ raw_shibor: {total} rows (total: {count_rows('raw_shibor')})")


# ═══════════════════════════════════════════
# Module 10: Macro
# ═══════════════════════════════════════════
def import_macro():
    print("\n=== Module 10: Macro ===")
    
    print("  CPI...")
    cpi_t = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cpi(start_period=period, end_period=period, fields='month,nt_val,nt_yoy,nt_mom,nt_accu')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        cpi_t += copy_into(conn, 'raw_cn_cpi', df)
                time.sleep(0.2)
            except: pass
    
    print("  GDP...")
    gdp_t = 0
    for year in range(2020, 2027):
        for q in range(1, 5):
            if year == 2026 and q > 1: continue
            try:
                df = pro.cn_gdp(quarter=f"{year}q{q}", fields='quarter,gdp,gdp_yoy,pi,pi_yoy,si,si_yoy,ti,ti_yoy')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        gdp_t += copy_into(conn, 'raw_cn_gdp', df)
                time.sleep(0.2)
            except: pass
    
    print("  PMI...")
    pmi_t = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cn_pmi(start_period=period, end_period=period, fields='month,pmi,pmi_yoy,pmi_month')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        pmi_t += copy_into(conn, 'raw_cn_pmi', df)
                time.sleep(0.2)
            except: pass
    
    print("  Money Supply...")
    ms_t = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            period = f"{year}{month:02d}"
            try:
                df = pro.cn_m(start_period=period, end_period=period, fields='month,m0,m0_yoy,m1,m1_yoy,m2,m2_yoy')
                rl()
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        ms_t += copy_into(conn, 'raw_cn_money_supply', df)
                time.sleep(0.2)
            except: pass
    
    totals = {k: count_rows(k) for k in ['raw_cn_cpi','raw_cn_gdp','raw_cn_pmi','raw_cn_money_supply']}
    print(f"  CPI={cpi_t}, GDP={gdp_t}, PMI={pmi_t}, MSupply={ms_t}")
    print(f"  ✅ Macro totals: {totals}")


# ═══════════════════════════════════════════
# Module 11: consultations
# ═══════════════════════════════════════════
def import_consultations():
    print("\n=== Module 11: raw_consultation ===")
    total = 0
    today = datetime.date.today()
    for days_ago in range(30):
        d = today - datetime.timedelta(days=days_ago)
        ds = d.strftime('%Y%m%d')
        try:
            df = pro.news(src='', start_date=ds, end_date=ds, fields='datetime,content,title,channels')
            rl()
            if df is not None and not df.empty:
                df = df.rename(columns={'datetime': 'pub_time', 'channels': 'source'})
                df['news_id'] = [f"news_{ds}_{i}" for i in range(len(df))]
                df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                keep = [c for c in ['news_id','title','content','source','pub_time'] if c in df.columns]
                with engine.begin() as conn:
                    r = copy_into(conn, 'raw_consultation', df[keep])
                total += r
                print(f"  {ds}: {len(df)} -> {r}")
            time.sleep(0.3)
        except: pass
    print(f"  ✅ raw_consultation: {total} rows (total: {count_rows('raw_consultation')})")


# ═══════════════════════════════════════════
# Module 12: major_news
# ═══════════════════════════════════════════
def import_major_news():
    print("\n=== Module 12: raw_major_news ===")
    total = 0
    for year in [2025, 2026]:
        for month in range(1, 13):
            if year == 2026 and month > 4: continue
            last_day = calendar.monthrange(year, month)[1]
            sd, ed = f"{year}{month:02d}01", f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.major_news(start_date=sd, end_date=ed, fields='datetime,content,title,channels')
                rl()
                if df is not None and not df.empty:
                    df = df.rename(columns={'datetime': 'pub_time', 'channels': 'source'})
                    df['news_id'] = [f"major_{year}{month:02d}_{i}" for i in range(len(df))]
                    df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                    keep = [c for c in ['news_id','title','content','source','pub_time'] if c in df.columns]
                    with engine.begin() as conn:
                        r = copy_into(conn, 'raw_major_news', df[keep])
                    total += r
                    print(f"  {year}-{month:02d}: {len(df)} -> {r}")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: {e}")
    print(f"  ✅ raw_major_news: {total} rows (total: {count_rows('raw_major_news')})")


# ═══════════════════════════════════════════
# Module 13: concept
# ═══════════════════════════════════════════
def import_concept():
    print("\n=== Module 13: ref_concept + ref_concept_detail ===")
    
    print("  Concept list...")
    try:
        df = pro.concept()
        rl()
        if df is not None and not df.empty:
            with engine.begin() as conn:
                r = copy_into(conn, 'ref_concept', df)
            print(f"  ref_concept: {r} rows (total: {count_rows('ref_concept')})")
    except Exception as e:
        print(f"  concept list: {e}")
    
    print("  Concept details (first 200)...")
    with engine.connect() as conn:
        codes = [r[0] for r in conn.execute(text("SELECT code FROM ref_concept LIMIT 200"))]
    
    total = 0
    for code in codes:
        try:
            df = pro.concept_detail(id=code, fields='code,name,ts_code,ts_name,weight')
            rl()
            if df is not None and not df.empty:
                df = df.rename(columns={'code': 'concept_code', 'name': 'concept_name', 'ts_name': 'name'})
                with engine.begin() as conn:
                    total += copy_into(conn, 'ref_concept_detail', df)
            time.sleep(0.2)
        except: pass
    print(f"  ✅ ref_concept_detail: {total} rows (total: {count_rows('ref_concept_detail')})")


# ═══════════════════════════════════════════
# Module 14: adj_factor
# ═══════════════════════════════════════════
def import_adj_factor():
    print("\n=== Module 14: ref_adj_factor (first 200 stocks) ===")
    with engine.connect() as conn:
        codes = [r[0] for r in conn.execute(text("SELECT ts_code FROM ref_stock_basic LIMIT 200"))]
    
    total = 0
    for i, ts_code in enumerate(codes):
        try:
            df = pro.adj_factor(ts_code=ts_code, fields='ts_code,trade_date,adj_factor')
            rl()
            if df is not None and not df.empty:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                with engine.begin() as conn:
                    total += copy_into(conn, 'ref_adj_factor', df)
            if i % 20 == 0 and i > 0:
                print(f"  {i}/{len(codes)} processed...")
            time.sleep(0.1)
        except Exception as e:
            print(f"  {ts_code}: {e}")
    print(f"  ✅ ref_adj_factor: {total} rows (total: {count_rows('ref_adj_factor')})")


# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print(f"Quant Data Import v3 - Starting at {datetime.datetime.now()}")
    print("=" * 60)
    
    import_daily_basic()
    import_index_daily()
    import_moneyflow()
    import_moneyflow_mkt()
    import_top_inst()
    import_margin()
    import_shibor()
    import_macro()
    import_consultations()
    import_major_news()
    import_concept()
    import_adj_factor()
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    with engine.connect() as conn:
        r = conn.execute(text("SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' ORDER BY n_live_tup DESC"))
        for row in r:
            print(f"  {row[0]:40s} {row[1]}")
    print(f"\nDone: {datetime.datetime.now()}")
