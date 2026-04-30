"""Financial reports and indicators."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawFinancialReports(TimestampMixin, Base):
    """Raw financial report data from Tushare income API."""
    __tablename__ = "raw_financial_reports"
    __table_args__ = (
        {"comment": "财报利润表 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="报告期"
    )
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业总收入")
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业收入")
    oper_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业成本")
    total_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="利润总额")
    n_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润")
    n_income_attr_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母净利润")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFinancialIndicators(TimestampMixin, Base):
    """Raw financial indicators from Tushare fina_indicator API."""
    __tablename__ = "raw_financial_indicators"
    __table_args__ = (
        {"comment": "财务指标 (ROE/EPS/PE等) — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="报告期"
    )
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股收益")
    dt_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="稀释每股收益")
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股净资产")
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="ROE")
    roe_waa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加权ROE")
    roa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="ROA")
    npta: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总资产净利润率")
    grossprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="毛利率")
    netprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利率")
    debt_to_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="资产负债率")
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市盈率")
    pb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="市净率")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawExpress(TimestampMixin, Base):
    """Raw express (业绩快报) data from Tushare express API."""
    __tablename__ = "raw_express"
    __table_args__ = (
        {"comment": "业绩快报 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="报告期"
    )
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业收入")
    operate_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业利润")
    total_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="利润总额")
    n_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润")
    n_income_attr_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母净利润")
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总资产")
    paid_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="实收资本")
    total_hldr_eqy_exc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母权益")
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股收益")
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股净资产")
    weighted_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加权ROE")
    total_revenue_so: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业总收入(单季)")
    operate_profit_so: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业利润(单季)")
    n_income_so: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润(单季)")
    n_income_attr_p_so: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母净利润(单季)")
    update_flag: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="更新标识")
    yoy_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="EPS同比")
    yoy_net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润同比")
    grossprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="毛利率")
    netprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利率")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawBalanceSheet(TimestampMixin, Base):
    """Raw balance sheet (资产负债表) data from Tushare balancesheet API."""
    __tablename__ = "raw_balance_sheet"
    __table_args__ = (
        {"comment": "资产负债表 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="报告期"
    )
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="资产总计")
    total_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="负债合计")
    total_hldr_eqy_exc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母权益")
    total_cur_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动资产合计")
    total_cur_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动负债合计")
    goodwill: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="商誉")
    inventories: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存货")
    accounts_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收账款")
    notes_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收票据")
    fix_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产")
    total_nca: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="非流动资产合计")
    notes_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付票据")
    accounts_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付账款")
    long_borrow: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期借款")
    short_borrow: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="短期借款")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCashFlow(TimestampMixin, Base):
    """Raw cash flow (现金流量表) data from Tushare cashflow API."""
    __tablename__ = "raw_cash_flow"
    __table_args__ = (
        {"comment": "现金流量表 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="报告期"
    )
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    cash_recp_sg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="销售商品提供劳务收到的现金")
    cash_pay_acq: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="购买商品接受劳务支付的现金")
    cash_pay_beh_empl: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付给职工以及为职工支付的现金")
    st_cash_out_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动现金流出小计")
    st_cash_in_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动现金流入小计")
    n_cashflow_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动产生的现金流量净额")
    n_cashflow_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资活动产生的现金流量净额")
    n_cashflow_fin_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="筹资活动产生的现金流量净额")
    n_incr_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现金及现金等价物净增加额")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawForecast(TimestampMixin, Base):
    """业绩预告 (forecast).

    Source: Tushare forecast API
    One row per stock per reporting period.
    """

    __tablename__ = "raw_forecast"
    __table_args__ = (
        {"comment": "业绩预告 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="公告日期"
    )
    end_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="报告期"
    )
    type: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="预告类型"
    )
    p_change_min: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净利润同比最小变动幅度(%)"
    )
    p_change_max: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净利润同比最大变动幅度(%)"
    )
    net_profit_min: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净利润下限(万元)"
    )
    net_profit_max: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="净利润上限(万元)"
    )
    last_parent_net: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="上年同期归母净利润(万元)"
    )
    first_ann_date: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="首次公告日"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="业绩预告摘要"
    )
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="业绩变动原因"
    )
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )




class RawFinaAudit(TimestampMixin, Base):
    """审计意见 (fina_audit).

    Source: Tushare fina_audit API
    Fields: ts_code, ann_date, end_date, audit_result, audit_fees,
            audit_agency, audit_sign
    """
    __tablename__ = "raw_fina_audit"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "ann_date",
                         name="uq_raw_fina_audit_code_date"),
        {"comment": "审计意见 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期")
    audit_result: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="审计意见")
    audit_fees: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="审计费用(元)")
    audit_agency: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="审计机构")
    audit_sign: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="签字会计师")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawFinaMainbz(TimestampMixin, Base):
    """主营业务构成 (fina_mainbz).

    Source: Tushare fina_mainbz API
    Fields: ts_code, end_date, bz_item, bz_code, bz_sales, bz_profit,
            bz_cost, curr_type
    Note: bz_code = P(产品)/S(地区); the API param is called 'type'.
    """
    __tablename__ = "raw_fina_mainbz"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "bz_item",
                         name="uq_raw_fina_mainbz_code_item"),
        {"comment": "主营业务构成 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期")
    bz_item: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="业务项目")
    bz_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="类型: P产品/S地区")
    bz_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主营收入(元)")
    bz_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主营利润(元)")
    bz_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="主营成本(元)")
    curr_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="货币代码")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkHolderTrade(TimestampMixin, Base):
    """高管增减持 (stk_holdertrade) — 董监高持股变动.

    Source: Tushare stk_holdertrade API
    Fields: ts_code, ann_date, holder_name, holder_type, in_de,
            change_vol, change_ratio, after_share, after_ratio,
            avg_price, total_share
    """
    __tablename__ = "raw_stk_holder_trade"
    __table_args__ = (
        {"comment": "高管增减持 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    holder_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股东名称")
    holder_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="股东类型")
    in_de: Mapped[Optional[str]] = mapped_column(String(4), nullable=True, comment="增减: IN/DE")
    change_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="变动数量(股)")
    change_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="变动比例(%)")
    after_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="变动后持股(股)")
    after_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="变动后比例(%)")
    avg_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="均价")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总持股(股)")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawStkHolderTop(TimestampMixin, Base):
    """十大股东 (top10_holders) — 前十大股东明细.

    Source: Tushare top10_holders API
    Fields: ts_code, ann_date, end_date, holder_name, hold_amount,
            hold_ratio, hold_float_ratio, hold_change, holder_type
    """
    __tablename__ = "raw_stk_holder_top"
    __table_args__ = (
        {"comment": "十大股东 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期")
    holder_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, comment="股东名称")
    hold_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股数量(股)")
    hold_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股比例(%)")
    hold_float_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流通股比例(%)")
    hold_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持股变动")
    holder_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="股东类型")
    raw_json: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="完整API响应JSON"
    )


class RawRepurchase(TimestampMixin, Base):
    """回购 (repurchase).

    Source: Tushare repurchase API
    Fields: ts_code, ann_date, end_date, proc, exp_date,
            vol, amount, high_limit, low_limit
    """
    __tablename__ = "raw_repurchase"
    __table_args__ = (
        {"comment": "股票回购 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="截止日期")
    proc: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="进度: 实施/完成")
    exp_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="回购有效期")
    vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回购数量(股)")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回购金额(元)")
    high_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回购最高价")
    low_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回购最低价")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawPledgeStat(TimestampMixin, Base):
    """质押统计 (pledge_stat).

    Source: Tushare pledge_stat API
    Fields: ts_code, end_date, pledge_count, unrest_pledge,
            rest_pledge, total_share, pledge_ratio
    """
    __tablename__ = "raw_pledge_stat"
    __table_args__ = (
        {"comment": "质押统计 — 原始数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="统计日期")
    pledge_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="质押总笔数")
    unrest_pledge: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="无限售股质押数(万股)")
    rest_pledge: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="限售股质押数(万股)")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总股本(万股)")
    pledge_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="质押比例(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CuratedFinancialReports(TimestampMixin, Base):
    """Cleaned financial report data."""
    __tablename__ = "curated_financial_reports"
    __table_args__ = (
        {"comment": "财报 — 清洗数据"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ann_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="公告日期"
    )
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operating_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
