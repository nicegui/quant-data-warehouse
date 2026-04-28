"""
Tushare 全量历史数据拉取脚本
按 Tushare 官网确认的每个 API 历史范围拉取全量数据
"""
import os
import sys
import time
import json
import math
import logging
from datetime import datetime, timedelta, date
from typing import Optional

import tushare as ts
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ─── 配置 ───
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "fa41d72664bf5207c4d52e3fceddafb66824e6efbee5cde67beef185")
DB_URL = os.environ.get("QUANT_DB_URL", "postgresql://quant:quant_pass@localhost:5432/quantdb")
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

def _to_pg(val):
    """Convert a Python value to a PostgreSQL literal string"""
    if val is None:
        return 'NULL'
    if isinstance(val, float) and math.isnan(val):
        return 'NULL'
    if isinstance(val, dict) or isinstance(val, list):
        s = json.dumps(val, ensure_ascii=False)
        return f"'{s.replace(chr(39), chr(39)+chr(39))}'"
    if isinstance(val, str):
        return f"'{val.replace(chr(39), chr(39)+chr(39))}'"
    if isinstance(val, (int, float)):
        if isinstance(val, float) and (math.isinf(val) or math.isnan(val)):
            return 'NULL'
        return str(val)
    if isinstance(val, bool):
        return 'TRUE' if val else 'FALSE'
    if isinstance(val, bytes):
        return 'NULL'
    return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"

def table_count(table: str) -> int:
    with engine.connect() as conn:
        r = conn.execute(text(f'SELECT count(*) FROM "{table}"'))
        return r.scalar() or 0

def upsert(table: str, df, pk_cols: list[str] = None, batch_size: int = 500):
    if df is None or df.empty:
        return 0
    df.columns = [c.lower() for c in df.columns]
    
    # Auto-generated columns to exclude
    auto_cols = {'id', 'asset_id', 'created_at', 'updated_at'}
    # Columns that need date string → timestamptz conversion
    ts_cols = {'cal_date', 'trade_date', 'pretrade_date', 'ann_date', 'f_ann_date', 'end_date', 'list_date', 'delist_date', 'start_date', 'exp_date', 'delist_date'}
    
    with engine.connect() as conn:
        r = conn.execute(text(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name='{table}'
        """))
        col_types = {row[0]: row[1] for row in r.fetchall()}
    
    existing_cols = set(col_types.keys())
    common_cols = [c for c in df.columns if c in existing_cols and c not in auto_cols]
    if not common_cols:
        log.warning(f"  [{table}] no matching columns, skipping")
        return 0
    df = df[common_cols]
    
    # Identify boolean columns
    bool_cols = {c for c in common_cols if 'bool' in col_types.get(c, '').lower()}
    total = 0
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start+batch_size]
        cols_str = ', '.join(f'"{c}"' for c in batch.columns)
        if pk_cols:
            conflict_pk = ', '.join(f'"{p}"' for p in pk_cols)
            conflict = f'ON CONFLICT ({conflict_pk}) DO NOTHING'
        else:
            conflict = ''
        with engine.begin() as conn:
            for _, row in batch.iterrows():
                vals = []
                for c in batch.columns:
                    v = row[c]
                    if v is None or (isinstance(v, float) and (v != v or math.isinf(v))):
                        vals.append('NULL')
                    elif isinstance(v, str) and c in ts_cols:
                        # Format YYYYMMDD → YYYY-MM-DD for timestamptz
                        s = v.strip()
                        if len(s) == 8 and s.isdigit():
                            s = f'{s[:4]}-{s[4:6]}-{s[6:8]}'
                        vals.append(f"'{s.replace(chr(39), chr(39)+chr(39))}'::timestamptz")
                    elif isinstance(v, dict) or isinstance(v, list):
                        s = json.dumps(v, ensure_ascii=False)
                        vals.append(f"'{s.replace(chr(39), chr(39)+chr(39))}'")
                    elif isinstance(v, str):
                        vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                    elif isinstance(v, (int, float)):
                        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
                            vals.append('NULL')
                        elif c in bool_cols:
                            vals.append('TRUE' if v else 'FALSE')
                        else:
                            vals.append(str(v))
                    elif isinstance(v, bool):
                        vals.append('TRUE' if v else 'FALSE')
                    else:
                        vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
                
                sql = f'INSERT INTO "{table}" ({cols_str}) VALUES ({", ".join(vals)}) {conflict}'
                try:
                    conn.execute(text(sql))
                except Exception as e:
                    log.warning(f"  upsert error: {e}")
                    raise  # Re-raise so we know what broke
        total += len(batch)
    return total

def _months(start_year, start_month, end_year, end_month):
    for y in range(start_year, end_year + 1):
        m_start = start_month if y == start_year else 1
        m_end = end_month if y == end_year else 12
        for m in range(m_start, m_end + 1):
            yield y, m

def pull_stock_basic():
    if table_count('ref_stock_basic') > 5000:
        log.info("[stock_basic] already present, skip")
        return
    log.info("[stock_basic] pulling...")
    df = pro.stock_basic(fields='ts_code,symbol,name,area,industry,fullname,enname,cnspell,market,exchange,curr_type,list_status,list_date,delist_date,is_hs')
    n = upsert('ref_stock_basic', df, pk_cols=['ts_code'])
    log.info(f"[stock_basic] wrote {n}")

def pull_trade_cal():
    if table_count('ref_trade_cal') > 10000:
        log.info("[trade_cal] skip")
        return
    log.info("[trade_cal] pulling...")
    all_dfs = []
    for ex in ['SSE', 'SZSE', 'BSE']:
        df = pro.trade_cal(exchange=ex, start_date='19900101', end_date='20261231')
        if df is not None and not df.empty:
            all_dfs.append(df)
        time.sleep(0.3)
    if all_dfs:
        df = pd.concat(all_dfs)
        n = upsert('ref_trade_cal', df, pk_cols=['exchange', 'cal_date'])
        log.info(f"[trade_cal] wrote {n}")

def pull_concept():
    if table_count('ref_concept') > 100:
        log.info("[concept] skip")
        return
    log.info("[concept] pulling...")
    df = pro.concept()
    n = upsert('ref_concept', df, pk_cols=['code'])
    log.info(f"[concept] wrote {n}")

def pull_adj_factor():
    log.info("[adj_factor] pulling full history...")
    total = 0
    for y, m in _months(1999, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.adj_factor(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('ref_adj_factor', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.2)
        except Exception as e:
            log.warning(f"  adj_factor {start}: {e}")
            time.sleep(3)
    log.info(f"[adj_factor] done! total {total}")

def pull_stock_daily():
    log.info("[stock_daily] pulling full history (1990-2026)...")
    total = 0
    for y, m in _months(1990, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.daily(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_stock_daily', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.15)
        except Exception as e:
            if '频率过快' in str(e):
                time.sleep(5)
                continue
            log.warning(f"  daily {start}: {e}")
            time.sleep(3)
        if m % 6 == 0:
            log.info(f"  [stock_daily] {y}-{m:02d}: cumulative {total}")
    log.info(f"[stock_daily] done! total {total}")

def pull_daily_basic():
    cur = table_count('raw_daily_basic')
    if cur > 100000:
        log.info(f"[daily_basic] already {cur}, skip")
        return
    log.info("[daily_basic] pulling full history (2010-2026)...")
    total = 0
    for y, m in _months(2010, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.daily_basic(ts_code='', start_date=start, end_date=end,
                fields='ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv,limit_status')
            if df is not None and not df.empty:
                total += upsert('raw_daily_basic', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  daily_basic {start}: {e}")
            time.sleep(3)
        if m % 3 == 0:
            log.info(f"  [daily_basic] {y}-{m:02d}: cumulative {total}")
    log.info(f"[daily_basic] done! total {total}")

def pull_financial():
    if table_count('raw_financial_reports') > 500000:
        log.info(f"[financial_reports] already {table_count('raw_financial_reports')}, skip")
        return
    log.info("[financial] pulling full history...")
    periods = []
    for y in range(2010, 2027):
        periods.append(f'{y}0630')
        periods.append(f'{y}1231')
    periods = periods[:-1]  # remove 20260630

    total_reports = 0
    for api_name in ['income_vip', 'balancesheet_vip', 'cashflow_vip']:
        t = 0
        for p in periods:
            try:
                df = getattr(pro, api_name)(period=p)
                if df is not None and not df.empty:
                    t += upsert('raw_financial_reports', df, pk_cols=['ts_code', 'end_date', 'report_type'])
                time.sleep(0.3)
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
                time.sleep(3)
        log.info(f"  [{api_name}] cumulative {t}")
        total_reports += t

    # fina_indicator_vip
    fi_total = 0
    for p in periods:
        try:
            df = pro.fina_indicator_vip(period=p)
            if df is not None and not df.empty:
                fi_total += upsert('raw_financial_indicators', df, pk_cols=['ts_code', 'end_date'])
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  fina_indicator_vip {p}: {e}")
            time.sleep(3)
    log.info(f"  [fina_indicator_vip] cumulative {fi_total}")

    # forecast + express (last 5 years)
    for api_name in ['forecast_vip', 'express_vip']:
        t = 0
        for p in periods[-10:]:
            try:
                df = getattr(pro, api_name)(period=p)
                if df is not None and not df.empty:
                    t += upsert('raw_financial_reports', df)
                time.sleep(0.3)
            except Exception as e:
                log.warning(f"  {api_name} {p}: {e}")
        log.info(f"  [{api_name}] cumulative {t}")

    log.info(f"[financial] done! total reports={total_reports}, indicators={fi_total}")

def pull_moneyflow():
    cur = table_count('raw_moneyflow')
    if cur > 100000:
        log.info(f"[moneyflow] already {cur}, skip")
        return
    log.info("[moneyflow] pulling full history (2010-2026)...")
    total = 0
    for y, m in _months(2010, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.moneyflow(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_moneyflow', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  moneyflow {start}: {e}")
            time.sleep(3)
        if m % 6 == 0:
            log.info(f"  [moneyflow] {y}: cumulative {total}")
    log.info(f"[moneyflow] done! total {total}")

def pull_margin():
    if table_count('raw_margin_detail') > 50000:
        log.info(f"[margin_detail] skip")
        return
    log.info("[margin_detail] pulling...")
    total = 0
    for y, m in _months(2010, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.margin_detail(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_margin_detail', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"  margin {start}: {e}")
            time.sleep(3)
    log.info(f"[margin_detail] done! total {total}")

def pull_stk_limit():
    if table_count('raw_stk_limit') > 100000:
        log.info(f"[stk_limit] skip")
        return
    log.info("[stk_limit] pulling full history...")
    total = 0
    for y, m in _months(2010, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.stk_limit(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_stk_limit', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.2)
        except Exception as e:
            log.warning(f"  stk_limit {start}: {e}")
            time.sleep(3)
    log.info(f"[stk_limit] done! total {total}")

def pull_index_daily():
    if table_count('raw_index_daily') > 100000:
        log.info(f"[index_daily] skip")
        return
    log.info("[index_daily] pulling full history...")
    total = 0
    for y, m in _months(1990, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.index_daily(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_index_daily', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.2)
        except Exception as e:
            log.warning(f"  index_daily {start}: {e}")
    log.info(f"[index_daily] done! total {total}")

def pull_macro():
    for api_name, table in [
        ('cn_cpi', 'raw_cn_cpi'), ('cn_pmi', 'raw_cn_pmi'), ('cn_gdp', 'raw_cn_gdp'),
        ('cn_m', 'raw_cn_money_supply'), ('shibor', 'raw_shibor'),
    ]:
        c = table_count(table)
        threshold = {'raw_shibor': 10000}.get(table, 100)
        if c > threshold:
            log.info(f"[{api_name}] already {c}, skip")
            continue
        log.info(f"[{api_name}] pulling...")
        try:
            df = getattr(pro, api_name)()
            if df is not None and not df.empty:
                n = upsert(table, df)
                log.info(f"[{api_name}] wrote {n}")
        except Exception as e:
            log.warning(f"  {api_name}: {e}")

def pull_futures():
    if table_count('raw_fut_daily') > 100000:
        log.info(f"[fut_daily] skip")
        return
    log.info("[fut_daily] pulling...")
    total = 0
    for y, m in _months(2005, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.fut_daily(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_fut_daily', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.2)
        except Exception as e:
            log.warning(f"  fut_daily {start}: {e}")
    log.info(f"[fut_daily] done! total {total}")

def pull_fund():
    if table_count('raw_fund_daily') > 50000:
        log.info(f"[fund_daily] skip")
        return
    log.info("[fund_daily] pulling...")
    total = 0
    for y, m in _months(2005, 1, 2026, 12):
        start = f'{y}{m:02d}01'
        import calendar
        last = calendar.monthrange(y, m)[1]
        end = f'{y}{m:02d}{last:02d}'
        try:
            df = pro.fund_daily(start_date=start, end_date=end)
            if df is not None and not df.empty:
                total += upsert('raw_fund_daily', df, pk_cols=['ts_code', 'trade_date'])
            time.sleep(0.2)
        except Exception as e:
            log.warning(f"  fund_daily {start}: {e}")
    log.info(f"[fund_daily] done! total {total}")

if __name__ == '__main__':
    log.info("=== Tushare Full History Pull ===")
    
    # 1. Reference data (small)
    pull_stock_basic()
    pull_trade_cal()
    pull_concept()
    pull_adj_factor()
    
    # 2. Index & macro (small-medium)
    pull_index_daily()
    pull_macro()
    
    # 3. Market data (big!)
    pull_stock_daily()
    pull_daily_basic()
    pull_stk_limit()
    
    # 4. Money flow (medium)
    pull_moneyflow()
    pull_margin()
    
    # 5. Financial (medium)
    pull_financial()
    
    # 6. Futures & fund (medium)
    pull_futures()
    pull_fund()
    
    log.info("=== ALL DONE! ===")
