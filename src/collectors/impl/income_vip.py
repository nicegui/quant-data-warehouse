"""利润表 VIP — IncomeVipCollector

使用 income_vip 接口, 一次性拉取全市场所有股票的利润表数据.
checkpoint_key = period (YYYYMMDD 格式报告期).
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.income import RawIncome
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f


class IncomeVipCollector(BaseTushareCollector):
    """利润表 VIP 全量 collector."""

    def __init__(self, token: str):
        super().__init__("income_vip", token)

    @property
    def checkpoint_key(self):
        return "period"

    def fetch(self, period: str = "", **kwargs) -> list[dict]:
        """调用 income_vip, period=YYYYMMDD."""
        params = {}
        if period:
            params["period"] = period
        return self.api_call("income_vip", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        """映射全部 80+ 字段, float 用 _f 处理 NaN."""
        # 所有字段名
        FIELDS = [
            "ts_code", "ann_date", "f_ann_date", "end_date",
            "report_type", "comp_type", "end_type",
            "basic_eps", "diluted_eps",
            "total_revenue", "revenue", "int_income", "prem_earned",
            "comm_income", "n_commis_income", "n_oth_income", "n_oth_b_income",
            "prem_income", "out_prem", "une_prem_reser", "reins_income",
            "n_sec_tb_income", "n_sec_uw_income", "n_asset_mg_income", "oth_b_income",
            "fv_value_chg_gain", "invest_income", "ass_invest_income", "forex_gain",
            "total_cogs", "oper_cost", "int_exp", "comm_exp",
            "biz_tax_surchg", "sell_exp", "admin_exp", "fin_exp", "assets_impair_loss",
            "prem_refund", "compens_payout", "reser_insur_liab", "div_payt",
            "reins_exp", "oper_exp", "compens_payout_refu", "insur_reser_refu",
            "reins_cost_refund", "other_bus_cost",
            "operate_profit", "non_oper_income", "non_oper_exp", "nca_disploss",
            "total_profit", "income_tax", "n_income", "n_income_attr_p", "minority_gain",
            "oth_compr_income", "t_compr_income", "compr_inc_attr_p", "compr_inc_attr_m_s",
            "ebit", "ebitda",
            "insurance_exp", "undist_profit", "distable_profit",
            "rd_exp", "fin_exp_int_exp", "fin_exp_int_inc",
            "transfer_surplus_rese", "transfer_housing_imprest", "transfer_oth",
            "adj_lossgain",
            "withdra_legal_surplus", "withdra_legal_pubfund", "withdra_biz_devfund",
            "withdra_rese_fund", "withdra_oth_ersu", "workers_welfare",
            "distr_profit_shrhder", "prfshare_payable_dvd", "comshare_payable_dvd",
            "capit_comstock_div",
            "net_after_nr_lp_correct", "credit_impa_loss",
            "net_expo_hedging_benefits", "oth_impair_loss_assets",
            "total_opcost", "amodcost_fin_assets", "oth_income",
            "asset_disp_income", "continued_net_profit", "end_net_profit",
            "update_flag",
        ]
        # 所有 float 字段 (非 str 的)
        STR_FIELDS = {"ts_code", "ann_date", "f_ann_date", "end_date",
                      "report_type", "comp_type", "end_type", "update_flag"}

        validated = []
        for row in raw:
            rec = {}
            for k in FIELDS:
                v = row.get(k)
                if k in STR_FIELDS:
                    rec[k] = v
                else:
                    rec[k] = _f(v)
            rec["raw_json"] = json.dumps(row, ensure_ascii=False, default=str)
            validated.append(rec)
        return validated
    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawIncome, records, ["ts_code", "end_date", "report_type"])
