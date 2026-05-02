"""财务指标 (fina_indicator_vip) — 全量 VIP 接口 (~130 fields)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawFinaIndicator(TimestampMixin, Base):
    """财务指标 (fina_indicator_vip)."""

    __tablename__ = "raw_fina_indicator"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "ann_date", name="uq_fi_ts_end_ann"),
        {"comment": "财务指标 — fina_indicator_vip 全量"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Per-share
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dt_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_revenue_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capital_rese_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surplus_rese_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    undist_profit_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_item: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_dedt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Margins
    gross_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quick_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cash_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invturn_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    arturn_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inv_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ar_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ca_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fa_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assets_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Operating income
    op_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    valuechange_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    interst_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcfe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_exint: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    noncurrent_exint: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    interestdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    netdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tangible_asset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    working_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    networking_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invest_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retained_earnings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diluted2_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocfps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retainedps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cfps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcff_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcfe_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Profitability ratios
    netprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grossprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cogs_of_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expense_of_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saleexp_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adminexp_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finaexp_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    impai_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gc_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ROE/ROA/ROIC
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_waa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_dt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    npta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa2_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Income structure
    opincome_of_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    investincome_of_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_op_profit_of_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tax_to_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dtprofit_to_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salescash_to_or: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_or: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_opincome: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capitalized_to_da: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Debt structure
    debt_to_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assets_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dp_assets_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ca_to_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nca_to_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tbassets_to_totalassets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    int_to_talcap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_to_talcapital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currentdebt_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longdeb_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_shortdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_to_interestdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tangibleasset_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tangasset_to_intdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tangibleasset_to_netdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_interestdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_netdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_to_interest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longdebt_to_workingcapital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebitda_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turn_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa_dp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional
    fixed_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_prefin_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    non_op_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_to_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nop_to_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_to_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cash_to_liqdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cash_to_liqdebt_withinterest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_to_liqdebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roic_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fa_trun: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_to_op: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Single-quarter
    q_opincome: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_investincome: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_dtprofit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_netprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_gsprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_exp_to_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_profit_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_saleexp_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_adminexp_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_finaexp_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_impair_to_gr_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_gc_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_op_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_dt_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_npta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_opincome_to_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_investincome_to_ebt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_dtprofit_to_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_salescash_to_or: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_ocf_to_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_ocf_to_or: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # YoY growth
    basic_eps_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dt_eps_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cfps_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebt_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    netprofit_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dt_netprofit_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocf_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bps_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assets_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tr_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    or_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Single-quarter YoY/QoQ
    q_gr_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_gr_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_sales_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_sales_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_op_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_op_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_profit_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_profit_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_netprofit_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_netprofit_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    rd_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="研发费用")
    update_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<RawFinaIndicator({self.ts_code} {self.end_date:%Y%m%d})>"
