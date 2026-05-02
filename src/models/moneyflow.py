"""Money flow / 资金流向 — 个股资金流、沪深港通、融资融券."""

from __future__ import annotations

from sqlalchemy import Column, String, Float, BigInteger, Text, UniqueConstraint
from src.models.base import TimestampMixin, Base


class RawMoneyflow(TimestampMixin, Base):
    """个股资金流 (moneyflow) — 逐日."""
    __tablename__ = "raw_moneyflow"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(32), nullable=False, index=True)
    trade_date = Column(String(8), nullable=False, index=True)
    buy_sm_vol = Column(Float)      # 小单买入量（手）
    buy_sm_amount = Column(Float)   # 小单买入金额（万元）
    sell_sm_vol = Column(Float)
    sell_sm_amount = Column(Float)
    buy_md_vol = Column(Float)      # 中单
    buy_md_amount = Column(Float)
    sell_md_vol = Column(Float)
    sell_md_amount = Column(Float)
    buy_lg_vol = Column(Float)      # 大单
    buy_lg_amount = Column(Float)
    sell_lg_vol = Column(Float)
    sell_lg_amount = Column(Float)
    buy_elg_vol = Column(Float)     # 特大单
    buy_elg_amount = Column(Float)
    sell_elg_vol = Column(Float)
    sell_elg_amount = Column(Float)
    net_mf_vol = Column(Float)      # 净流入量（手）
    net_mf_amount = Column(Float)   # 净流入额（万元）
    raw_json = Column(Text, nullable=True)  # 原始 JSON

    def __repr__(self):
        return f"<RawMoneyflow({self.ts_code}, {self.trade_date})>"


class RawMoneyflowMktDc(TimestampMixin, Base):
    """大盘资金流 (moneyflow_mkt_dc)."""
    __tablename__ = "raw_moneyflow_mkt_dc"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, unique=True)
    s_d_value = Column(Float)       # 小单净流入
    m_d_value = Column(Float)       # 中单
    l_d_value = Column(Float)       # 大单
    el_d_value = Column(Float)      # 特大单
    net_main = Column(Float)        # 主力净流入
    net_main_pct = Column(Float)    # 主力净占比


class RawHsgtTop10(TimestampMixin, Base):
    """沪深港通十大成交 (hsgt_top10)."""
    __tablename__ = "raw_hsgt_top10"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False)
    name = Column(String(64))
    close = Column(Float)
    pct_change = Column(Float)
    rank = Column(String(8))        # 1：沪股通 2：深股通
    buy_amount = Column(Float)      # 买入金额（亿元）
    sell_amount = Column(Float)     # 卖出金额（亿元）
    net_amount = Column(Float)      # 净买入金额（亿元）


class RawGgtTop10(TimestampMixin, Base):
    """港股通十大成交 (ggt_top10)."""
    __tablename__ = "raw_ggt_top10"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False)
    name = Column(String(64))
    close = Column(Float)
    pct_change = Column(Float)
    rank = Column(String(8))
    buy_amount = Column(Float)
    sell_amount = Column(Float)
    net_amount = Column(Float)


class RawMarginDetail(TimestampMixin, Base):
    """融资融券明细 (margin_detail)."""
    __tablename__ = "raw_margin_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64))
    rzye = Column(Float)            # 融资余额（元）
    rzmre = Column(Float)           # 融资买入额（元）
    rzche = Column(Float)           # 融资偿还额（元）
    rqye = Column(Float)            # 融券余额（元）
    rqyl = Column(Float, nullable=True)   # 融券余量（股）
    rqchl = Column(Float, nullable=True)  # 融券偿还量（股）
    rqmcl = Column(Float)           # 融券卖出量（股）
    rzrqye = Column(Float)          # 融资融券余额（元）
    raw_json = Column(Text, nullable=True)  # 原始 JSON

    # ── Computed (T+1) ──
    # 这些字段由 compute_curated 计算，非 API 直接返回
    rzye_change = Column(Float, nullable=True)       # 融资余额变动
    rqye_change = Column(Float, nullable=True)       # 融券余额变动
    net_margin_flow = Column(Float, nullable=True)   # 净融资融券流量


class RawMarginTotal(TimestampMixin, Base):
    """融资融券总量 (margin) — 大盘汇总，非个股明细.

    Source: Tushare margin API (not margin_detail)
    Fields: trade_date, exchange_id, rzye, rzmre, rzche, rqye, rqmcl, rzrqye, rqyl
    """
    __tablename__ = "raw_margin_total"
    __table_args__ = (
        UniqueConstraint("trade_date", "exchange_id", name="uq_margin_total_date_exchange"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    exchange_id = Column(String(8), nullable=True)  # 交易所: SSE/SZSE/BSE
    rzye = Column(Float)            # 融资余额（元）
    rzmre = Column(Float)           # 融资买入额（元）
    rzche = Column(Float)           # 融资偿还额（元）
    rqye = Column(Float)            # 融券余额（元）
    rqmcl = Column(Float)           # 融券卖出量（股）
    rzrqye = Column(Float)          # 融资融券余额（元）
    rqyl = Column(Float, nullable=True)  # 融券余量（股）


class RawMoneyflowHsgt(TimestampMixin, Base):
    """沪深港通资金流向 (moneyflow_hsgt) — 北向/南向资金.

    Source: Tushare moneyflow_hsgt API
    Fields: trade_date, ggt_ss, ggt_sz, hgt, sgt, north_money, south_money
    """
    __tablename__ = "raw_moneyflow_hsgt"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, unique=True)
    ggt_ss = Column(Float, nullable=True)       # 港股通(沪)成交净买入(亿)
    ggt_sz = Column(Float, nullable=True)       # 港股通(深)成交净买入(亿)
    hgt = Column(Float, nullable=True)          # 沪股通成交净买入(亿)
    sgt = Column(Float, nullable=True)          # 深股通成交净买入(亿)
    north_money = Column(Float, nullable=True)  # 北向资金成交净买入(亿)
    south_money = Column(Float, nullable=True)  # 南向资金成交净买入(亿)
    raw_json = Column(Text, nullable=True)       # 原始 JSON


class RawGgtDaily(TimestampMixin, Base):
    """港股通日度成交统计 (ggt_daily).

    Tushare pro.ggt_daily(trade_date=..., start_date=..., end_date=...).
    """
    __tablename__ = "raw_ggt_daily"
    __table_args__ = (
        {"comment": "港股通日度成交统计"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True, unique=True, comment="交易日期")
    buy_amount = Column(Float, nullable=True, comment="买入成交金额(亿元)")
    buy_volume = Column(Float, nullable=True, comment="买入成交笔数(万笔)")
    sell_amount = Column(Float, nullable=True, comment="卖出成交金额(亿元)")
    sell_volume = Column(Float, nullable=True, comment="卖出成交笔数(万笔)")
    raw_json = Column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawGgtDaily({self.trade_date})>"

class RawGgtMonthly(TimestampMixin, Base):
    """港股通月度成交 (ggt_monthly)."""
    __tablename__ = "raw_ggt_monthly"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(String(6), nullable=False, index=True)
    day_buy_amt = Column(Float)
    day_buy_vol = Column(Float)
    day_sell_amt = Column(Float)
    day_sell_vol = Column(Float)
    total_buy_amt = Column(Float)
    total_buy_vol = Column(Float)
    total_sell_amt = Column(Float)
    total_sell_vol = Column(Float)

class RefHsConst(TimestampMixin, Base):
    """沪深股通成分股 (hs_const)."""
    __tablename__ = "ref_hs_const"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(16), nullable=False, index=True)
    hs_type = Column(String(2))
    in_date = Column(String(8))
    out_date = Column(String(8))
    is_new = Column(String(4))


class RawMarginSecs(TimestampMixin, Base):
    """融资融券标的 (margin_secs).

    Source: Tushare margin_secs API
    Fields: trade_date, ts_code, name, exchange
    """
    __tablename__ = "raw_margin_secs"
    __table_args__ = (
        {"comment": "融资融券标的 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    exchange = Column(String(8), nullable=True)
    raw_json = Column(Text, nullable=True, comment="完整API响应JSON")

    def __repr__(self):
        return f"<RawMarginSecs({self.trade_date}, {self.ts_code})>"


class RawStockSt(TimestampMixin, Base):
    """ST股票列表 (stock_st) — 每日ST/PT股票.

    Source: Tushare stock_st API
    Fields: ts_code, name, trade_date, type, type_name
    Data range: 2016-01-01 onward
    """
    __tablename__ = "raw_stock_st"
    __table_args__ = (
        UniqueConstraint("trade_date", "ts_code", name="uq_stock_st_date_code"),
        {"comment": "ST股票列表 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    type = Column(String(4), nullable=True, comment="ST/*ST/PT")
    type_name = Column(String(32), nullable=True, comment="风险警示板/退市整理板等")


class RawStockHsgt(TimestampMixin, Base):
    """沪深港通股票列表 (stock_hsgt) — 每日成分股快照.

    Source: Tushare stock_hsgt API
    Fields: ts_code, trade_date, type, name, type_name
    Data range: 2025-08-12 onward
    """
    __tablename__ = "raw_stock_hsgt"
    __table_args__ = (
        UniqueConstraint("trade_date", "ts_code", "type", name="uq_stock_hsgt_date_code_type"),
        {"comment": "沪深港通股票列表 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(16), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    type = Column(String(8), nullable=False, comment="HK_SZ/SZ_HK/HK_SH/SH_HK")
    type_name = Column(String(32), nullable=True, comment="深股通/港股通(深)/沪股通/港股通(沪)")


class RawMoneyflowThs(TimestampMixin, Base):
    """同花顺个股资金流向 (moneyflow_ths) — 逐日.

    Source: Tushare moneyflow_ths API
    Fields: trade_date, ts_code, name, pct_change, latest, net_amount,
            net_d5_amount, buy_lg/md/sm_amount + rate
    """
    __tablename__ = "raw_moneyflow_ths"
    __table_args__ = (
        {"comment": "同花顺个股资金流向 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    pct_change = Column(Float)
    latest = Column(Float)
    net_amount = Column(Float)           # 资金净流入(万元)
    net_d5_amount = Column(Float)        # 5日主力净额(万元)
    buy_lg_amount = Column(Float)        # 今日大单净流入额(万元)
    buy_lg_amount_rate = Column(Float)   # 大单净流入占比(%)
    buy_md_amount = Column(Float)        # 中单净流入额(万元)
    buy_md_amount_rate = Column(Float)   # 中单净流入占比(%)
    buy_sm_amount = Column(Float)        # 小单净流入额(万元)
    buy_sm_amount_rate = Column(Float)   # 小单净流入占比(%)
    raw_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawMoneyflowThs({self.ts_code}, {self.trade_date})>"


class RawMoneyflowDc(TimestampMixin, Base):
    """东方财富个股资金流向 (moneyflow_dc) — 逐日.

    Source: Tushare moneyflow_dc API
    Data from 2023-09-11 onward, ~5400 stocks/day.
    """
    __tablename__ = "raw_moneyflow_dc"
    __table_args__ = (
        {"comment": "东方财富个股资金流向 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    pct_change = Column(Float)
    close = Column(Float)
    net_amount = Column(Float)           # 主力净流入额(万元)
    net_amount_rate = Column(Float)      # 主力净流入占比(%)
    buy_elg_amount = Column(Float)       # 超大单净流入额(万元)
    buy_elg_amount_rate = Column(Float)  # 超大单净流入占比(%)
    buy_lg_amount = Column(Float)        # 大单净流入额(万元)
    buy_lg_amount_rate = Column(Float)   # 大单净流入占比(%)
    buy_md_amount = Column(Float)        # 中单净流入额(万元)
    buy_md_amount_rate = Column(Float)   # 中单净流入占比(%)
    buy_sm_amount = Column(Float)        # 小单净流入额(万元)
    buy_sm_amount_rate = Column(Float)   # 小单净流入占比(%)
    raw_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawMoneyflowDc({self.ts_code}, {self.trade_date})>"


class RawMoneyflowCntThs(TimestampMixin, Base):
    """同花顺概念板块资金流向 (moneyflow_cnt_ths) — 逐日.

    Source: Tushare moneyflow_cnt_ths API
    ~387 concept sectors/day, includes leading stock + fund flow.
    """
    __tablename__ = "raw_moneyflow_cnt_ths"
    __table_args__ = (
        {"comment": "同花顺概念板块资金流向 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    lead_stock = Column(String(64), nullable=True)   # 领涨股票名称
    close_price = Column(Float)
    pct_change = Column(Float)                        # 板块涨跌幅
    industry_index = Column(Float)                    # 板块指数
    company_num = Column(BigInteger)                  # 公司数量
    pct_change_stock = Column(Float)                  # 领涨股涨跌幅
    net_buy_amount = Column(Float)                    # 流入资金(亿元)
    net_sell_amount = Column(Float)                   # 流出资金(亿元)
    net_amount = Column(Float)                        # 净额(亿元)
    raw_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawMoneyflowCntThs({self.ts_code}, {self.trade_date})>"


class RawMoneyflowIndThs(TimestampMixin, Base):
    """同花顺行业资金流向 (moneyflow_ind_ths) — 逐日.

    Source: Tushare moneyflow_ind_ths API
    ~90 industries/day, includes leading stock + sector index.
    """
    __tablename__ = "raw_moneyflow_ind_ths"
    __table_args__ = (
        {"comment": "同花顺行业资金流向 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    ts_code = Column(String(32), nullable=False, index=True)
    industry = Column(String(64), nullable=True)     # 板块名称
    lead_stock = Column(String(64), nullable=True)   # 领涨股票
    close = Column(Float)                             # 收盘指数
    pct_change = Column(Float)                        # 指数涨跌幅
    company_num = Column(BigInteger)                  # 公司数量
    pct_change_stock = Column(Float)                  # 领涨股涨跌幅
    close_price = Column(Float)                       # 领涨股最新价
    net_buy_amount = Column(Float)                    # 流入资金(亿元)
    net_sell_amount = Column(Float)                   # 流出资金(亿元)
    net_amount = Column(Float)                        # 净额(亿元)
    raw_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawMoneyflowIndThs({self.ts_code}, {self.trade_date})>"


class RawMoneyflowIndDc(TimestampMixin, Base):
    """东财板块资金流向 (moneyflow_ind_dc) — 逐日，含地域/概念/行业.

    Source: Tushare moneyflow_ind_dc API
    ~1013 sectors/day (地域+概念+行业), data from ~2024-11.
    """
    __tablename__ = "raw_moneyflow_ind_dc"
    __table_args__ = (
        {"comment": "东财板块资金流向 — 原始数据"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(String(8), nullable=False, index=True)
    content_type = Column(String(8), nullable=True)          # 地域/概念/行业
    ts_code = Column(String(32), nullable=False, index=True)
    name = Column(String(64), nullable=True)
    pct_change = Column(Float)
    close = Column(Float)
    net_amount = Column(Float)              # 主力净流入净额(元)
    net_amount_rate = Column(Float)         # 主力净流入净占比%
    buy_elg_amount = Column(Float)          # 超大单净流入净额(元)
    buy_elg_amount_rate = Column(Float)     # 超大单净流入净占比%
    buy_lg_amount = Column(Float)           # 大单净流入净额(元)
    buy_lg_amount_rate = Column(Float)      # 大单净流入净占比%
    buy_md_amount = Column(Float)           # 中单净流入净额(元)
    buy_md_amount_rate = Column(Float)      # 中单净流入净占比%
    buy_sm_amount = Column(Float)           # 小单净流入净额(元)
    buy_sm_amount_rate = Column(Float)      # 小单净流入净占比%
    buy_sm_amount_stock = Column(String(64), nullable=True)   # 主力净流入最大股
    rank = Column(BigInteger, nullable=True)                   # 序号
    raw_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawMoneyflowIndDc({self.ts_code}, {self.trade_date})>"
