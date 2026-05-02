"""资产负债表 (balancesheet_vip) — 全量 VIP 接口."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawBalanceSheet(TimestampMixin, Base):
    """资产负债表 — 全量 VIP 接口 (balancesheet_vip).

    period=YYYYMMDD 格式报告期, 一次拉全市场所有股票.
    """

    __tablename__ = "raw_balance_sheet"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "report_type", name="uq_bs_ts_end_report"),
        {"comment": "资产负债表 — balancesheet_vip 全量"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ── 标识字段 ──
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True, comment="报告期")
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报告类型")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    end_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="报告期类型")

    # ── 权益 ──
    total_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期末总股本")
    cap_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="资本公积金")
    undistr_porfit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未分配利润")
    surplus_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈余公积金")
    special_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="专项储备")

    # ── 流动资产 ──
    money_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="货币资金")
    trad_asset: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="交易性金融资产")
    notes_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收票据")
    accounts_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收账款")
    oth_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他应收款")
    prepayment: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预付款项")
    div_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收股利")
    int_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收利息")
    inventories: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存货")
    amor_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="待摊费用")
    nca_within_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="一年内到期的非流动资产")
    sett_rsrv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="结算备付金")
    loanto_oth_bank_fi: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="拆出资金")
    premium_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收保费")
    reinsur_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保账款")
    reinsur_res_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保合同准备金")
    pur_resale_fa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买入返售金融资产")
    oth_cur_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他流动资产")
    total_cur_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动资产合计")

    # ── 非流动资产 ──
    fa_avail_for_sale: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="可供出售金融资产")
    htm_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持有至到期投资")
    lt_eqt_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期股权投资")
    invest_real_estate: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资性房地产")
    time_deposits: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="定期存款")
    oth_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他资产")
    lt_rec: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期应收款")
    fix_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产")
    cip: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="在建工程")
    const_materials: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="工程物资")
    fixed_assets_disp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产清理")
    produc_bio_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="生产性生物资产")
    oil_and_gas_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="油气资产")
    intan_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="无形资产")
    r_and_d: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="研发支出")
    goodwill: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="商誉")
    lt_amor_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期待摊费用")
    defer_tax_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延所得税资产")
    decr_in_disbur: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="发放贷款及垫款")
    oth_nca: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他非流动资产")
    total_nca: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="非流动资产合计")

    # ── 金融/保险专项资产 ──
    cash_reser_cb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现金及存放中央银行款项")
    depos_in_oth_bfi: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存放同业和其它金融机构款项")
    prec_metals: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="贵金属")
    deriv_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="衍生金融资产")
    rr_reins_une_prem: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保未到期责任准备金")
    rr_reins_outstd_cla: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保未决赔款准备金")
    rr_reins_lins_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保寿险责任准备金")
    rr_reins_lthins_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收分保长期健康险责任准备金")
    refund_depos: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存出保证金")
    ph_pledge_loans: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保户质押贷款")
    refund_cap_depos: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存出资本保证金")
    indep_acct_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="独立账户资产")
    client_depos: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中：客户资金存款")
    client_prov: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中：客户备付金")
    transac_seat_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中:交易席位费")
    invest_as_receiv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收款项类投资")

    # ── 资产总计 ──
    total_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="资产总计")

    # ── 负债-短期 ──
    lt_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期借款")
    st_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="短期借款")
    cb_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="向中央银行借款")
    depos_ib_deposits: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="吸收存款及同业存放")
    loan_oth_bank: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="拆入资金")
    trading_fl: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="交易性金融负债")
    notes_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付票据")
    acct_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付账款")
    adv_receipts: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预收款项")
    sold_for_repur_fa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖出回购金融资产款")
    comm_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付手续费及佣金")
    payroll_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付职工薪酬")
    taxes_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应交税费")
    int_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付利息")
    div_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付股利")
    oth_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他应付款")
    acc_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预提费用")
    deferred_inc: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延收益")
    st_bonds_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付短期债券")
    payable_to_reinsurer: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付分保账款")
    rsrv_insur_cont: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保险合同准备金")
    acting_trading_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="代理买卖证券款")
    acting_uw_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="代理承销证券款")
    non_cur_liab_due_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="一年内到期的非流动负债")
    oth_cur_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他流动负债")
    total_cur_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="流动负债合计")

    # ── 负债-长期 ──
    bond_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付债券")
    lt_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期应付款")
    specific_payables: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="专项应付款")
    estimated_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预计负债")
    defer_tax_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延所得税负债")
    defer_inc_non_cur_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延收益-非流动负债")
    oth_ncl: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他非流动负债")
    total_ncl: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="非流动负债合计")

    # ── 金融/保险专项负债 ──
    depos_oth_bfi: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="同业和其它金融机构存放款项")
    deriv_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="衍生金融负债")
    depos: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="吸收存款")
    agency_bus_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="代理业务负债")
    oth_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他负债")
    prem_receiv_adva: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预收保费")
    depos_received: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存入保证金")
    ph_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保户储金及投资款")
    reser_une_prem: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未到期责任准备金")
    reser_outstd_claims: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未决赔款准备金")
    reser_lins_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="寿险责任准备金")
    reser_lthins_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期健康险责任准备金")
    indept_acc_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="独立账户负债")
    pledge_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中:质押借款")
    indem_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付赔付款")
    policy_div_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付保单红利")

    # ── 负债合计 ──
    total_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="负债合计")

    # ── 股东权益 ──
    treasury_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:库存股")
    ordin_risk_reser: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="一般风险准备")
    forex_differ: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="外币报表折算差额")
    invest_loss_unconf: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未确认的投资损失")
    minority_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="少数股东权益")
    total_hldr_eqy_exc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股东权益合计(不含少数股东权益)")
    total_hldr_eqy_inc_min_int: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="股东权益合计(含少数股东权益)")
    total_liab_hldr_eqy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="负债及股东权益总计")
    lt_payroll_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期应付职工薪酬")
    oth_comp_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他综合收益")
    oth_eqt_tools: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他权益工具")
    oth_eqt_tools_p_shr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他权益工具(优先股)")

    # ── 券商专项 ──
    lending_funds: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="融出资金")
    acc_receivable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收款项")
    st_fin_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付短期融资款")
    payables: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付款项")

    # ── 持有待售 ──
    hfs_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持有待售的资产")
    hfs_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持有待售的负债")

    # ── 新增 ──
    cost_fin_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="以摊余成本计量的金融资产")
    fair_value_fin_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="FVOCI金融资产")
    cip_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="在建工程(合计)")
    oth_pay_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他应付款(合计)")
    long_pay_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期应付款(合计)")
    debt_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="债权投资")
    oth_debt_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他债权投资")
    oth_eq_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他权益工具投资")
    oth_illiq_fin_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他非流动金融资产")
    oth_eq_ppbond: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他权益工具:永续债")
    receiv_financing: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收款项融资")
    use_right_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="使用权资产")
    lease_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="租赁负债")
    contract_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="合同资产")
    contract_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="合同负债")
    accounts_receiv_bill: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应收票据及应收账款")
    accounts_pay: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付票据及应付账款")
    oth_rcv_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他应收款(合计)")
    fix_assets_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产(合计)")

    # ── 元数据 ──
    update_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="更新标识")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应")

    def __repr__(self):
        return f"<RawBalanceSheet({self.ts_code} {self.end_date:%Y%m%d} rpt={self.report_type})>"
