#!/usr/bin/env python3
"""全量数据导入 — 直接 Tushare API → PostgreSQL 批量写入。

一次性搞定所有数据，不依赖可能有bug的collector类。

用法:
  python scripts/bulk_import.py [--skip-daily] [--dry-run]

环境变量:
  TUSHARE_TOKEN 必须设置（已在 .env 中）
"""
import sys, os, time, json, argparse, uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.engine import get_engine as get_sync_engine
from src.db.session import db_session
from src.config.settings import settings
from src.utils.logging import setup_logging, get_logger

setup_logging()
log = get_logger("bulk_import")

pro = ts.pro_api()
BATCH_SIZE = 1000
RATE_LIMIT_SLEEP = 0.12  # ~500 calls/min


def get_trade_cal(start="19900101", end="20261231"):
    """拉取交易日历"""
    log.info("📅 拉取交易日历...")
    df = pro.trade_cal(exchange='SSE', start_date=start, end_date=end)
    if df is None or df.empty:
        log.warning("  -> 无数据")
        return 0
    recs = df.to_dict('records')
    engine = get_sync_engine()
    written = 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ref_trade_cal"))
        for r in recs:
            pt = r.get('pretrade_date')
            if pt is None or (isinstance(pt, float) and (pt != pt)):
                pt = None
            conn.execute(text("""
                INSERT INTO ref_trade_cal (exchange, cal_date, is_open, pretrade_date)
                VALUES (:exchange, :cal_date, :is_open, :pretrade_date)
            """), {
                "exchange": r.get("exchange"),
                "cal_date": r.get("cal_date"),
                "is_open": bool(r.get("is_open")),
                "pretrade_date": pt,
            })
            written += 1
    log.info(f"  ✅ {written} 条写入")
    return written


def get_stock_basic():
    """拉取股票基本信息（已有数据，做补充）"""
    log.info("🏢 拉取股票基本信息补充...")

    df = pro.stock_basic()
    if df is None or df.empty:
        log.warning("  -> 无数据")
        return 0

    engine = get_sync_engine()
    now = datetime.now(timezone.utc)
    written = 0

    with engine.begin() as conn:
        for _, r in df.iterrows():
            ts_code = r["ts_code"]
            symbol = r["symbol"]
            name = r["name"]

            # 检查 asset 是否存在
            row = conn.execute(text(
                "SELECT id FROM asset WHERE source_id = :code AND asset_type = 'stock'"
            ), {"code": ts_code}).fetchone()

            if row:
                asset_id = row[0]
            else:
                asset_id = uuid.uuid4()
                exchange = "SSE" if ts_code.endswith(".SH") else "SZSE"
                conn.execute(text("""
                    INSERT INTO asset (id, symbol, exchange, asset_type, name, source_id, status, valid_from)
                    VALUES (:id, :symbol, :exchange, :atype, :name, :source_id, 'active', :now)
                """), {
                    "id": asset_id, "symbol": symbol, "exchange": exchange,
                    "atype": "stock", "name": name, "source_id": ts_code, "now": now,
                })

            # 更新 ref_stock_basic
            list_date = r.get("list_date")
            delist_date = r.get("delist_date")
            if pd.notna(list_date) and list_date:
                list_date = datetime.strptime(str(list_date)[:10], "%Y%m%d").replace(tzinfo=timezone.utc)
            else:
                list_date = None
            if pd.notna(delist_date) and delist_date:
                delist_date = datetime.strptime(str(delist_date)[:10], "%Y%m%d").replace(tzinfo=timezone.utc)
            else:
                delist_date = None

            conn.execute(text("""
                INSERT INTO ref_stock_basic (asset_id, ts_code, symbol, name, area, industry, market, list_date, delist_date, is_hs)
                VALUES (:asset_id, :ts_code, :symbol, :name, :area, :industry, :market, :list_date, :delist_date, :is_hs)
                ON CONFLICT (ts_code) DO UPDATE SET
                    name=EXCLUDED.name, area=EXCLUDED.area,
                    industry=EXCLUDED.industry, market=EXCLUDED.market,
                    list_date=EXCLUDED.list_date, delist_date=EXCLUDED.delist_date,
                    is_hs=EXCLUDED.is_hs
            """), {
                "asset_id": asset_id, "ts_code": ts_code, "symbol": symbol,
                "name": name, "area": r.get("area"), "industry": r.get("industry"),
                "market": r.get("market"), "list_date": list_date,
                "delist_date": delist_date, "is_hs": r.get("is_hs"),
            })
            written += 1

    log.info(f"  ✅ 更新/插入 {written} 条")
    return written


def get_daily_basic(year, month):
    """按月拉 daily_basic (PE/PB/成交量/换手率/市值)"""
    if year >= 2026 and month > 4:
        return 0
    start = f"{year}{month:02d}01"
    if month == 12:
        end = f"{year+1}0101"
    else:
        end = f"{year}{month+1:02d}01"

    log.info(f"📊 daily_basic: {start} ~ {end}")
    try:
        df = pro.daily_basic(start_date=start, end_date=end)
    except Exception as e:
        log.warning(f"  API error: {e}")
        time.sleep(5)
        return 0

    if df is None or df.empty:
        return 0

    engine = get_sync_engine()
    written = 0
    recs = df.to_dict('records')

    with engine.begin() as conn:
        for r in recs:
            try:
                conn.execute(text("""
                    INSERT INTO raw_daily_basic (ts_code, trade_date, open, high, low, close,
                        pre_close, change, pct_chg, vol, amount, turnover_rate,
                        turnover_rate_f, volume_ratio, pe, pe_ttm, pb, total_mv, circ_mv, raw_json)
                    VALUES (:ts_code, :trade_date, :open, :high, :low, :close,
                        :pre_close, :change, :pct_chg, :vol, :amount, :turnover_rate,
                        :turnover_rate_f, :volume_ratio, :pe, :pe_ttm, :pb, :total_mv, :circ_mv, :raw_json)
                    ON CONFLICT (ts_code, trade_date) DO NOTHING
                """), {
                    "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                    "open": float(r.get("open", 0) or 0),
                    "high": float(r.get("high", 0) or 0),
                    "low": float(r.get("low", 0) or 0),
                    "close": float(r.get("close", 0) or 0),
                    "pre_close": float(r.get("pre_close", 0) or 0),
                    "change": float(r.get("change", 0) or 0),
                    "pct_chg": float(r.get("pct_chg", 0) or 0),
                    "vol": float(r.get("vol", 0) or 0),
                    "amount": float(r.get("amount", 0) or 0),
                    "turnover_rate": float(r.get("turnover_rate", 0) or 0),
                    "turnover_rate_f": float(r.get("turnover_rate_f", 0) or 0),
                    "volume_ratio": float(r.get("volume_ratio", 0) or 0),
                    "pe": float(r.get("pe", 0) or 0),
                    "pe_ttm": float(r.get("pe_ttm", 0) or 0),
                    "pb": float(r.get("pb", 0) or 0),
                    "total_mv": float(r.get("total_mv", 0) or 0),
                    "circ_mv": float(r.get("circ_mv", 0) or 0),
                    "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                })
                written += 1
            except Exception as e:
                log.warning(f"  Insert error: {e}")

    log.info(f"  -> {written} rows")
    time.sleep(0.5)
    return written


def get_index_daily():
    """拉取指数日线"""
    log.info("📈 拉取指数日线...")
    indices = {
        "000001.SH": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
        "000688.SH": "科创50",
        "000300.SH": "沪深300",
        "000016.SH": "上证50",
        "000905.SH": "中证500",
        "000852.SH": "中证1000",
        "399005.SZ": "中小板指",
    }
    engine = get_sync_engine()
    total = 0
    for idx, name in indices.items():
        try:
            df = pro.index_daily(ts_code=idx, start_date="20240101", end_date="20260428")
            if df is None or df.empty:
                continue
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_index_daily (ts_code, trade_date, open, high, low, close,
                            pre_close, change, pct_chg, vol, amount, raw_json)
                        VALUES (:ts_code, :trade_date, :open, :high, :low, :close,
                            :pre_close, :change, :pct_chg, :vol, :amount, :raw_json)
                        ON CONFLICT (ts_code, trade_date) DO NOTHING
                    """), {
                        "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                        "open": float(r.get("open", 0)), "high": float(r.get("high", 0)),
                        "low": float(r.get("low", 0)), "close": float(r.get("close", 0)),
                        "pre_close": float(r.get("pre_close", 0)),
                        "change": float(r.get("change", 0)),
                        "pct_chg": float(r.get("pct_chg", 0)),
                        "vol": float(r.get("vol", 0)), "amount": float(r.get("amount", 0)),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  {name}({idx}): {len(df)} rows")
        except Exception as e:
            log.warning(f"  {name}: {e}")
        time.sleep(RATE_LIMIT_SLEEP)

    log.info(f"  ✅ 指数日线共 {total} 条")
    return total


def get_moneyflow():
    """拉取个股资金流向"""
    log.info("💰 拉取个股资金流向...")
    engine = get_sync_engine()
    total = 0

    # 分批拉取日期
    import calendar
    for year in [2024, 2025, 2026]:
        max_month = 4 if year == 2026 else 12
        for month in range(1, max_month + 1):
            start = f"{year}{month:02d}01"
            _, last_day = calendar.monthrange(year, month)
            if year == 2026 and month == 4:
                last_day = 28
            end = f"{year}{month:02d}{last_day:02d}"
            log.info(f"  moneyflow: {start} ~ {end}")

            try:
                df = pro.moneyflow(start_date=start, end_date=end)
            except Exception as e:
                log.warning(f"    API err: {e}")
                time.sleep(3)
                continue

            if df is None or df.empty:
                continue

            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_moneyflow (ts_code, trade_date, buy_sm_vol, buy_sm_amount, sell_sm_vol, sell_sm_amount,
                            buy_md_vol, buy_md_amount, sell_md_vol, sell_md_amount, buy_lg_vol, buy_lg_amount,
                            sell_lg_vol, sell_lg_amount, buy_elg_vol, buy_elg_amount, sell_elg_vol, sell_elg_amount,
                            net_mf_vol, net_mf_amount, trade_count, raw_json)
                        VALUES (:ts_code, :trade_date, :bsv, :bsa, :ssv, :ssa, :bmv, :bma, :smv, :sma,
                            :blv, :bla, :slv, :sla, :bev, :bea, :sev, :sea, :nmv, :nma, :tc, :rj)
                        ON CONFLICT (ts_code, trade_date) DO NOTHING
                    """), {
                        "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                        "bsv": float(r.get("buy_sm_vol", 0) or 0),
                        "bsa": float(r.get("buy_sm_amount", 0) or 0),
                        "ssv": float(r.get("sell_sm_vol", 0) or 0),
                        "ssa": float(r.get("sell_sm_amount", 0) or 0),
                        "bmv": float(r.get("buy_md_vol", 0) or 0),
                        "bma": float(r.get("buy_md_amount", 0) or 0),
                        "smv": float(r.get("sell_md_vol", 0) or 0),
                        "sma": float(r.get("sell_md_amount", 0) or 0),
                        "blv": float(r.get("buy_lg_vol", 0) or 0),
                        "bla": float(r.get("buy_lg_amount", 0) or 0),
                        "slv": float(r.get("sell_lg_vol", 0) or 0),
                        "sla": float(r.get("sell_lg_amount", 0) or 0),
                        "bev": float(r.get("buy_elg_vol", 0) or 0),
                        "bea": float(r.get("buy_elg_amount", 0) or 0),
                        "sev": float(r.get("sell_elg_vol", 0) or 0),
                        "sea": float(r.get("sell_elg_amount", 0) or 0),
                        "nmv": float(r.get("net_mf_vol", 0) or 0),
                        "nma": float(r.get("net_mf_amount", 0) or 0),
                        "tc": float(r.get("trade_count", 0) or 0),
                        "rj": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1

            time.sleep(RATE_LIMIT_SLEEP)

    log.info(f"  ✅ 共 {total} 条")
    return total


def get_top_inst():
    """拉取龙虎榜机构明细"""
    log.info("🏆 拉取龙虎榜机构成交明细...")
    engine = get_sync_engine()
    total = 0
    for year in [2024, 2025]:
        start, end = f"{year}0101", f"{year}1231"
        try:
            df = pro.top_inst(start_date=start, end_date=end)
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_top_inst (ts_code, trade_date, buy, buy_rate, sell, sell_rate, net_buy, net_buy_rate,
                                amount, raw_json)
                            VALUES (:ts_code, :trade_date, :buy, :buy_rate, :sell, :sell_rate,
                                :net_buy, :net_buy_rate, :amount, :raw_json)
                            ON CONFLICT (ts_code, trade_date) DO NOTHING
                        """), {
                            "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                            "buy": float(r.get("buy", 0) or 0),
                            "buy_rate": float(r.get("buy_rate", 0) or 0),
                            "sell": float(r.get("sell", 0) or 0),
                            "sell_rate": float(r.get("sell_rate", 0) or 0),
                            "net_buy": float(r.get("net_buy", 0) or 0),
                            "net_buy_rate": float(r.get("net_buy_rate", 0) or 0),
                            "amount": float(r.get("amount", 0) or 0),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                log.info(f"  {year}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {year}: {e}")
        time.sleep(RATE_LIMIT_SLEEP*3)
    log.info(f"  ✅ 共 {total} 条")
    return total


def get_major_news():
    """拉取重大新闻"""
    log.info("📰 拉取重大新闻...")
    engine = get_sync_engine()
    total = 0
    for month_start in ["20250101", "20250401", "20250701", "20251001",
                         "20260101", "20260401"]:
        month_end_map = {
            "20250101": "20250331", "20250401": "20250630",
            "20250701": "20250930", "20251001": "20251231",
            "20260101": "20260331", "20260401": "20260428",
        }
        end = month_end_map[month_start]
        try:
            df = pro.major_news(start_date=month_start, end_date=end)
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_major_news (news_id, title, content, source, pub_time, raw_json)
                            VALUES (:news_id, :title, :content, :source, :pub_time, :raw_json)
                            ON CONFLICT (news_id) DO NOTHING
                        """), {
                            "news_id": str(r.get("id", "")),
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "source": r.get("source", ""),
                            "pub_time": r.get("news_date"),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                log.info(f"  {month_start}~{end}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {month_start}: {e}")
        time.sleep(RATE_LIMIT_SLEEP*2)
    log.info(f"  ✅ 共 {total} 条")
    return total


def get_futures():
    """拉取期货日线"""
    log.info("🛢️ 拉取期货日线...")
    engine = get_sync_engine()
    total = 0

    main_contracts = ["CU.SHF", "AL.SHF", "ZN.SHF", "RB.SHF", "AU.SHF",
                      "AG.SHF", "SC.SHF", "BU.SHF", "NI.SHF", "SN.SHF",
                      "A.DCE", "B.DCE", "C.DCE", "M.DCE", "P.DCE",
                      "Y.DCE", "J.DCE", "JM.DCE", "I.DCE", "PP.DCE",
                      "L.DCE", "V.DCE", "CF.CZC", "TA.CZC", "MA.CZC",
                      "RM.CZC", "OI.CZC", "SR.CZC", "ZC.CZC", "FG.CZC",
                      "AP.CZC", "PK.DCE", "EB.DCE", "PG.DCE", "LH.DCE",
                      "FU.SHF", "SS.SHF", "SP.SHF", "UR.CZC", "SA.CZC",
                      "PF.CZC", "SM.CZC", "SF.CZC", "CY.CZC", "CJ.CZC",
                      "IF.CCF", "IC.CCF", "IH.CCF", "TS.CCF", "TF.CCF", "T.CCF"
                      ]
    for ts_code in main_contracts:
        try:
            df = pro.fut_daily(ts_code=ts_code, start_date="20240101", end_date="20260428",
                                market="DCE" if ts_code.endswith(".DCE") else
                                       "CZCE" if ts_code.endswith(".CZC") else
                                       "SHFE" if ts_code.endswith(".SHF") else
                                       "CFFEX" if ts_code.endswith(".CCF") else "SHFE")
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_fut_daily (ts_code, trade_date, open, high, low, close,
                                pre_close, change, pct_chg, vol, amount, hold, settle, raw_json)
                            VALUES (:ts_code, :trade_date, :open, :high, :low, :close,
                                :pre_close, :change, :pct_chg, :vol, :amount, :hold, :settle, :raw_json)
                            ON CONFLICT (ts_code, trade_date) DO NOTHING
                        """), {
                            "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                            "open": float(r.get("open", 0)), "high": float(r.get("high", 0)),
                            "low": float(r.get("low", 0)), "close": float(r.get("close", 0)),
                            "pre_close": float(r.get("pre_close", 0)),
                            "change": float(r.get("change", 0)),
                            "pct_chg": float(r.get("pct_chg", 0)),
                            "vol": float(r.get("vol", 0)), "amount": float(r.get("amount", 0)),
                            "hold": float(r.get("hold", 0)), "settle": float(r.get("settle", 0)),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
        except Exception as e:
            pass
        time.sleep(RATE_LIMIT_SLEEP)

    log.info(f"  ✅ 期货日线共 {total} 条")
    return total


def get_hsgt():
    """拉取沪深港通数据"""
    log.info("🌐 拉取沪深港通持股/资金流向...")
    engine = get_sync_engine()
    total = 0

    # 北向每日资金流向
    try:
        df = pro.moneyflow_hsgt(start_date="20240101", end_date="20260428")
        if df is not None and not df.empty:
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_moneyflow_mkt_dc (trade_date, s_market, s_amount, s_volume, s_ratio,
                            ggt_amount, ggt_volume, ggt_ratio, raw_json)
                        VALUES (:trade_date, :s_market, :s_amount, :s_volume, :s_ratio,
                            :ggt_amount, :ggt_volume, :ggt_ratio, :raw_json)
                        ON CONFLICT (trade_date) DO NOTHING
                    """), {
                        "trade_date": r["trade_date"],
                        "s_market": r.get("s_market", "SZSH"),
                        "s_amount": float(r.get("s_amount", 0) or 0),
                        "s_volume": float(r.get("s_volume", 0) or 0),
                        "s_ratio": float(r.get("s_ratio", 0) or 0),
                        "ggt_amount": float(r.get("ggt_amount", 0) or 0),
                        "ggt_volume": float(r.get("ggt_volume", 0) or 0),
                        "ggt_ratio": float(r.get("ggt_ratio", 0) or 0),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  北向资金: {len(df)} rows")
    except Exception as e:
        log.warning(f"  北向: {e}")

    time.sleep(RATE_LIMIT_SLEEP)

    # 沪深港通十大成交
    try:
        for years in ["2024", "2025", "2026"]:
            df = pro.hsgt_top10(start_date=f"{years}0101", end_date=f"{years}1231" if years != "2026" else "20260428")
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    c = 0
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_hsgt_top10 (ts_code, trade_date, name, close, pct_chg,
                                amount, raw_json)
                            VALUES (:ts_code, :trade_date, :name, :close, :pct_chg,
                                :amount, :raw_json)
                            ON CONFLICT (ts_code, trade_date) DO NOTHING
                        """), {
                            "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                            "name": r.get("name", ""), "close": float(r.get("close", 0) or 0),
                            "pct_chg": float(r.get("pct_chg", 0) or 0),
                            "amount": float(r.get("amount", 0) or 0),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        c += 1
                    log.info(f"  港股通十大: {years} {c} rows")
                    total += c
            time.sleep(RATE_LIMIT_SLEEP)
    except Exception as e:
        log.warning(f"  港股通十大: {e}")

    log.info(f"  ✅ 沪深港通共 {total} 条")
    return total


def get_moneyflow_market():
    """拉取大盘资金流向"""
    log.info("🏛️ 拉取大盘资金流向...")
    engine = get_sync_engine()
    total = 0

    # 按日查询
    for start, end in [("20240101", "20240630"), ("20240701", "20241231"),
                        ("20250101", "20250630"), ("20251001", "20251231"),
                        ("20260101", "20260428")]:
        try:
            df = pro.moneyflow_mkt_dc(start_date=start, end_date=end)
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_moneyflow_mkt_dc (trade_date, s_market, s_amount, s_volume, s_ratio,
                                ggt_amount, ggt_volume, ggt_ratio, raw_json)
                            VALUES (:trade_date, :s_market, :s_amount, :s_volume, :s_ratio,
                                :ggt_amount, :ggt_volume, :ggt_ratio, :raw_json)
                            ON CONFLICT (trade_date) DO NOTHING
                        """), {
                            "trade_date": r["trade_date"],
                            "s_market": r.get("s_market", "SZSH"),
                            "s_amount": float(r.get("s_amount", 0) or 0),
                            "s_volume": float(r.get("s_volume", 0) or 0),
                            "s_ratio": float(r.get("s_ratio", 0) or 0),
                            "ggt_amount": float(r.get("ggt_amount", 0) or 0),
                            "ggt_volume": float(r.get("ggt_volume", 0) or 0),
                            "ggt_ratio": float(r.get("ggt_ratio", 0) or 0),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                log.info(f"  {start}~{end}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {start}: {e}")
        time.sleep(RATE_LIMIT_SLEEP)

    log.info(f"  ✅ 共 {total} 条")
    return total


def get_margin():
    """拉取融资融券"""
    log.info("💳 拉取融资融券数据...")
    engine = get_sync_engine()
    total = 0

    for start, end in [("20240101", "20240630"), ("20240701", "20241231"),
                        ("20250101", "20250630"), ("20250701", "20251231"),
                        ("20260101", "20260428")]:
        try:
            df = pro.margin(start_date=start, end_date=end)
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_margin_detail (ts_code, trade_date, rzye, rzmre, rzye_comm,
                                rqye, rqmcl, rqye_comm, rzrqye, rzrqjyz, raw_json)
                            VALUES (:ts_code, :trade_date, :rzye, :rzmre, :rzye_comm,
                                :rqye, :rqmcl, :rqye_comm, :rzrqye, :rzrqjyz, :raw_json)
                            ON CONFLICT (ts_code, trade_date) DO NOTHING
                        """), {
                            "ts_code": r["ts_code"], "trade_date": r["trade_date"],
                            "rzye": float(r.get("rzye", 0) or 0),
                            "rzmre": float(r.get("rzmre", 0) or 0),
                            "rzye_comm": float(r.get("rzye_comm", 0) or 0),
                            "rqye": float(r.get("rqye", 0) or 0),
                            "rqmcl": float(r.get("rqmcl", 0) or 0),
                            "rqye_comm": float(r.get("rqye_comm", 0) or 0),
                            "rzrqye": float(r.get("rzrqye", 0) or 0),
                            "rzrqjyz": float(r.get("rzrqjyz", 0) or 0),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                log.info(f"  {start}~{end}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {start}: {e}")
        time.sleep(RATE_LIMIT_SLEEP*2)

    log.info(f"  ✅ 共 {total} 条")
    return total


def get_shibor():
    """拉取Shibor利率"""
    log.info("🏦 拉取Shibor利率...")
    engine = get_sync_engine()
    total = 0
    for start, end in [("20200101", "20221231"), ("20230101", "20241231"),
                        ("20250101", "20260428")]:
        try:
            df = pro.shibor(start_date=start, end_date=end)
            if df is not None and not df.empty:
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        conn.execute(text("""
                            INSERT INTO raw_shibor (date, on_rate, w1_rate, m1_rate, m3_rate, m6_rate, m9_rate, y1_rate, raw_json)
                            VALUES (:date, :on, :w1, :m1, :m3, :m6, :m9, :y1, :raw_json)
                            ON CONFLICT (date) DO NOTHING
                        """), {
                            "date": r["date"],
                            "on": float(r.get("on", 0) or 0),
                            "w1": float(r.get("1w", 0) or 0),
                            "m1": float(r.get("1m", 0) or 0),
                            "m3": float(r.get("3m", 0) or 0),
                            "m6": float(r.get("6m", 0) or 0),
                            "m9": float(r.get("9m", 0) or 0),
                            "y1": float(r.get("1y", 0) or 0),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                log.info(f"  {start}~{end}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {start}: {e}")
        time.sleep(RATE_LIMIT_SLEEP)
    log.info(f"  ✅ 共 {total} 条")
    return total


def get_macro():
    """拉取宏观数据 (GDP/CPI/PMI/货币供应)"""
    log.info("🌍 拉取宏观数据...")
    engine = get_sync_engine()
    total = 0

    # CPI
    try:
        df = pro.cpi(start_date="20100101", end_date="20260428")
        if df is not None and not df.empty:
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_cn_cpi (date, month, cpi_yoy, cpi_mom, cpi_accum, core_cpi_yoy, raw_json)
                        VALUES (:date, :month, :cpi_yoy, :cpi_mom, :cpi_accum, :core_cpi_yoy, :raw_json)
                        ON CONFLICT (date) DO NOTHING
                    """), {
                        "date": r["date"], "month": r.get("month", ""),
                        "cpi_yoy": float(r.get("cpi_yoy", 0) or 0),
                        "cpi_mom": float(r.get("cpi_mom", 0) or 0),
                        "cpi_accum": float(r.get("cpi_accum", 0) or 0),
                        "core_cpi_yoy": float(r.get("core_cpi_yoy", 0) or 0),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  CPI: {len(df)} rows")
    except Exception as e:
        log.warning(f"  CPI: {e}")

    # GDP
    try:
        df = pro.gdp(start_date="20100101", end_date="20260428")
        if df is not None and not df.empty:
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_cn_gdp (date, gdp, gdp_yoy, pi, pi_yoy, si, si_yoy, ti, ti_yoy, raw_json)
                        VALUES (:date, :gdp, :gdp_yoy, :pi, :pi_yoy, :si, :si_yoy, :ti, :ti_yoy, :raw_json)
                        ON CONFLICT (date) DO NOTHING
                    """), {
                        "date": r["date"],
                        "gdp": float(r.get("gdp", 0) or 0),
                        "gdp_yoy": float(r.get("gdp_yoy", 0) or 0),
                        "pi": float(r.get("pi", 0) or 0),
                        "pi_yoy": float(r.get("pi_yoy", 0) or 0),
                        "si": float(r.get("si", 0) or 0),
                        "si_yoy": float(r.get("si_yoy", 0) or 0),
                        "ti": float(r.get("ti", 0) or 0),
                        "ti_yoy": float(r.get("ti_yoy", 0) or 0),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  GDP: {len(df)} rows")
    except Exception as e:
        log.warning(f"  GDP: {e}")

    # PMI
    try:
        df = pro.pmi(start_date="20100101", end_date="20260428")
        if df is not None and not df.empty:
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO raw_cn_pmi (date, pmi, pmi_yoy, pmi_produce, produce_yoy,
                            new_order, new_order_yoy, raw_json)
                        VALUES (:date, :pmi, :pmi_yoy, :pmi_produce, :produce_yoy,
                            :new_order, :new_order_yoy, :raw_json)
                        ON CONFLICT (date) DO NOTHING
                    """), {
                        "date": r["date"],
                        "pmi": float(r.get("pmi", 0) or 0),
                        "pmi_yoy": float(r.get("pmi_yoy", 0) or 0),
                        "pmi_produce": float(r.get("pmi_produce", 0) or 0),
                        "produce_yoy": float(r.get("produce_yoy", 0) or 0),
                        "new_order": float(r.get("new_order", 0) or 0),
                        "new_order_yoy": float(r.get("new_order_yoy", 0) or 0),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  PMI: {len(df)} rows")
    except Exception as e:
        log.warning(f"  PMI: {e}")

    # 货币供应
    for fn_name in ["money_supply", "money_supply_md"]:
        try:
            fn = getattr(pro, fn_name, None)
            if fn:
                df = fn(start_date="20100101", end_date="20260428")
                if df is not None and not df.empty:
                    with engine.begin() as conn:
                        for _, r in df.iterrows():
                            conn.execute(text("""
                                INSERT INTO raw_cn_money_supply (date, m2, m2_yoy, m1, m1_yoy, m0, m0_yoy, raw_json)
                                VALUES (:date, :m2, :m2_yoy, :m1, :m1_yoy, :m0, :m0_yoy, :raw_json)
                                ON CONFLICT (date) DO NOTHING
                            """), {
                                "date": r["date"],
                                "m2": float(r.get("m2", 0) or 0),
                                "m2_yoy": float(r.get("m2_yoy", 0) or 0),
                                "m1": float(r.get("m1", 0) or 0),
                                "m1_yoy": float(r.get("m1_yoy", 0) or 0),
                                "m0": float(r.get("m0", 0) or 0),
                                "m0_yoy": float(r.get("m0_yoy", 0) or 0),
                                "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                            })
                            total += 1
                    log.info(f"  {fn_name}: {len(df)} rows")
        except Exception as e:
            log.warning(f"  {fn_name}: {e}")
        time.sleep(RATE_LIMIT_SLEEP*2)

    log.info(f"  ✅ 宏观数据共 {total} 条")
    return total


def get_consultations():
    """拉取快讯"""
    log.info("📨 拉取快讯...")
    engine = get_sync_engine()
    total = 0
    try:
        df = pro.news(src='sina', start_date="20260427", end_date="20260428", limit=2000)
        if df is not None and not df.empty:
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    try:
                        conn.execute(text("""
                            INSERT INTO raw_consultation (news_id, title, content, source, pub_time, raw_json)
                            VALUES (:news_id, :title, :content, :source, :pub_time, :raw_json)
                            ON CONFLICT (news_id) DO NOTHING
                        """), {
                            "news_id": str(r.get("id", "") or ""),
                            "title": str(r.get("title", "") or ""),
                            "content": str(r.get("content", "") or ""),
                            "source": str(r.get("source", "") or ""),
                            "pub_time": r.get("datetime", r.get("pub_time")),
                            "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                        })
                        total += 1
                    except Exception:
                        pass
            log.info(f"  快讯: {total} rows")
    except Exception as e:
        log.warning(f"  快讯: {e}")
    return total


def get_concept():
    """拉取概念板块"""
    log.info("🎯 拉取概念板块...")
    engine = get_sync_engine()
    total = 0
    try:
        df = pro.concept()
        if df is not None and not df.empty:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM ref_concept"))
                for _, r in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO ref_concept (code, name, src, raw_json)
                        VALUES (:code, :name, :src, :raw_json)
                    """), {
                        "code": r.get("code", ""),
                        "name": r.get("name", ""),
                        "src": r.get("src", ""),
                        "raw_json": json.dumps(r, ensure_ascii=False, default=str),
                    })
                    total += 1
            log.info(f"  概念板块: {total}")

            # 拉取每个概念成分股
            codes = df["code"].tolist() if "code" in df.columns else []
            detail_count = 0
            for code in codes[:50]:  # 限制前50个板块
                try:
                    dd = pro.concept_detail(concept_code=code)
                    if dd is not None and not dd.empty:
                        with engine.begin() as conn:
                            for _, dr in dd.iterrows():
                                conn.execute(text("""
                                    INSERT INTO ref_concept_detail (concept_code, ts_code, name, raw_json)
                                    VALUES (:code, :ts_code, :name, :raw_json)
                                    ON CONFLICT (concept_code, ts_code) DO NOTHING
                                """), {
                                    "code": code,
                                    "ts_code": dr.get("ts_code", ""),
                                    "name": dr.get("name", ""),
                                    "raw_json": json.dumps(dr, ensure_ascii=False, default=str),
                                })
                                detail_count += 1
                except:
                    pass
                time.sleep(RATE_LIMIT_SLEEP)
            log.info(f"  概念成分股: {detail_count} 条")
    except Exception as e:
        log.warning(f"  概念: {e}")
    return total


def check_state():
    """检查数据库当前数据状态"""
    engine = get_sync_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT relname, n_live_tup
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
        """)).fetchall()

    print(f"\n{'='*70}")
    print(f"{'📊 数据导入状态':^70}")
    print(f"{'='*70}")
    print(f"{'表名':<35} {'行数':>10} {'状态':>10}")
    print(f"{'-'*55}")
    for r in rows:
        status = "✅" if r[1] > 0 else "⬜"
        print(f"{r[0]:<35} {r[1]:>10,} {status:>10}")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="全量数据导入")
    parser.add_argument("--skip-daily", action="store_true", help="跳过日线数据（已有4.2M行）")
    parser.add_argument("--dry-run", action="store_true", help="只检查不导入")
    parser.add_argument("--check", action="store_true", help="检查状态")
    parser.add_argument("--modules", nargs="+", choices=[
        "trade_cal", "daily_basic", "index_daily", "moneyflow", "top_inst",
        "major_news", "futures", "hsgt", "margin", "shibor", "macro",
        "consultations", "concept", "stock_basic", "all"
    ], default=["all"], help="只导入指定模块")
    args = parser.parse_args()

    if args.check:
        check_state()
        return

    if args.dry_run:
        log.info("🧪 干运行模式，实际数据不会导入")
        check_state()
        return

    start_time = time.time()
    log.info(f"{'='*60}")
    log.info("🚀 全量数据导入 开始")
    log.info(f"{'='*60}")

    results = {}

    modules = [
        ("trade_cal", get_trade_cal),
        ("stock_basic", get_stock_basic),
        ("concept", get_concept),
        ("daily_basic", get_daily_basic_multi),
        ("index_daily", get_index_daily),
        ("moneyflow", get_moneyflow),
        ("top_inst", get_top_inst),
        ("margin", get_margin),
        ("hsgt", get_hsgt),
        ("shibor", get_shibor),
        ("macro", get_macro),
        ("consultations", get_consultations),
        ("major_news", get_major_news),
        ("futures", get_futures),
    ]

    if "all" not in args.modules:
        modules = [(n, f) for n, f in modules if n in args.modules]

    for name, func in modules:
        log.info(f"\n{'─'*50}")
        try:
            log.info(f"▶ {name}")
            count = func()
            results[name] = count
            elapsed = time.time() - start_time
            log.info(f"✅ {name} 完成: {count} rows (⏱ {elapsed:.0f}s)")
        except Exception as e:
            log.error(f"❌ {name} 失败: {e}")
            results[name] = -1
        log.info(f"{'─'*50}")
        time.sleep(1)

    # 最终状态
    total_time = time.time() - start_time
    log.info(f"\n{'='*60}")
    log.info(f"🏁 数据导入完成！耗时: {total_time:.0f}s")
    log.info(f"{'='*60}")
    check_state()


def get_daily_basic_multi():
    total = 0
    for year in [2024, 2025, 2026]:
        max_m = 4 if year == 2026 else 12
        for month in range(1, max_m + 1):
            total += get_daily_basic(year, month)
            log.info(f"  daily_basic 累计: {total}")
    return total


if __name__ == "__main__":
    main()
