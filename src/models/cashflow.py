"""现金流量表 (cashflow_vip) — 全量 VIP 接口."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawCashFlow(TimestampMixin, Base):
    """现金流量表 — 全量 VIP 接口 (cashflow_vip)."""

    __tablename__ = "raw_cashflow"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "report_type", name="uq_cf_ts_end_report"),
        {"comment": "现金流量表 — cashflow_vip 全量"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ── 标识 ──
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="公告日期")
    f_ann_date: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="实际公告日期")
    end_date: Mapped[datetime] = mapped_column(nullable=False, index=True, comment="报告期")
    comp_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="公司类型")
    report_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, comment="报表类型")
    end_type: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="报告期类型")

    # ── 经营活动-流入 ──
    net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润")
    finan_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="财务费用")
    c_fr_sale_sg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="销售商品提供劳务收到的现金")
    recp_tax_rends: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到的税费返还")
    n_depos_incr_fi: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="客户存款和同业存放净增加")
    n_incr_loans_cb: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="向中央银行借款净增加")
    n_inc_borr_oth_fi: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="向其他金融机构拆入资金净增加")
    prem_fr_orig_contr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到原保险合同保费现金")
    n_incr_insured_dep: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保户储金净增加")
    n_reinsur_prem: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到再保业务现金净额")
    n_incr_disp_tfa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="处置交易性金融资产净增加")
    ifc_cash_incr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收取利息和手续费净增加")
    n_incr_disp_faas: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="处置可供出售金融资产净增加")
    n_incr_loans_oth_bank: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="拆入资金净增加")
    n_cap_incr_repur: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="回购业务资金净增加")
    c_fr_oth_operate_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到其他与经营活动有关的现金")
    c_inf_fr_operate_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动现金流入小计")

    # ── 经营活动-流出 ──
    c_paid_goods_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="购买商品接受劳务支付的现金")
    c_paid_to_for_empl: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付给职工以及为职工支付的现金")
    c_paid_for_taxes: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付的各项税费")
    n_incr_clt_loan_adv: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="客户贷款及垫款净增加")
    n_incr_dep_cbob: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存放央行和同业款项净增加")
    c_pay_claims_orig_inco: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付原保险合同赔付款项")
    pay_handling_chrg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付手续费的现金")
    pay_comm_insur_plcy: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付保单红利的现金")
    oth_cash_pay_oper_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付其他与经营活动有关的现金")
    st_cash_out_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动现金流出小计")
    n_cashflow_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动产生的现金流量净额")

    # ── 投资活动-流入 ──
    oth_recp_ral_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到其他与投资活动有关的现金")
    c_disp_withdrwl_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收回投资收到的现金")
    c_recp_return_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="取得投资收益收到的现金")
    n_recp_disp_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="处置固定无形资产等收回的现金净额")
    n_recp_disp_sobu: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="处置子公司及其他营业单位收到的现金净额")
    stot_inflows_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资活动现金流入小计")

    # ── 投资活动-流出 ──
    c_pay_acq_const_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="购建固定无形资产等支付的现金")
    c_paid_invest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资支付的现金")
    n_disp_subs_oth_biz: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="取得子公司及其他营业单位支付的现金净额")
    oth_pay_ral_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付其他与投资活动有关的现金")
    n_incr_pledge_loan: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="质押贷款净增加")
    stot_out_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资活动现金流出小计")
    n_cashflow_inv_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资活动产生的现金流量净额")

    # ── 筹资活动-流入 ──
    c_recp_borrow: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="取得借款收到的现金")
    proc_issue_bonds: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="发行债券收到的现金")
    oth_cash_recp_ral_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收到其他与筹资活动有关的现金")
    stot_cash_in_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="筹资活动现金流入小计")

    # ── 筹资活动-流出 ──
    free_cashflow: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="企业自由现金流量")
    c_prepay_amt_borr: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="偿还债务支付的现金")
    c_pay_dist_dpcp_int_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="分配股利利润或偿付利息支付的现金")
    incl_dvd_profit_paid_sc_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中子公司支付给少数股东的股利")
    oth_cashpay_ral_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="支付其他与筹资活动有关的现金")
    stot_cashout_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="筹资活动现金流出小计")
    n_cash_flows_fnc_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="筹资活动产生的现金流量净额")

    # ── 现金净额 ──
    eff_fx_flu_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="汇率变动对现金的影响")
    n_incr_cash_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现金及现金等价物净增加额")
    c_cash_equ_beg_period: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期初现金及现金等价物余额")
    c_cash_equ_end_period: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="期末现金及现金等价物余额")
    c_recp_cap_contrib: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="吸收投资收到的现金")
    incl_cash_rec_saims: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中子公司吸收少数股东投资收到的现金")

    # ── 间接法 ──
    uncon_invest_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="未确认投资损失")
    prov_depr_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加资产减值准备")
    depr_fa_coga_dpba: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产折旧油气资产折耗生物资产折旧")
    amort_intang_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="无形资产摊销")
    lt_amort_deferred_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="长期待摊费用摊销")
    decr_deferred_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="待摊费用减少")
    incr_acc_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预提费用增加")
    loss_disp_fiolta: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="处置固定无形资产和其他长期资产的损失")
    loss_scr_fa: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="固定资产报废损失")
    loss_fv_chg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="公允价值变动损失")
    invest_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="投资损失")
    decr_def_inc_tax_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延所得税资产减少")
    incr_def_inc_tax_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="递延所得税负债增加")
    decr_inventories: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="存货的减少")
    decr_oper_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营性应收项目的减少")
    incr_oper_payable: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营性应付项目的增加")
    others: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他")
    im_net_cashflow_oper_act: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="经营活动现金流量净额间接法")
    conv_debt_into_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="债务转为资本")
    conv_copbonds_due_within_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="一年内到期的可转换公司债券")
    fa_fnc_leases: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="融资租入固定资产")
    im_n_incr_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现金及现金等价物净增加额间接法")

    # ── 新增 ──
    net_dism_capital_add: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="拆出资金净增加")
    net_cash_rece_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="代理买卖证券收到的现金净额")
    credit_impa_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="信用减值损失")
    use_right_asset_dep: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="使用权资产折旧")
    oth_loss_asset: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他资产减值损失")
    end_bal_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="现金的期末余额")
    beg_bal_cash: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减现金的期初余额")
    end_bal_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加现金等价物的期末余额")
    beg_bal_cash_equ: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减现金等价物的期初余额")

    # ── 元数据 ──
    update_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="更新标志")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应")

    def __repr__(self):
        return f"<RawCashFlow({self.ts_code} {self.end_date:%Y%m%d} rpt={self.report_type})>"
