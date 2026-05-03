"""Models for BDI航运+商品价格+国债+回购+工业+热搜+汇率+美股 — akshare v3."""

from __future__ import annotations
from typing import Optional
from sqlalchemy import BigInteger, Float, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base, TimestampMixin


class RawShippingIndex(TimestampMixin, Base):
    """BDI/BCI 航运指数 — akshare macro_shipping_bdi/bci()."""

    __tablename__ = "raw_shipping_index"
    __table_args__ = (
        UniqueConstraint("date_str", "index_type", name="uq_si_date_type"),
        {"comment": "BDI/BCI航运指数 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    index_type: Mapped[str] = mapped_column(String(8), nullable=False, comment="指数类型: BDI/BCI")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最新值")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    chg_3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3月涨跌幅(%)")
    chg_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近6月涨跌幅(%)")
    chg_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近1年涨跌幅(%)")
    chg_2y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近2年涨跌幅(%)")
    chg_3y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3年涨跌幅(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawCommodityPrice(TimestampMixin, Base):
    """商品价格指数 — akshare macro_china_commodity_price_index()."""

    __tablename__ = "raw_commodity_price"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_cp_date"),
        {"comment": "商品价格指数 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="最新值")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    chg_3m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3月涨跌幅(%)")
    chg_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近6月涨跌幅(%)")
    chg_1y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近1年涨跌幅(%)")
    chg_2y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近2年涨跌幅(%)")
    chg_3y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="近3年涨跌幅(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawYieldCurve(TimestampMixin, Base):
    """国债收益率曲线 — akshare bond_china_close_return_map()."""

    __tablename__ = "raw_yield_curve_ak"
    __table_args__ = (
        UniqueConstraint("term", name="uq_yc_term"),
        {"comment": "国债收益率曲线 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(16), nullable=False, comment="期限标识")
    cn_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="中文标签")
    en_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="英文标签")
    yield_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="收益率(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawRepoRate(TimestampMixin, Base):
    """回购定盘利率 — akshare repo_rate_query()."""

    __tablename__ = "raw_repo_rate"
    __table_args__ = (
        UniqueConstraint("date_str", name="uq_rr_date"),
        {"comment": "回购定盘利率 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    fr001: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="FR001(%)")
    fr007: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="FR007(%)")
    fr014: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="FR014(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawIndustrialProduction(TimestampMixin, Base):
    """工业增加值(宏观日历格式) — akshare macro_china_industrial_production_yoy()."""

    __tablename__ = "raw_industrial_production"
    __table_args__ = (
        UniqueConstraint("date_str", "item", name="uq_ip_date_item"),
        {"comment": "工业增加值 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(String(64), nullable=False, comment="指标名称")
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="今值")
    forecast: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="预测值")
    previous: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="前值")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawBaiduHotSearch(TimestampMixin, Base):
    """百度热搜 — akshare stock_hot_search_baidu()."""

    __tablename__ = "raw_baidu_hot_search"
    __table_args__ = (
        UniqueConstraint("date_str", "name", name="uq_bhs_date_name"),
        {"comment": "百度热搜 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="名称/代码")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    heat: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="综合热度")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawFxSpot(TimestampMixin, Base):
    """外汇即期报价 — akshare fx_spot_quote()."""

    __tablename__ = "raw_fx_spot"
    __table_args__ = (
        UniqueConstraint("pair", name="uq_fx_pair"),
        {"comment": "外汇即期报价 — akshare"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(16), nullable=False, comment="货币对")
    bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="买报价")
    ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="卖报价")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RawUsStockDaily(TimestampMixin, Base):
    """美股日线(akshare源) — akshare stock_us_hist()."""

    __tablename__ = "raw_us_stock_daily"
    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_usd_sym_date"),
        {"comment": "美股日线(akshare) — S&P500成分股"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="股票代码")
    trade_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="日期")
    open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amplitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="振幅(%)")
    change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌幅(%)")
    change_amt: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="涨跌额")
    turnover: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="换手率(%)")
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
