"""Market sentiment models — limit-up/down, dragon-tiger board, margin.

Raw layer only (append-only). No curated layer needed — these are event data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawTopInst(TimestampMixin, Base):
    """龙虎榜机构成交明细 — Tushare top_inst.

    Fields match the Tushare Pro API response.
    Each row = one institution's buy/sell record for one stock on one day.
    """
    __tablename__ = "raw_top_inst"
    __table_args__ = {"comment": "龙虎榜机构成交明细 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    exalter: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="营业部名称/机构席位"
    )
    buy: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="买入金额(元)"
    )
    buy_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="买入占总成交比例(%)"
    )
    sell: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="卖出金额(元)"
    )
    sell_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="卖出占总成交比例(%)"
    )
    net_buy: Mapped[float] = mapped_column(
        Float, nullable=False, default=0, comment="净买入金额(元)"
    )
    side: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="0=买入 1=卖出"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="上榜原因"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawLimitList(TimestampMixin, Base):
    """涨停板股票列表 — Tushare limit_list_d."""
    __tablename__ = "raw_limit_list"
    __table_args__ = {"comment": "涨停板股票列表 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="股票名称"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="所属行业"
    )
    limit_type: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="涨停类型 (L=涨停, D=跌停)"
    )
    open_vol: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="开盘涨停封单量(万股)"
    )
    close_vol: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘涨停封单量(万股)"
    )
    open_amt: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="开盘涨停封单金额(万元)"
    )
    close_amt: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘涨停封单金额(万元)"
    )
    first_time: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="首次涨停时间"
    )
    last_time: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="最后涨停时间"
    )
    limit_times: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="连续涨停天数"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawTopList(TimestampMixin, Base):
    """龙虎榜明细 — Tushare top_list (15 API fields)."""
    __tablename__ = "raw_top_list"
    __table_args__ = {"comment": "龙虎榜明细 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="股票名称"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="上榜原因"
    )
    close: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="收盘价"
    )
    pct_change: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="涨跌幅(%)"
    )
    turnover_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="换手率(%)"
    )
    amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="成交额(万元)"
    )
    l_sell: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="龙虎榜卖出额(万元)"
    )
    l_buy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="龙虎榜买入额(万元)"
    )
    l_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="龙虎榜成交额(万元)"
    )
    net_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净买入额(万元)"
    )
    net_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净买率(%)"
    )
    amount_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="成交额占比(%)"
    )
    float_values: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="流通市值(万元)"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkLimit(TimestampMixin, Base):
    """涨跌停价格限制 — Tushare stk_limit."""
    __tablename__ = "raw_stk_limit"
    __table_args__ = {"comment": "涨跌停价格限制 — 原始API返回"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    pre_close: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="前收盘价"
    )
    up_limit: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="涨停价"
    )
    down_limit: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="跌停价"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawCyqChips(TimestampMixin, Base):
    """筹码分布 — Tushare cyq_chips.

    Each row = one price level's chip concentration for one stock on one day.
    Deduplicates on (ts_code, trade_date, price).
    """
    __tablename__ = "raw_cyq_chips"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", "price", name="uq_cyq_chips_ts_code_date_price"),
        {"comment": "筹码分布 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    price: Mapped[float] = mapped_column(
        Float, nullable=False, comment="价格区间"
    )
    percent: Mapped[float] = mapped_column(
        Float, nullable=False, comment="筹码占比(%)"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawCyqPerf(TimestampMixin, Base):
    """筹码表现 — Tushare cyq_perf.

    Each row = one stock's chip performance metrics on one day.
    Deduplicates on (ts_code, trade_date).
    """
    __tablename__ = "raw_cyq_perf"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_cyq_perf_ts_code_date"),
        {"comment": "筹码表现 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="交易日期"
    )
    his_low: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="历史最低价"
    )
    his_high: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="历史最高价"
    )
    cost_5pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="5%筹码成本"
    )
    cost_15pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="15%筹码成本"
    )
    cost_50pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="50%筹码成本"
    )
    cost_85pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="85%筹码成本"
    )
    cost_95pct: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="95%筹码成本"
    )
    weight_avg: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="加权平均成本"
    )
    winner_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="获利盘比例(%)"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkShock(TimestampMixin, Base):
    """个股异常波动 — Tushare stk_shock.

    Each row = one stock's abnormal volatility announcement on one day.
    同一只票同日可能多次异常波动，使用 (ts_code, trade_date, period) 唯一约束。
    """
    __tablename__ = "raw_stk_shock"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", "period", name="uq_stk_shock_ts_code_date_period"),
        {"comment": "个股异常波动 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="公告日期"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="股票名称"
    )
    trade_market: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="交易所"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="异常说明"
    )
    period: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="异常期间"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkHighShock(TimestampMixin, Base):
    """个股严重异常波动 — Tushare stk_high_shock.

    Each row = one stock's severe abnormal volatility announcement on one day.
    同一只票同日可能多次严重异常波动，使用 (ts_code, trade_date, period) 唯一约束。
    """
    __tablename__ = "raw_stk_high_shock"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", "period", name="uq_stk_high_shock_ts_code_date_period"),
        {"comment": "个股严重异常波动 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    trade_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="公告日期"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="股票名称"
    )
    trade_market: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="交易所"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="异常说明"
    )
    period: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="异常期间"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkAlert(TimestampMixin, Base):
    """交易所重点提示证券 — Tushare stk_alert.

    同一只票可能有多条提示（不同日期范围），使用 (ts_code, start_date, end_date) 唯一约束。
    """
    __tablename__ = "raw_stk_alert"
    __table_args__ = (
        UniqueConstraint("ts_code", "start_date", "end_date", name="uq_stk_alert_ts_code_start_end"),
        {"comment": "交易所重点提示证券 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="股票代码"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="股票名称"
    )
    start_date: Mapped[datetime] = mapped_column(
        Date, nullable=False, index=True, comment="提示起始日期"
    )
    end_date: Mapped[datetime] = mapped_column(
        Date, nullable=True, comment="提示截至日期"
    )
    type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="提示类型"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawSlbLen(TimestampMixin, Base):
    """转融通融资汇总 (slb_len) — 日频大盘数据.

    Source: Tushare slb_len API
    """
    __tablename__ = "raw_slb_len"
    __table_args__ = (
        UniqueConstraint("trade_date", name="uq_slb_len_trade_date"),
        {"comment": "转融通融资汇总 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True, comment="交易日期"
    )
    ob: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期初余额(亿元)")
    auc_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="竞价成交金额(亿元)")
    repo_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="再借成交金额(亿元)")
    repay_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="偿还金额(亿元)")
    cb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期末余额(亿元)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawLimitListThs(TimestampMixin, Base):
    """同花顺涨跌停榜单 (limit_list_ths) — 逐日.

    Source: Tushare limit_list_ths API
    Data from 2023-11-01, ~150 stocks/day across 5 limit_types.
    """
    __tablename__ = "raw_limit_list_ths"
    __table_args__ = (
        {"comment": "同花顺涨跌停榜单 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_num: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    lu_desc: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    limit_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_lu_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    last_lu_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    first_ld_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    last_ld_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    limit_order: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    limit_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_float: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lu_limit_order: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    limit_up_suc_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rise_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sum_float: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawLimitListD(TimestampMixin, Base):
    """涨跌停列表新版 (limit_list_d) — 逐日.

    Source: Tushare limit_list_d API
    Data from 2020, ~100 stocks/day across U/D/Z limit_types.
    """
    __tablename__ = "raw_limit_list_d"
    __table_args__ = (
        {"comment": "涨跌停列表新版 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    limit_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    float_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_mv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnover_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fd_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    last_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    open_times: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    up_stat: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    limit_times: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    lim: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawLimitStep(TimestampMixin, Base):
    """连板天梯 (limit_step) — 逐日.

    Source: Tushare limit_step API
    ~24 stocks/day, tracks consecutive limit-up count.
    """
    __tablename__ = "raw_limit_step"
    __table_args__ = (
        {"comment": "连板天梯 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    nums: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawLimitCptList(TimestampMixin, Base):
    """最强板块统计 (limit_cpt_list) — 逐日.

    Source: Tushare limit_cpt_list API
    ~20 concept sectors/day ranked by limit-up activity.
    """
    __tablename__ = "raw_limit_cpt_list"
    __table_args__ = (
        {"comment": "最强板块统计 — 原始API返回"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    ts_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    days: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    up_stat: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cons_nums: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    up_nums: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    pct_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
