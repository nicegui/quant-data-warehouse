"""利润表 (income_vip) — 全量 VIP 接口."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RawIncome(TimestampMixin, Base):
    """利润表 — 全量 VIP 接口 (income_vip).

    period=YYYYMMDD 格式报告期, 一次拉全市场所有股票.
    """

    __tablename__ = "raw_income"
    __table_args__ = (
        UniqueConstraint("ts_code", "end_date", "report_type", name="uq_income_ts_end_report"),
        {"comment": "利润表 — income_vip 全量"},
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

    # ── 每股指标 ──
    basic_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="基本每股收益")
    diluted_eps: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="稀释每股收益")

    # ── 收入 ──
    total_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业总收入")
    revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业收入")
    int_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="利息收入")
    prem_earned: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="已赚保费")
    comm_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="手续费及佣金收入")
    n_commis_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="手续费及佣金净收入")
    n_oth_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他经营净收益")
    n_oth_b_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加:其他业务净收益")
    prem_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保险业务收入")
    out_prem: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:分出保费")
    une_prem_reser: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取未到期责任准备金")
    reins_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中:分保费收入")
    n_sec_tb_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="代理买卖证券业务净收入")
    n_sec_uw_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="证券承销业务净收入")
    n_asset_mg_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="受托客户资产管理业务净收入")
    oth_b_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他业务收入")

    # ── 收益 ──
    fv_value_chg_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加:公允价值变动净收益")
    invest_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加:投资净收益")
    ass_invest_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中:对联营企业和合营企业的投资收益")
    forex_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加:汇兑净收益")

    # ── 成本 ──
    total_cogs: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业总成本")
    oper_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:营业成本")
    int_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:利息支出")
    comm_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:手续费及佣金支出")
    biz_tax_surchg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:营业税金及附加")
    sell_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:销售费用")
    admin_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:管理费用")
    fin_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:财务费用")
    assets_impair_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:资产减值损失")

    # ── 保险专项 ──
    prem_refund: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="退保金")
    compens_payout: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="赔付总支出")
    reser_insur_liab: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取保险责任准备金")
    div_payt: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保户红利支出")
    reins_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="分保费用")
    oper_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业支出")
    compens_payout_refu: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:摊回赔付支出")
    insur_reser_refu: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:摊回保险责任准备金")
    reins_cost_refund: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:摊回分保费用")
    other_bus_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他业务成本")

    # ── 利润 ──
    operate_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业利润")
    non_oper_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="加:营业外收入")
    non_oper_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="减:营业外支出")
    nca_disploss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其中:减:非流动资产处置净损失")
    total_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="利润总额")
    income_tax: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="所得税费用")
    n_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润(含少数股东损益)")
    n_income_attr_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净利润(不含少数股东损益)")
    minority_gain: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="少数股东损益")

    # ── 综合收益 ──
    oth_compr_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他综合收益")
    t_compr_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="综合收益总额")
    compr_inc_attr_p: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归属于母公司(或股东)的综合收益总额")
    compr_inc_attr_m_s: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="归属于少数股东的综合收益总额")

    # ── 税息 ──
    ebit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="息税前利润")
    ebitda: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="息税折旧摊销前利润")

    # ── 保险 + 未分配 ──
    insurance_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="保险业务支出")
    undist_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="年初未分配利润")
    distable_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="可分配利润")

    # ── 研发 + 财务费用明细 ──
    rd_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="研发费用")
    fin_exp_int_exp: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="财务费用:利息费用")
    fin_exp_int_inc: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="财务费用:利息收入")

    # ── 公积金 / 转入 ──
    transfer_surplus_rese: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="盈余公积转入")
    transfer_housing_imprest: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="住房周转金转入")
    transfer_oth: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他转入")
    adj_lossgain: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="调整以前年度损益")

    # ── 股东分配 ──
    withdra_legal_surplus: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取法定盈余公积")
    withdra_legal_pubfund: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取法定公益金")
    withdra_biz_devfund: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取企业发展基金")
    withdra_rese_fund: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取储备基金")
    withdra_oth_ersu: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="提取任意盈余公积金")
    workers_welfare: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="职工奖金福利")
    distr_profit_shrhder: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="可供股东分配的利润")
    prfshare_payable_dvd: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付优先股股利")
    comshare_payable_dvd: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="应付普通股股利")
    capit_comstock_div: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="转作股本的普通股股利")

    # ── 新增字段 (nullable=N 在 API 文档) ──
    net_after_nr_lp_correct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="扣除非经常性损益后的净利润（更正前）")
    credit_impa_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="信用减值损失")
    net_expo_hedging_benefits: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="净敞口套期收益")
    oth_impair_loss_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他资产减值损失")
    total_opcost: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="营业总成本（二）")
    amodcost_fin_assets: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="以摊余成本计量的金融资产终止确认收益")
    oth_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="其他收益")
    asset_disp_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="资产处置收益")
    continued_net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持续经营净利润")
    end_net_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="终止经营净利润")

    # ── 元数据 ──
    update_flag: Mapped[Optional[str]] = mapped_column(String(1), nullable=True, comment="更新标识")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="完整API响应")

    def __repr__(self):
        return f"<RawIncome({self.ts_code} {self.end_date:%Y%m%d} rpt={self.report_type})>"
