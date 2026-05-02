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
    """财务指标 (ROE/EPS/PE等) — 原始数据 (108 fields)"""
    __tablename__ = "raw_financial_indicators"
    __table_args__ = (
        {"comment": "财务指标 (ROE/EPS/PE等) — 原始数据 (108 fields)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=False, comment="报告期")
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dt_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_revenue_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    capital_rese_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surplus_rese_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    undist_profit_ps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_item: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_dedt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    current_ratio: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    quick_ratio: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cash_ratio: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ar_turn: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ca_turn: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fa_turn: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    assets_turn: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ebitda: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fcff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcfe: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    current_exint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    noncurrent_exint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    interestdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    netdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tangible_asset: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    working_capital: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    networking_capital: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    invest_capital: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    retained_earnings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diluted2_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocfps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retainedps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cfps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_ps: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fcff_ps: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fcfe_ps: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    netprofit_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grossprofit_margin: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cogs_of_sales: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    expense_of_sales: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    profit_to_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saleexp_to_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    adminexp_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finaexp_of_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    impai_ttm: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    gc_of_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    op_of_gr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ebit_of_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_waa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe_dt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    npta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roic: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    roe_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa2_yearly: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    debt_to_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assets_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dp_assets_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ca_to_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    nca_to_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tbassets_to_totalassets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    int_to_talcap: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    eqt_to_talcapital: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    currentdebt_to_debt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    longdeb_to_debt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ocf_to_shortdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    debt_to_eqt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eqt_to_interestdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tangibleasset_to_debt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tangasset_to_intdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tangibleasset_to_netdebt: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ocf_to_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turn_days: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    roa_yearly: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roa_dp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fixed_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_to_op: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_saleexp_to_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    q_gc_to_gr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    q_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_dt_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_npta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_ocf_to_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    q_sales_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q_op_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="总资产")
    total_hldr_eqy_exc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归母权益")
    diluted_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="稀释每股收益")
    diluted_roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="稀释ROE")
    yoy_net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润同比")
    bps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="每股净资产")
    perf_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="业绩摘要")
    update_flag: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="更新标识")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawBalanceSheet(TimestampMixin, Base):
    """资产负债表 — 原始数据 (152 fields)"""
    __tablename__ = "raw_balance_sheet"
    __table_args__ = (
        {"comment": "资产负债表 — 原始数据 (152 fields)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=False, comment="报告期")
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    end_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期类型")
    update_flag: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="更新标识")
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cap_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    undistr_porfit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surplus_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    special_rese: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    money_cap: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    trad_asset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    accounts_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    prepayment: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    div_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    int_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    inventories: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    amor_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    nca_within_1y: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sett_rsrv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    loanto_oth_bank_fi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    premium_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reinsur_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reinsur_res_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pur_resale_fa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_cur_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_cur_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fa_avail_for_sale: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    htm_invest: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lt_eqt_invest: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    invest_real_estate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_deposits: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_rec: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fix_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cip: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    const_materials: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fixed_assets_disp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    produc_bio_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oil_and_gas_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    intan_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    r_and_d: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    goodwill: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_amor_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    defer_tax_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    decr_in_disbur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_nca: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_nca: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cash_reser_cb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depos_in_oth_bfi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prec_metals: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deriv_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rr_reins_une_prem: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rr_reins_outstd_cla: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rr_reins_lins_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rr_reins_lthins_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    refund_depos: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ph_pledge_loans: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    refund_cap_depos: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    indep_acct_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    client_depos: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    client_prov: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    transac_seat_fee: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    invest_as_receiv: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_borr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    st_borr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cb_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depos_ib_deposits: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    loan_oth_bank: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trading_fl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acct_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    adv_receipts: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sold_for_repur_fa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    comm_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payroll_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    taxes_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    int_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    div_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acc_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    deferred_inc: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    st_bonds_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payable_to_reinsurer: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rsrv_insur_cont: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acting_trading_sec: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acting_uw_sec: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    non_cur_liab_due_1y: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_cur_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_cur_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    bond_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    specific_payables: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    estimated_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    defer_tax_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    defer_inc_non_cur_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_ncl: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_ncl: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    depos_oth_bfi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deriv_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depos: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    agency_bus_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prem_receiv_adva: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    depos_received: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ph_invest: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reser_une_prem: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reser_outstd_claims: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reser_lins_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reser_lthins_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    indept_acc_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pledge_borr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    indem_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    policy_div_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    treasury_share: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ordin_risk_reser: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forex_differ: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    invest_loss_unconf: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    minority_int: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_hldr_eqy_exc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_hldr_eqy_inc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_liab_hldr_eqy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_payroll_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_comp_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_eqt_tools: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_eqt_tools_p_shr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lending_funds: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    acc_receivable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    st_fin_payable: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payables: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hfs_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hfs_sales: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cost_fin_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fair_value_fin_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contract_assets: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contract_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    accounts_receiv_bill: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    accounts_pay: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_rcv_total: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fix_assets_total: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    cip_total: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_pay_total: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    long_pay_total: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    debt_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_debt_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
class RawCashFlow(TimestampMixin, Base):
    """现金流量表 — 原始数据 (97 fields)"""
    __tablename__ = "raw_cash_flow"
    __table_args__ = (
        {"comment": "现金流量表 — 原始数据 (97 fields)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=False, comment="报告期")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    end_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告期类型")
    update_flag: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="更新标识")
    net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    finan_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    c_fr_sale_sg: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    recp_tax_rends: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_depos_incr_fi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_incr_loans_cb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_inc_borr_oth_fi: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    prem_fr_orig_contr: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_incr_insured_dep: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_reinsur_prem: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_incr_disp_tfa: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ifc_cash_incr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_incr_disp_faas: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_incr_loans_oth_bank: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_cap_incr_repur: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    c_fr_oth_operate_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_inf_fr_operate_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_paid_goods_s: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    c_paid_to_for_empl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_paid_for_taxes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_incr_clt_loan_adv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_incr_dep_cbob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_pay_claims_orig_inco: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pay_handling_chrg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pay_comm_insur_plcy: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_cash_pay_oper_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    st_cash_out_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_cashflow_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_recp_ral_inv_act: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    c_disp_withdrwl_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_recp_return_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_recp_disp_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_recp_disp_sobu: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    stot_inflows_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_pay_acq_const_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_paid_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_disp_subs_oth_biz: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_pay_ral_inv_act: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    n_incr_pledge_loan: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    stot_out_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_cashflow_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_recp_borrow: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    proc_issue_bonds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_cash_recp_ral_fnc_act: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    stot_cash_in_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_cashflow: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_prepay_amt_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_pay_dist_dpcp_int_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    incl_dvd_profit_paid_sc_ms: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    oth_cashpay_ral_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stot_cashout_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_cash_flows_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eff_fx_flu_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    n_incr_cash_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_cash_equ_beg_period: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_cash_equ_end_period: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    c_recp_cap_contrib: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    incl_cash_rec_saims: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    uncon_invest_loss: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    prov_depr_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depr_fa_coga_dpba: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amort_intang_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lt_amort_deferred_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    decr_deferred_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    incr_acc_exp: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    loss_disp_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    loss_scr_fa: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    loss_fv_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    invest_loss: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    decr_def_inc_tax_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    incr_def_inc_tax_liab: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    decr_inventories: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    decr_oper_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    incr_oper_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    others: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    im_net_cashflow_oper_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    conv_debt_into_cap: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    conv_copbonds_due_within_1y: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    fa_fnc_leases: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    im_n_incr_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_dism_capital_add: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_cash_rece_sec: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    credit_impa_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    use_right_asset_dep: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oth_loss_asset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_bal_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beg_bal_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_bal_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beg_bal_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    holder_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, comment="股东名称")
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


class RawPledgeDetail(TimestampMixin, Base):
    """股权质押明细 (pledge_detail)."""
    __tablename__ = "raw_pledge_detail"
    __table_args__ = ({"comment": "股权质押明细 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    holder_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pledge_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    is_release: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    release_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    pledgor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    holding_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pledged_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p_total_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    h_total_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_buyback: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class RawStkHolderFloatTop(TimestampMixin, Base):
    """十大流通股东 (top10_floatholders)."""
    __tablename__ = "raw_stk_holder_float_top"
    __table_args__ = ({"comment": "十大流通股东 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    holder_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    hold_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hold_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hold_float_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hold_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    holder_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class RawStkManagers(TimestampMixin, Base):
    """上市公司管理层 (stk_managers)."""
    __tablename__ = "raw_stk_managers"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    lev: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    edu: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    national: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    birthday: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    begin_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

class RawStkRewards(TimestampMixin, Base):
    """管理层薪酬 (stk_rewards)."""
    __tablename__ = "raw_stk_rewards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hold_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RawReportRc(TimestampMixin, Base):
    """卖方盈利预测 (report_rc)."""
    __tablename__ = "raw_report_rc"
    __table_args__ = ({"comment": "卖方盈利预测 — 原始数据"},)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    report_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    report_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    report_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    classify: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    org_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    quarter: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    op_rt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_pr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    np: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rating: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
