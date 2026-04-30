"""
Quant Data Import Script
Direct imports using Tushare Pro API → PostgreSQL.
Skips the existing collector classes (buggy) and uses raw inserts.
"""

import os
import sys
import time
import datetime
from pathlib import Path

import pandas as pd
import tushare as ts
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Load env
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from db.engine import get_engine

# Init Tushare
token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# Rate limiting
CALL_COUNT = 0
RATE_LIMIT = 100

def rate_limit():
    global CALL_COUNT
    CALL_COUNT += 1
    if CALL_COUNT >= RATE_LIMIT:
        print(f"  [rate limit] sleeping 1s after {CALL_COUNT} calls...")
        time.sleep(1)
        CALL_COUNT = 0

def safe_insert(engine, table, df, conflict_cols=None, batch_size=2000):
    """Insert DataFrame into table with ON CONFLICT DO NOTHING where possible."""
    if df is None or df.empty:
        return 0
    total = 0
    with engine.begin() as conn:
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start+batch_size]
            # Use to_sql with method='multi' for multi-row insert
            # Then catch unique violations gracefully
            try:
                if conflict_cols:
                    # Build insert statement manually to support ON CONFLICT
                    from sqlalchemy import Table, MetaData
                    meta = MetaData()
                    # Reflect just the target table
                    tbl = Table(table, meta, autoload_with=engine, keep_existing=True)
                    # Get column list from db table
                    col_names = [c.name for c in tbl.columns if c.name in batch.columns]
                    if not col_names:
                        # fallback
                        batch.to_sql(table, conn, if_exists='append', method='multi', index=False)
                        total += len(batch)
                    else:
                        stmt = tbl.insert()
                        # Build values
                        for _, row in batch.iterrows():
                            vals = {c: row[c] if pd.notna(row[c]) else None for c in col_names}
                            stmt = stmt.values(**vals)
                        # Add ON CONFLICT
                        conflict_target = ', '.join(conflict_cols)
                        from sqlalchemy.dialects.postgresql import insert as pg_insert
                        pg_stmt = pg_insert(tbl).values(
                            [{c: row[c] if pd.notna(row[c]) else None for c in col_names} 
                             for _, row in batch.iterrows()]
                        )
                        pg_stmt = pg_stmt.on_conflict_do_nothing(constraint=conflict_target if len(conflict_cols) == 1 else None)
                        # Simplify: just use to_sql and catch exceptions
                        raise NotImplementedError("Fall through to simpler approach")
                raise NotImplementedError("Using simple approach")
            except (NotImplementedError, Exception):
                pass
            # Simple approach
            try:
                batch.to_sql(table, conn, if_exists='append', method='multi', index=False)
                total += len(batch)
            except Exception as e:
                print(f"  [WARN] batch insert failed: {e[:200] if hasattr(e, '__str__') else e}")
                # Try row by row
                for _, row in batch.iterrows():
                    try:
                        row_df = pd.DataFrame([row])
                        row_df.to_sql(table, conn, if_exists='append', method='multi', index=False)
                        total += 1
                    except Exception:
                        pass
    return total


def safe_insert_best_effort(engine, table, df, batch_size=2000):
    """Insert DataFrame with best effort - ON CONFLICT DO NOTHING using pg dialect."""
    if df is None or df.empty:
        return 0
    total = 0
    with engine.begin() as conn:
        # Reflect table
        meta = MetaData()
        tbl = Table(table, meta, autoload_with=engine, keep_existing=True)
        col_names = [c.name for c in tbl.columns if c.name in df.columns]
        if not col_names:
            return 0
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start+batch_size]
            records = [{c: (row[c] if pd.notna(row[c]) else None) for c in col_names} 
                       for _, row in batch.iterrows()]
            try:
                stmt = pg_insert(tbl).values(records)
                stmt = stmt.on_conflict_do_nothing()
                conn.execute(stmt)
                total += len(batch)
            except Exception as e:
                print(f"  [WARN] batch failed: {e}")
                # row by row
                for rec in records:
                    try:
                        stmt = pg_insert(tbl).values([rec]).on_conflict_do_nothing()
                        conn.execute(stmt)
                        total += 1
                    except Exception:
                        pass
    return total


from sqlalchemy import Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert


def count_rows(engine, table):
    with engine.connect() as conn:
        r = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return r.scalar()


# ─────────────────────────────────────────────
# Module 1: trade_cal → ref_trade_cal
# ─────────────────────────────────────────────
def import_trade_cal(engine):
    print("\n=== Module 1: ref_trade_cal (SSE Trade Calendar) ===")
    df = pro.trade_cal(exchange='SSE', start_date='19900101', end_date='20261231', fields='exchange,cal_date,is_open,pretrade_date')
    rate_limit()
    print(f"  Fetched {len(df)} rows from Tushare")
    
    # Rename to match schema
    df['cal_date'] = pd.to_datetime(df['cal_date'])
    df['pretrade_date'] = pd.to_datetime(df['pretrade_date'])
    df = df.rename(columns={'is_open': 'is_open'})
    
    rows = safe_insert_best_effort(engine, 'ref_trade_cal', df)
    print(f"  ✅ ref_trade_cal: {rows} rows written (total: {count_rows(engine, 'ref_trade_cal')})")
    return rows


# ─────────────────────────────────────────────
# Module 2: stock_basic → ref_stock_basic + asset
# ─────────────────────────────────────────────
def import_stock_basic(engine):
    print("\n=== Module 2: ref_stock_basic + asset ===")
    
    # Fetch all listed stocks
    df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs')
    rate_limit()
    # Also fetch delisted
    df_d = pro.stock_basic(exchange='', list_status='D', fields='ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs')
    rate_limit()
    df = pd.concat([df, df_d], ignore_index=True).drop_duplicates(subset='ts_code')
    
    print(f"  Fetched {len(df)} stocks from Tushare")
    
    # Convert dates
    if 'list_date' in df.columns:
        df['list_date'] = pd.to_datetime(df['list_date'], errors='coerce')
    if 'delist_date' in df.columns:
        df['delist_date'] = pd.to_datetime(df['delist_date'], errors='coerce')
    
    # asset table: create asset records with UUIDs
    import uuid
    now = datetime.datetime.now()
    asset_records = []
    stock_records = []
    
    for _, row in df.iterrows():
        aid = uuid.uuid4()
        exchange = ''
        if row.get('ts_code', ''):
            ts_c = str(row['ts_code'])
            if ts_c.endswith('.SZ'):
                exchange = 'SZSE'
            elif ts_c.endswith('.SH'):
                exchange = 'SSE'
            elif ts_c.endswith('.BJ'):
                exchange = 'BSE'
        
        asset_records.append({
            'id': aid,
            'symbol': row.get('symbol', ''),
            'exchange': exchange,
            'asset_type': 'stock',
            'name': row.get('name', ''),
            'isin': '',
            'source_id': row.get('ts_code', ''),
            'status': 'active' if row.get('list_status', 'L') == 'L' else 'delisted',
            'valid_from': row.get('list_date') or now,
            'valid_to': row.get('delist_date') or datetime.datetime(2099, 12, 31),
            'extra': None,
        })
        
        stock_records.append({
            'asset_id': aid,
            'ts_code': row.get('ts_code', ''),
            'symbol': row.get('symbol', ''),
            'name': row.get('name', ''),
            'area': row.get('area', ''),
            'industry': row.get('industry', ''),
            'market': row.get('market', ''),
            'list_date': row.get('list_date'),
            'delist_date': row.get('delist_date'),
            'is_hs': row.get('is_hs', ''),
        })
    
    # Insert asset
    print(f"  Inserting {len(asset_records)} asset records...")
    with engine.begin() as conn:
        meta = MetaData()
        tbl = Table('asset', meta, autoload_with=engine, keep_existing=True)
        stmt = pg_insert(tbl).values(asset_records).on_conflict_do_nothing()
        r = conn.execute(stmt)
        print(f"  ✅ asset: inserted {r.rowcount} rows (total: {count_rows(engine, 'asset')})")
    
    # Insert ref_stock_basic
    print(f"  Inserting {len(stock_records)} stock_basic records...")
    with engine.begin() as conn:
        meta = MetaData()
        tbl = Table('ref_stock_basic', meta, autoload_with=engine, keep_existing=True)
        # batch
        for i in range(0, len(stock_records), 500):
            batch = stock_records[i:i+500]
            stmt = pg_insert(tbl).values(batch).on_conflict_do_nothing(
                index_elements=['ts_code']
            )
            conn.execute(stmt)
        print(f"  ✅ ref_stock_basic: total {count_rows(engine, 'ref_stock_basic')} rows")
    
    return len(stock_records)


# ─────────────────────────────────────────────
# Module 3: daily_basic → raw_daily_basic
# ─────────────────────────────────────────────
def import_daily_basic(engine):
    print("\n=== Module 3: raw_daily_basic (PE/PB/换手率) ===")
    
    # Get all stock codes
    with engine.connect() as conn:
        r = conn.execute(text("SELECT ts_code FROM ref_stock_basic"))
        all_codes = [row[0] for row in r]
    
    # Fetch month by month for 2024-2026
    total_rows = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            end_month = month + 1
            end_year = year
            if end_month > 12:
                end_month = 1
                end_year += 1
            end_date = f"{end_year}{end_month:02d}01"
            # Use the format YYYYMMDD
            # Use end of month: calculate last day
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            
            if (year == 2026 and month > 4):
                continue  # Skip future months
                
            try:
                df = pro.daily_basic(ts_code='', trade_date='', 
                                     start_date=start_date, end_date=end_date,
                                     fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_mv,circ_mv,total_share,float_share,free_share')
                rate_limit()
                if df is not None and not df.empty:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    rows = safe_insert_best_effort(engine, 'raw_daily_basic', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows} written")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
                continue
    
    final = count_rows(engine, 'raw_daily_basic')
    print(f"  ✅ raw_daily_basic: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 4: index_daily → raw_index_daily
# ─────────────────────────────────────────────
def import_index_daily(engine):
    print("\n=== Module 4: raw_index_daily (9 major indices) ===")
    
    indices = {
        '000001.SH': '上证指数',
        '399001.SZ': '深证成指',
        '399006.SZ': '创业板指',
        '000688.SH': '科创50',
        '000300.SH': '沪深300',
        '000016.SH': '上证50',
        '000905.SH': '中证500',
        '000852.SH': '中证1000',
        '399303.SZ': '国证2000',
    }
    
    total_rows = 0
    for ts_code, name in indices.items():
        try:
            df = pro.index_daily(ts_code=ts_code, start_date='20240101', end_date='20260430',
                                 fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
            rate_limit()
            if df is not None and not df.empty:
                rows = safe_insert_best_effort(engine, 'raw_index_daily', df)
                total_rows += rows
                print(f"  {name} ({ts_code}): {len(df)} -> {rows}")
            else:
                print(f"  {name} ({ts_code}): empty")
            time.sleep(0.3)
        except Exception as e:
            print(f"  {name} ({ts_code}): ERROR {e}")
    
    final = count_rows(engine, 'raw_index_daily')
    print(f"  ✅ raw_index_daily: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 5: moneyflow → raw_moneyflow
# ─────────────────────────────────────────────
def import_moneyflow(engine):
    print("\n=== Module 5: raw_moneyflow (个股资金流向) ===")
    
    total_rows = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            
            if (year == 2026 and month > 4):
                continue
            
            try:
                df = pro.moneyflow(trade_date='', start_date=start_date, end_date=end_date,
                                   fields='ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,net_mf_vol,net_mf_amount')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_moneyflow', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_moneyflow')
    print(f"  ✅ raw_moneyflow: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 6: moneyflow_mkt_dc → raw_moneyflow_mkt_dc
# ─────────────────────────────────────────────
def import_moneyflow_mkt(engine):
    print("\n=== Module 6: raw_moneyflow_mkt_dc (大盘资金流) ===")
    
    total_rows = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            
            if (year == 2026 and month > 4):
                continue
            
            try:
                df = pro.moneyflow_mkt_dc(start_date=start_date, end_date=end_date,
                                          fields='trade_date,s_d_value,m_d_value,l_d_value,el_d_value,net_main,net_main_pct')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_moneyflow_mkt_dc', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_moneyflow_mkt_dc')
    print(f"  ✅ raw_moneyflow_mkt_dc: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 7: top_inst → raw_top_inst
# ─────────────────────────────────────────────
def import_top_inst(engine):
    print("\n=== Module 7: raw_top_inst (龙虎榜机构) ===")
    
    total_rows = 0
    # 2024-2025 monthly
    for year in [2024, 2025]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            try:
                df = pro.top_inst(trade_date='', start_date=start_date, end_date=end_date,
                                 fields='trade_date,ts_code,exalter,buy,buy_rate,sell,sell_rate,net_buy,side,reason')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_top_inst', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_top_inst')
    print(f"  ✅ raw_top_inst: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 8: margin → raw_margin_detail
# ─────────────────────────────────────────────
def import_margin(engine):
    print("\n=== Module 8: raw_margin_detail (融资融券) ===")
    
    total_rows = 0
    for year in [2024, 2025, 2026]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            
            if (year == 2026 and month > 4):
                continue
            
            try:
                df = pro.margin(start_date=start_date, end_date=end_date,
                                fields='trade_date,ts_code,name,rzye,rzmre,rzche,rqye,rqmcl,rzrqye')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_margin_detail', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_margin_detail')
    print(f"  ✅ raw_margin_detail: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 9: shibor → raw_shibor
# ─────────────────────────────────────────────
def import_shibor(engine):
    print("\n=== Module 9: raw_shibor (2020-2026) ===")
    
    total_rows = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            if (year == 2026 and month > 4):
                continue
            try:
                df = pro.shibor(start_date=start_date, end_date=end_date,
                                fields='date,on_rate,on_bid,w1_rate,w1_bid,w2_rate,w2_bid,m1_rate,m1_bid,m3_rate,m3_bid,m6_rate,m6_bid,m9_rate,m9_bid,y1_rate,y1_bid')
                rate_limit()
                # Our schema doesn't have m1_bid, m3_bid etc. Let's filter
                if df is not None and not df.empty:
                    schema_cols = ['date', 'on_rate', 'on_bid', 'w1_rate', 'w1_bid', 'w2_rate', 'w2_bid',
                                   'm1_rate', 'm3_rate', 'm6_rate', 'm9_rate', 'y1_rate']
                    avail_cols = [c for c in schema_cols if c in df.columns]
                    df = df[avail_cols]
                    rows = safe_insert_best_effort(engine, 'raw_shibor', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_shibor')
    print(f"  ✅ raw_shibor: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 10: macro (CPI/GDP/PMI/M2)
# ─────────────────────────────────────────────
def import_macro(engine):
    print("\n=== Module 10: Macro Indicators ===")
    
    # CPI
    print("  CPI...")
    total_cpi = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            period = f"{year}{month:02d}"
            if (year == 2026 and month > 4):
                continue
            try:
                df = pro.cpi(start_period=period, end_period=period,
                             fields='month,nt_val,nt_yoy,nt_mom,nt_accu')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_cn_cpi', df)
                    total_cpi += rows
                time.sleep(0.2)
            except Exception:
                pass
    print(f"    CPI: {total_cpi} rows")
    
    # GDP
    print("  GDP...")
    total_gdp = 0
    for year in range(2020, 2027):
        for q in range(1, 5):
            quarter = f"{year}q{q}"
            if (year == 2026 and q > 1):
                continue
            try:
                df = pro.cn_gdp(quarter=quarter, fields='quarter,gdp,gdp_yoy,pi,pi_yoy,si,si_yoy,ti,ti_yoy')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_cn_gdp', df)
                    total_gdp += rows
                time.sleep(0.2)
            except Exception:
                pass
    print(f"    GDP: {total_gdp} rows")
    
    # PMI
    print("  PMI...")
    total_pmi = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            period = f"{year}{month:02d}"
            if (year == 2026 and month > 4):
                continue
            try:
                df = pro.cn_pmi(start_period=period, end_period=period,
                                fields='month,pmi,pmi_yoy,pmi_month')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_cn_pmi', df)
                    total_pmi += rows
                time.sleep(0.2)
            except Exception:
                pass
    print(f"    PMI: {total_pmi} rows")
    
    # Money Supply (M0/M1/M2)
    print("  Money Supply...")
    total_ms = 0
    for year in range(2020, 2027):
        for month in range(1, 13):
            period = f"{year}{month:02d}"
            if (year == 2026 and month > 4):
                continue
            try:
                df = pro.cn_m(start_period=period, end_period=period,
                              fields='month,m0,m0_yoy,m1,m1_yoy,m2,m2_yoy')
                rate_limit()
                if df is not None and not df.empty:
                    rows = safe_insert_best_effort(engine, 'raw_cn_money_supply', df)
                    total_ms += rows
                time.sleep(0.2)
            except Exception:
                pass
    print(f"    Money Supply: {total_ms} rows")
    
    totals = {
        'raw_cn_cpi': count_rows(engine, 'raw_cn_cpi'),
        'raw_cn_gdp': count_rows(engine, 'raw_cn_gdp'),
        'raw_cn_pmi': count_rows(engine, 'raw_cn_pmi'),
        'raw_cn_money_supply': count_rows(engine, 'raw_cn_money_supply'),
    }
    print(f"  ✅ Macro totals: {totals}")
    return sum(totals.values())


# ─────────────────────────────────────────────
# Module 11: consultations → raw_consultation
# ─────────────────────────────────────────────
def import_consultations(engine):
    print("\n=== Module 11: raw_consultation (快讯) ===")
    
    total_rows = 0
    import datetime
    today = datetime.date.today()
    for days_ago in range(30):
        d = today - datetime.timedelta(days=days_ago)
        date_str = d.strftime('%Y%m%d')
        try:
            df = pro.news(src='', start_date=date_str, end_date=date_str,
                          fields='datetime,content,title,channels')
            rate_limit()
            if df is not None and not df.empty:
                # Rename columns to match schema
                df = df.rename(columns={
                    'datetime': 'pub_time',
                    'channels': 'source',
                })
                # Generate news_id if not present
                if 'news_id' not in df.columns:
                    df['news_id'] = [f"news_{d.strftime('%Y%m%d')}_{i}" for i in range(len(df))]
                df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                # Select matching columns
                cols = ['news_id', 'title', 'content', 'source', 'pub_time']
                avail = [c for c in cols if c in df.columns]
                df = df[avail]
                rows = safe_insert_best_effort(engine, 'raw_consultation', df)
                total_rows += rows
                print(f"  {date_str}: {len(df)} -> {rows}")
            time.sleep(0.3)
        except Exception as e:
            pass
    
    final = count_rows(engine, 'raw_consultation')
    print(f"  ✅ raw_consultation: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 12: major_news → raw_major_news
# ─────────────────────────────────────────────
def import_major_news(engine):
    print("\n=== Module 12: raw_major_news (重大新闻) ===")
    
    total_rows = 0
    # Tushare's major_news has start_date/end_date filters
    for year in [2025, 2026]:
        for month in range(1, 13):
            start_date = f"{year}{month:02d}01"
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}{month:02d}{last_day:02d}"
            if (year == 2026 and month > 4):
                continue
            try:
                df = pro.major_news(start_date=start_date, end_date=end_date,
                                    fields='datetime,content,title,channels')
                rate_limit()
                if df is not None and not df.empty:
                    df = df.rename(columns={
                        'datetime': 'pub_time',
                        'channels': 'source',
                    })
                    if 'news_id' not in df.columns:
                        df['news_id'] = [f"major_{year}{month:02d}_{i}" for i in range(len(df))]
                    df['pub_time'] = pd.to_datetime(df['pub_time'], errors='coerce')
                    cols = ['news_id', 'title', 'content', 'source', 'pub_time']
                    avail = [c for c in cols if c in df.columns]
                    df = df[avail]
                    rows = safe_insert_best_effort(engine, 'raw_major_news', df)
                    total_rows += rows
                    print(f"  {year}-{month:02d}: {len(df)} -> {rows}")
                else:
                    print(f"  {year}-{month:02d}: empty")
                time.sleep(0.3)
            except Exception as e:
                print(f"  {year}-{month:02d}: ERROR {e}")
    
    final = count_rows(engine, 'raw_major_news')
    print(f"  ✅ raw_major_news: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Module 13: concept → ref_concept + ref_concept_detail
# ─────────────────────────────────────────────
def import_concept(engine):
    print("\n=== Module 13: ref_concept + ref_concept_detail ===")
    
    # 1. Concept list
    print("  Concept list...")
    try:
        df = pro.concept()
        rate_limit()
        if df is not None and not df.empty:
            df = df.rename(columns={'code': 'code', 'name': 'name', 'src': 'src'})
            rows = safe_insert_best_effort(engine, 'ref_concept', df)
            print(f"  ref_concept: {rows} rows (total: {count_rows(engine, 'ref_concept')})")
    except Exception as e:
        print(f"  concept list ERROR: {e}")
    
    # 2. Concept detail for each concept
    print("  Concept details...")
    with engine.connect() as conn:
        r = conn.execute(text("SELECT code, name FROM ref_concept"))
        concepts = [(row[0], row[1]) for row in r]
    print(f"  {len(concepts)} concepts to process")
    
    total_detail = 0
    for code, name in concepts[:200]:  # Limit to 200 concepts
        try:
            df = pro.concept_detail(id=code, fields='code,name,ts_code,ts_name,weight')
            rate_limit()
            if df is not None and not df.empty:
                df = df.rename(columns={
                    'code': 'concept_code',
                    'name': 'concept_name',
                    'ts_name': 'name',
                    'ts_code': 'ts_code',
                })
                detail_rows = safe_insert_best_effort(engine, 'ref_concept_detail', df)
                total_detail += detail_rows
            time.sleep(0.2)
        except Exception as e:
            print(f"  concept {code}: ERROR {e}")
    
    final_detail = count_rows(engine, 'ref_concept_detail')
    print(f"  ✅ ref_concept_detail: {total_detail} rows written (total: {final_detail})")
    return len(concepts)


# ─────────────────────────────────────────────
# Module 14: adj_factor → ref_adj_factor (first 200 stocks)
# ─────────────────────────────────────────────
def import_adj_factor(engine):
    print("\n=== Module 14: ref_adj_factor (first 200 stocks, full history) ===")
    
    with engine.connect() as conn:
        r = conn.execute(text("SELECT ts_code FROM ref_stock_basic LIMIT 200"))
        codes = [row[0] for row in r]
    
    total_rows = 0
    for i, ts_code in enumerate(codes):
        try:
            df = pro.adj_factor(ts_code=ts_code, fields='ts_code,trade_date,adj_factor')
            rate_limit()
            if df is not None and not df.empty:
                df
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                rows = safe_insert_best_effort(engine, 'ref_adj_factor', df)
                total_rows += rows
            if i % 20 == 0 and i > 0:
                print(f"  {i}/{len(codes)} processed...")
            time.sleep(0.1)
        except Exception as e:
            print(f"  {ts_code}: ERROR {e}")

    final = count_rows(engine, 'ref_adj_factor')
    print(f"  ✅ ref_adj_factor: {total_rows} rows written (total: {final})")
    return total_rows


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == '__main__':
    engine = get_engine()

    print("=" * 60)
    print("Quant Data Import - Starting")
    print(f"Time: {datetime.datetime.now()}")
    print("=" * 60)

    # 1
    import_trade_cal(engine)

    # 2
    import_stock_basic(engine)

    # 3
    import_daily_basic(engine)

    # 4
    import_index_daily(engine)

    # 5
    import_moneyflow(engine)

    # 6
    import_moneyflow_mkt(engine)

    # 7
    import_top_inst(engine)

    # 8
    import_margin(engine)

    # 9
    import_shibor(engine)

    # 10
    import_macro(engine)

    # 11
    import_consultations(engine)

    # 12
    import_major_news(engine)

    # 13
    import_concept(engine)

    # 14
    import_adj_factor(engine)

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    with engine.connect() as conn:
        r = conn.execute(text("SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' ORDER BY n_live_tup DESC"))
        for row in r:
            print(f"  {row[0]:40s} {row[1]}")

    print(f"\nDone: {datetime.datetime.now()}")
