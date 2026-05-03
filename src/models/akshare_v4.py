"""Models for 全球宏观+LPR+可转债+期权+ETF+失业率 — akshare v4."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawGlobalMacro(TimestampMixin, Base):
    """全球宏观日历 — USA/Europe/Japan unified format."""

    __tablename__ = "raw_global_macro"
    __table_args__ = (
        UniqueConstraint("source", "item", "date_str", name="uq_gm_src_item_date"),
        {"comment": "全球宏观日历(今值/预测值/前值) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="数据源: usa_cpi/usa_nfp/usa_unemp/usa_conf/usa_gdp/usa_retail/usa_trade/euro_cpi/euro_gdp/japan_rate/japan_cpi")
    item: Mapped[str] = mapped_column(String(128), nullable=False, comment="指标名称")
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今值")
    forecast: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测值")
    previous: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="前值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawLprRate(TimestampMixin, Base):
    """LPR利率 — akshare macro_china_lpr()."""

    __tablename__ = "raw_lpr_rate"
    __table_args__ = (
        UniqueConstraint("trade_date", name="uq_lpr_date"),
        {"comment": "LPR贷款市场报价利率 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    lpr_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="1年期LPR(%)")
    lpr_5y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="5年期LPR(%)")
    rate_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="短期利率1")
    rate_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="短期利率2")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCbIndex(TimestampMixin, Base):
    """可转债等权指数 — akshare bond_cb_index_jsl()."""

    __tablename__ = "raw_cb_index"
    __table_args__ = (
        UniqueConstraint("price_date", name="uq_cbi_date"),
        {"comment": "可转债等权指数 — 集思录"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    price_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="指数价格")
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交额(亿)")
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="成交量(万手)")
    count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="转债数量")
    increase_val: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌额")
    increase_rt: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    avg_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="均价")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawHs300Option(TimestampMixin, Base):
    """沪深300股指期权 — akshare option_cffex_hs300_spot_sina()."""

    __tablename__ = "raw_hs300_option"
    __table_args__ = (
        UniqueConstraint("trade_date", "strike", "opt_type", name="uq_hso_date_strike_type"),
        {"comment": "沪深300股指期权 — 新浪"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    opt_type: Mapped[str] = mapped_column(String(8), nullable=False, comment="CALL/PUT")
    strike: Mapped[float] = mapped_column(Float, nullable=False, comment="行权价")
    buy_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买量")
    bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买价")
    last: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最新价")
    ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖价")
    sell_vol: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖量")
    position: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="持仓量")
    change: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawEtfScale(TimestampMixin, Base):
    """ETF规模 — akshare fund_etf_scale_sse()."""

    __tablename__ = "raw_etf_scale"
    __table_args__ = (
        UniqueConstraint("fund_code", "stat_date", name="uq_es_code_date"),
        {"comment": "ETF规模(上交所) — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fund_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    etf_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    stat_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    shares: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="基金份额(万份)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawUnemployment(TimestampMixin, Base):
    """城镇失业率 — akshare macro_china_urban_unemployment()."""

    __tablename__ = "raw_unemployment"
    __table_args__ = (
        UniqueConstraint("date_str", "item", name="uq_ue_date_item"),
        {"comment": "城镇失业率 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    item: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
