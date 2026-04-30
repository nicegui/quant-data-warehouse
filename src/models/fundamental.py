"""Financial reports and indicators."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text
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
