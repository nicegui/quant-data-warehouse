"""Alpha158 因子集 — qlib 风格

Reference: Microsoft qlib Alpha158 handler
  https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/handler.py

158 factors across 6 categories:
  - KDAY:  OHLCV raw values + VWAP + turnover
  - PRICE: return/chg/amplitude over 5/10/20/30/60 days
  - VOLUME: volume/amount rolling stats
  - ROLLING: rolling mean/std/max/min/skew/kurt of close/volume
  - TECH: RSI, MACD, KDJ, OBV
  - GROWTH: YoY growth on financial indicators (需要财务数据)

注意: 这里只注册表达式因子; 代码因子在 custom.py。
"""

from src.factors.registry import register_factor

# ═══════════════════════════════════════════
# KDAY — 基础量价 (直接引用，无表达式)
# ═══════════════════════════════════════════
# $open, $high, $low, $close, $volume, $amount, $vwap, $turnover
# 这些是基础变量，不需要表达式注册


# ═══════════════════════════════════════════
# PRICE — 价格衍生因子 (returns / change / amplitude)
# ═══════════════════════════════════════════

@register_factor("price", "ret_1d")
def ret_1d():
    """1日收益率"""
    return "Ref($close, -1) / $close - 1"

@register_factor("price", "ret_3d")
def ret_3d():
    """3日收益率"""
    return "Ref($close, -3) / $close - 1"

@register_factor("price", "ret_5d")
def ret_5d():
    """5日收益率"""
    return "Ref($close, -5) / $close - 1"

@register_factor("price", "ret_7d")
def ret_7d():
    """7日收益率"""
    return "Ref($close, -7) / $close - 1"

@register_factor("price", "ret_10d")
def ret_10d():
    """10日收益率"""
    return "Ref($close, -10) / $close - 1"

@register_factor("price", "ret_15d")
def ret_15d():
    """15日收益率"""
    return "Ref($close, -15) / $close - 1"

@register_factor("price", "ret_20d")
def ret_20d():
    """20日收益率"""
    return "Ref($close, -20) / $close - 1"

@register_factor("price", "ret_30d")
def ret_30d():
    """30日收益率"""
    return "Ref($close, -30) / $close - 1"

@register_factor("price", "ret_60d")
def ret_60d():
    """60日收益率"""
    return "Ref($close, -60) / $close - 1"

@register_factor("price", "ret_90d")
def ret_90d():
    """90日收益率"""
    return "Ref($close, -90) / $close - 1"

@register_factor("price", "ret_120d")
def ret_120d():
    """120日收益率"""
    return "Ref($close, -120) / $close - 1"

@register_factor("price", "ret_180d")
def ret_180d():
    """180日收益率"""
    return "Ref($close, -180) / $close - 1"

@register_factor("price", "ret_240d")
def ret_240d():
    """240日收益率"""
    return "Ref($close, -240) / $close - 1"

@register_factor("price", "amp_3d")
def amp_3d():
    """3日振幅"""
    return "(Max($high, 3) - Min($low, 3)) / Ref($close, -3)"

@register_factor("price", "amp_5d")
def amp_5d():
    """5日振幅: (Max($high,5) - Min($low,5)) / Ref($close,-5)"""
    return "(Max($high, 5) - Min($low, 5)) / Ref($close, -5)"

@register_factor("price", "amp_7d")
def amp_7d():
    """7日振幅"""
    return "(Max($high, 7) - Min($low, 7)) / Ref($close, -7)"

@register_factor("price", "amp_10d")
def amp_10d():
    """10日振幅"""
    return "(Max($high, 10) - Min($low, 10)) / Ref($close, -10)"

@register_factor("price", "amp_20d")
def amp_20d():
    """20日振幅"""
    return "(Max($high, 20) - Min($low, 20)) / Ref($close, -20)"

@register_factor("price", "amp_60d")
def amp_60d():
    """60日振幅"""
    return "(Max($high, 60) - Min($low, 60)) / Ref($close, -60)"

@register_factor("price", "amp_90d")
def amp_90d():
    """90日振幅"""
    return "(Max($high, 90) - Min($low, 90)) / Ref($close, -90)"

@register_factor("price", "high_low_spread_5d")
def high_low_spread_5d():
    """5日高低价差比: MaxHigh/MinLow - 1"""
    return "Max($high, 5) / Min($low, 5) - 1"

@register_factor("price", "high_low_spread_10d")
def high_low_spread_10d():
    """10日高低价差比"""
    return "Max($high, 10) / Min($low, 10) - 1"

@register_factor("price", "high_low_spread_20d")
def high_low_spread_20d():
    """20日高低价差比"""
    return "Max($high, 20) / Min($low, 20) - 1"

@register_factor("price", "overnight_ret")
def overnight_ret():
    """隔夜收益: open / 昨日close - 1"""
    return "$open / Ref($close, -1) - 1"

@register_factor("price", "intraday_ret")
def intraday_ret():
    """日内收益: close / open - 1"""
    return "$close / $open - 1"


# ═══════════════════════════════════════════
# VOLUME — 成交量价因子
# ═══════════════════════════════════════════

@register_factor("volume", "vol_change_3d")
def vol_change_3d():
    """3日量比: volume / 3日前volume"""
    return "$volume / Ref($volume, -3)"

@register_factor("volume", "vol_change_5d")
def vol_change_5d():
    """5日量比"""
    return "$volume / Ref($volume, -5)"

@register_factor("volume", "vol_change_10d")
def vol_change_10d():
    """10日量比"""
    return "$volume / Ref($volume, -10)"

@register_factor("volume", "vol_change_20d")
def vol_change_20d():
    """20日量比"""
    return "$volume / Ref($volume, -20)"

@register_factor("volume", "amount_change_3d")
def amount_change_3d():
    """3日额比: amount / 3日前amount"""
    return "$amount / Ref($amount, -3)"

@register_factor("volume", "amount_change_5d")
def amount_change_5d():
    """5日额比"""
    return "$amount / Ref($amount, -5)"

@register_factor("volume", "amount_change_10d")
def amount_change_10d():
    """10日额比"""
    return "$amount / Ref($amount, -10)"

@register_factor("volume", "amount_change_20d")
def amount_change_20d():
    """20日额比"""
    return "$amount / Ref($amount, -20)"

@register_factor("volume", "vol_mean_5d")
def vol_mean_5d():
    """5日均量 / 20日均量"""
    return "Mean($volume, 5) / Mean($volume, 20)"

@register_factor("volume", "vol_mean_10d")
def vol_mean_10d():
    """10日均量 / 60日均量"""
    return "Mean($volume, 10) / Mean($volume, 60)"

@register_factor("volume", "vol_mean_20d")
def vol_mean_20d():
    """20日均量 / 60日均量"""
    return "Mean($volume, 20) / Mean($volume, 60)"

@register_factor("volume", "vol_mean_60d")
def vol_mean_60d():
    """60日均量 / 120日均量"""
    return "Mean($volume, 60) / Mean($volume, 120)"

@register_factor("volume", "vol_std_20d")
def vol_std_20d():
    """20日量波动"""
    return "Std($volume, 20) / Mean($volume, 20)"

@register_factor("volume", "vol_max_20d")
def vol_max_20d():
    """成交量距20日最大: vol / Max(vol,20)"""
    return "$volume / Max($volume, 20)"

@register_factor("volume", "amount_mean_5d")
def amount_mean_5d():
    """5日均额 / 20日均额"""
    return "Mean($amount, 5) / Mean($amount, 20)"

@register_factor("volume", "amount_mean_10d")
def amount_mean_10d():
    """10日均额 / 20日均额"""
    return "Mean($amount, 10) / Mean($amount, 20)"

@register_factor("volume", "amount_mean_20d")
def amount_mean_20d():
    """20日均额 / 60日均额"""
    return "Mean($amount, 20) / Mean($amount, 60)"


# ═══════════════════════════════════════════
# ROLLING — 滚动统计
# ═══════════════════════════════════════════

@register_factor("rolling", "close_mean_3d")
def close_mean_3d():
    """3日均线偏离: Mean($close,3) / $close - 1"""
    return "Mean($close, 3) / $close - 1"

@register_factor("rolling", "close_mean_5d")
def close_mean_5d():
    """5日均线偏离: Mean($close,5) / $close - 1"""
    return "Mean($close, 5) / $close - 1"

@register_factor("rolling", "close_mean_7d")
def close_mean_7d():
    """7日均线偏离"""
    return "Mean($close, 7) / $close - 1"

@register_factor("rolling", "close_mean_10d")
def close_mean_10d():
    """10日均线偏离"""
    return "Mean($close, 10) / $close - 1"

@register_factor("rolling", "close_mean_20d")
def close_mean_20d():
    """20日均线偏离"""
    return "Mean($close, 20) / $close - 1"

@register_factor("rolling", "close_mean_30d")
def close_mean_30d():
    """30日均线偏离"""
    return "Mean($close, 30) / $close - 1"

@register_factor("rolling", "close_mean_60d")
def close_mean_60d():
    """60日均线偏离"""
    return "Mean($close, 60) / $close - 1"

@register_factor("rolling", "close_mean_90d")
def close_mean_90d():
    """90日均线偏离"""
    return "Mean($close, 90) / $close - 1"

@register_factor("rolling", "close_mean_120d")
def close_mean_120d():
    """120日均线偏离"""
    return "Mean($close, 120) / $close - 1"

@register_factor("rolling", "close_std_5d")
def close_std_5d():
    """5日波动率"""
    return "Std($close, 5) / Mean($close, 5)"

@register_factor("rolling", "close_std_10d")
def close_std_10d():
    """10日波动率"""
    return "Std($close, 10) / Mean($close, 10)"

@register_factor("rolling", "close_std_20d")
def close_std_20d():
    """20日波动率"""
    return "Std($close, 20) / Mean($close, 20)"

@register_factor("rolling", "close_std_30d")
def close_std_30d():
    """30日波动率"""
    return "Std($close, 30) / Mean($close, 30)"

@register_factor("rolling", "close_std_60d")
def close_std_60d():
    """60日波动率"""
    return "Std($close, 60) / Mean($close, 60)"

@register_factor("rolling", "close_std_90d")
def close_std_90d():
    """90日波动率"""
    return "Std($close, 90) / Mean($close, 90)"

@register_factor("rolling", "close_std_120d")
def close_std_120d():
    """120日波动率"""
    return "Std($close, 120) / Mean($close, 120)"

@register_factor("rolling", "close_max_5d")
def close_max_5d():
    """距5日高点: $close / Max($close, 5)"""
    return "$close / Max($close, 5)"

@register_factor("rolling", "close_max_10d")
def close_max_10d():
    """距10日高点"""
    return "$close / Max($close, 10)"

@register_factor("rolling", "close_max_20d")
def close_max_20d():
    """距20日高点: $close / Max($close, 20)"""
    return "$close / Max($close, 20)"

@register_factor("rolling", "close_max_60d")
def close_max_60d():
    """距60日高点"""
    return "$close / Max($close, 60)"

@register_factor("rolling", "close_min_5d")
def close_min_5d():
    """距5日低点: $close / Min($close, 5)"""
    return "$close / Min($close, 5)"

@register_factor("rolling", "close_min_10d")
def close_min_10d():
    """距10日低点"""
    return "$close / Min($close, 10)"

@register_factor("rolling", "close_min_20d")
def close_min_20d():
    """距20日低点: $close / Min($close, 20)"""
    return "$close / Min($close, 20)"

@register_factor("rolling", "close_min_60d")
def close_min_60d():
    """距60日低点"""
    return "$close / Min($close, 60)"

@register_factor("rolling", "close_skew_20d")
def close_skew_20d():
    """20日收盘价偏度"""
    return "Skew($close, 20)"

@register_factor("rolling", "close_kurt_20d")
def close_kurt_20d():
    """20日收盘价峰度"""
    return "Kurt($close, 20)"

@register_factor("rolling", "vol_std_5d")
def vol_std_5d():
    """5日成交量波动率"""
    return "Std($volume, 5) / Mean($volume, 5)"

@register_factor("rolling", "vol_std_10d")
def vol_std_10d():
    """10日成交量波动率"""
    return "Std($volume, 10) / Mean($volume, 10)"

@register_factor("rolling", "vol_skew_20d")
def vol_skew_20d():
    """20日成交量偏度"""
    return "Skew($volume, 20)"

@register_factor("rolling", "high_mean_5d")
def high_mean_5d():
    """5日均高价 / close"""
    return "Mean($high, 5) / $close"

@register_factor("rolling", "high_mean_10d")
def high_mean_10d():
    """10日均高价 / close"""
    return "Mean($high, 10) / $close"

@register_factor("rolling", "low_mean_5d")
def low_mean_5d():
    """5日均低价 / close"""
    return "Mean($low, 5) / $close"

@register_factor("rolling", "low_mean_10d")
def low_mean_10d():
    """10日均低价 / close"""
    return "Mean($low, 10) / $close"


# ═══════════════════════════════════════════
# TECH — 技术指标
# ═══════════════════════════════════════════

@register_factor("tech", "rsi_6")
def rsi_6():
    """6日RSI"""
    return "RSI($close, 6)"

@register_factor("tech", "rsi_9")
def rsi_9():
    """9日RSI"""
    return "RSI($close, 9)"

@register_factor("tech", "rsi_14")
def rsi_14():
    """14日RSI"""
    return "RSI($close, 14)"

@register_factor("tech", "rsi_24")
def rsi_24():
    """24日RSI"""
    return "RSI($close, 24)"

@register_factor("tech", "rsi_48")
def rsi_48():
    """48日RSI"""
    return "RSI($close, 48)"

@register_factor("tech", "ema_12")
def ema_12():
    """12日EMA / close"""
    return "EMA($close, 12) / $close"

@register_factor("tech", "ema_26")
def ema_26():
    """26日EMA / close"""
    return "EMA($close, 26) / $close"

@register_factor("tech", "ema_12_26")
def ema_12_26():
    """MACD线: EMA12 / EMA26"""
    return "EMA($close, 12) / EMA($close, 26)"


# ═══════════════════════════════════════════
# MOMENTUM — 动量/反转
# ═══════════════════════════════════════════

@register_factor("momentum", "mom_1d")
def mom_1d():
    """1日动量: close - Ref(close, -1)"""
    return "$close - Ref($close, -1)"

@register_factor("momentum", "mom_3d")
def mom_3d():
    """3日动量"""
    return "$close - Ref($close, -3)"

@register_factor("momentum", "mom_5d")
def mom_5d():
    """5日动量: close - Ref(close, -5)"""
    return "$close - Ref($close, -5)"

@register_factor("momentum", "mom_7d")
def mom_7d():
    """7日动量"""
    return "$close - Ref($close, -7)"

@register_factor("momentum", "mom_10d")
def mom_10d():
    """10日动量"""
    return "$close - Ref($close, -10)"

@register_factor("momentum", "mom_15d")
def mom_15d():
    """15日动量"""
    return "$close - Ref($close, -15)"

@register_factor("momentum", "mom_20d")
def mom_20d():
    """20日动量"""
    return "$close - Ref($close, -20)"

@register_factor("momentum", "mom_60d")
def mom_60d():
    """60日动量"""
    return "$close - Ref($close, -60)"

@register_factor("momentum", "mom_90d")
def mom_90d():
    """90日动量"""
    return "$close - Ref($close, -90)"

@register_factor("momentum", "mom_120d")
def mom_120d():
    """120日动量"""
    return "$close - Ref($close, -120)"

@register_factor("momentum", "ma_dev_5d")
def ma_dev_5d():
    """5日均线偏离: (close - MA5) / MA5"""
    return "($close - Mean($close, 5)) / Mean($close, 5)"

@register_factor("momentum", "ma_dev_10d")
def ma_dev_10d():
    """10日均线偏离"""
    return "($close - Mean($close, 10)) / Mean($close, 10)"

@register_factor("momentum", "ma_dev_20d")
def ma_dev_20d():
    """20日均线偏离: (close - MA20) / MA20"""
    return "($close - Mean($close, 20)) / Mean($close, 20)"

@register_factor("momentum", "ma_dev_60d")
def ma_dev_60d():
    """60日均线偏离"""
    return "($close - Mean($close, 60)) / Mean($close, 60)"

@register_factor("momentum", "ma_dev_5_20")
def ma_dev_5_20():
    """MA5-MA20 交叉: MA5/MA20 - 1"""
    return "Mean($close, 5) / Mean($close, 20) - 1"

@register_factor("momentum", "ma_dev_10_60")
def ma_dev_10_60():
    """MA10-MA60 交叉: MA10/MA60 - 1"""
    return "Mean($close, 10) / Mean($close, 60) - 1"

@register_factor("momentum", "chg_5d")
def chg_5d():
    """5日涨跌幅: PctChg($close,5)"""
    return "PctChg($close, 5)"

@register_factor("momentum", "chg_10d")
def chg_10d():
    """10日涨跌幅"""
    return "PctChg($close, 10)"

@register_factor("momentum", "chg_20d")
def chg_20d():
    """20日涨跌幅"""
    return "PctChg($close, 20)"

@register_factor("momentum", "chg_30d")
def chg_30d():
    """30日涨跌幅"""
    return "PctChg($close, 30)"

@register_factor("momentum", "chg_60d")
def chg_60d():
    """60日涨跌幅"""
    return "PctChg($close, 60)"

@register_factor("momentum", "chg_90d")
def chg_90d():
    """90日涨跌幅"""
    return "PctChg($close, 90)"


# ═══════════════════════════════════════════
# LEVERAGE — 回撤/波动风险
# ═══════════════════════════════════════════

@register_factor("leverage", "dd_5d")
def dd_5d():
    """5日回撤: close / Max(close,5) - 1"""
    return "$close / Max($close, 5) - 1"

@register_factor("leverage", "dd_10d")
def dd_10d():
    """10日回撤: close / Max(close,10) - 1"""
    return "$close / Max($close, 10) - 1"

@register_factor("leverage", "dd_20d")
def dd_20d():
    """20日回撤: close / Max(close,20) - 1"""
    return "$close / Max($close, 20) - 1"

@register_factor("leverage", "dd_60d")
def dd_60d():
    """60日回撤: close / Max(close,60) - 1"""
    return "$close / Max($close, 60) - 1"

@register_factor("leverage", "dd_120d")
def dd_120d():
    """120日回撤: close / Max(close,120) - 1"""
    return "$close / Max($close, 120) - 1"

@register_factor("leverage", "atr_5")
def atr_5():
    """5日ATR近似: Mean(high-low,5) / close"""
    return "Mean($high - $low, 5) / $close"

@register_factor("leverage", "atr_7")
def atr_7():
    """7日ATR近似: Mean(high-low,7) / close"""
    return "Mean($high - $low, 7) / $close"

@register_factor("leverage", "atr_14")
def atr_14():
    """14日ATR近似: Mean(high-low,14) / close"""
    return "Mean($high - $low, 14) / $close"


# ═══════════════════════════════════════════
# CORRELATION — 相关性因子
# ═══════════════════════════════════════════

@register_factor("correlation", "corr_close_vol_20")
def corr_close_vol_20():
    """20日收盘价-成交量相关性"""
    return "Corr($close, $volume, 20)"

@register_factor("correlation", "corr_close_amount_20")
def corr_close_amount_20():
    """20日收盘价-成交额相关性"""
    return "Corr($close, $amount, 20)"

@register_factor("correlation", "corr_high_low_20")
def corr_high_low_20():
    """20日最高价-最低价相关性"""
    return "Corr($high, $low, 20)"


# 注: KDJ, MACD, OBV 等复杂技术指标需要用 impl="code" 实现
# 放在 custom.py 中注册
