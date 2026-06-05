"""WorldQuant 101 Alpha 因子库 (wide-DataFrame 适配).

原始: yli188/WorldQuant_alpha101_code (736★)
适配: 所有算子改为 date×stock 宽表批量计算.

共 101 个 alpha, 其中 ~80 个可直接用 OHLCV 实现,
~20 个 (48,56,58,59,63,67,69,70,76,79,80,82,87,89,90,91,93,97,100)
需要行业/市值数据, 暂标记为 SKIP.

使用:
    from src.factors.wq101 import compute_all_wq101
    results = compute_all_wq101()  # {alpha001-101: DataFrame}
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from functools import lru_cache
from scipy.stats import rankdata

from src.factors.data import read_ohlcv
from src.factors.utils import process_factor

# ═══════════════════════════════════════════════════════
# Wide-DF helper operators (全部支持 date×stock DataFrame)
# ═══════════════════════════════════════════════════════

def ts_sum(df, w=10):
    return df.rolling(w, min_periods=1).sum()

def sma(df, w=10):
    return df.rolling(w, min_periods=1).mean()

def stddev(df, w=10):
    return df.rolling(w, min_periods=2).std()

def correlation(x, y, w=10):
    result = x.rolling(w, min_periods=3).corr(y)
    return result.replace([np.inf, -np.inf], 0).fillna(0)

def covariance(x, y, w=10):
    result = x.rolling(w, min_periods=3).cov(y)
    return result.replace([np.inf, -np.inf], 0).fillna(0)

def delta(df, period=1):
    return df.diff(period)

def delay(df, period=1):
    return df.shift(period)

def rank(df):
    """时间序列 rank (每列独立)."""
    return df.rank(axis=0, pct=True)

def ts_rank(df, w=10):
    """滚动窗口内最后一值的 rank."""
    def _rolling_rank(na):
        return rankdata(na)[-1]
    return df.rolling(w, min_periods=1).apply(_rolling_rank, raw=True)

def ts_min(df, w=10):
    return df.rolling(w, min_periods=1).min()

def ts_max(df, w=10):
    return df.rolling(w, min_periods=1).max()

def ts_argmax(df, w=10):
    return df.rolling(w, min_periods=1).apply(np.argmax, raw=True) + 1

def ts_argmin(df, w=10):
    return df.rolling(w, min_periods=1).apply(np.argmin, raw=True) + 1

def product(df, w=10):
    return df.rolling(w, min_periods=1).apply(np.prod, raw=True)

def scale(df, k=1):
    s = np.abs(df).sum(axis=0)
    s = s.replace(0, 1)
    return df.mul(k).div(s)

def decay_linear(df, period=10):
    """线性衰减加权平均 (LWMA)."""
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
    result = pd.DataFrame(np.nan, index=df.index, columns=df.columns)
    w = np.arange(1, period + 1, dtype=float) / (period * (period + 1) / 2)
    arr = df.values
    for i in range(period - 1, arr.shape[0]):
        result.iloc[i] = arr[i - period + 1:i + 1].T @ w
    return result.fillna(df)


# ═══════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _prepare_data(start_date=None, end_date=None):
    """加载并预处理 OHLCV 数据 (带缓存)."""
    raw = read_ohlcv(start_date, end_date)
    close = raw['close'].astype(float)
    volume = raw['volume'].astype(float) * 100  # 手 → 股
    vwap = raw['vwap'].astype(float)
    
    # returns = pct_change
    returns = close.pct_change().fillna(0)
    
    data = {
        'open': raw['open'].astype(float),
        'high': raw['high'].astype(float),
        'low': raw['low'].astype(float),
        'close': close,
        'volume': volume,
        'vwap': vwap,
        'returns': returns,
    }
    return data


# ═══════════════════════════════════════════════════════
# Alpha 计算 (适配 wide DataFrame)
# ═══════════════════════════════════════════════════════

# Each function: takes data dict, returns wide DataFrame (dates × stocks)
# Returns None for skipped alphas

def _inf_fill(df):
    return df.replace([np.inf, -np.inf], np.nan).fillna(0)


def alpha001(d):
    """rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2),5)) - 0.5"""
    inner = d['close'].where(d['returns'] >= 0, stddev(d['returns'], 20))
    return rank(ts_argmax(inner ** 2, 5)) - 0.5


def alpha002(d):
    """-1 * correlation(rank(delta(log(volume),2)), rank(((close-open)/open)), 6)"""
    return -1 * correlation(rank(delta(np.log(d['volume'].replace(0, np.nan)), 2)),
                            rank((d['close'] - d['open']) / d['open'].replace(0, np.nan)), 6)


def alpha003(d):
    """-1 * correlation(rank(open), rank(volume), 10)"""
    return -1 * correlation(rank(d['open']), rank(d['volume']), 10)


def alpha004(d):
    """-1 * Ts_Rank(rank(low), 9)"""
    return -1 * ts_rank(rank(d['low']), 9)


def alpha005(d):
    """rank((open - (sum(vwap,10)/10))) * (-1 * abs(rank((close - vwap))))"""
    return rank(d['open'] - ts_sum(d['vwap'], 10) / 10) * (-1 * np.abs(rank(d['close'] - d['vwap'])))


def alpha006(d):
    """-1 * correlation(open, volume, 10)"""
    return -1 * correlation(d['open'], d['volume'], 10)


def alpha007(d):
    """((adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1))"""
    adv20 = sma(d['volume'], 20)
    alpha = -1 * ts_rank(np.abs(delta(d['close'], 7)), 60) * np.sign(delta(d['close'], 7))
    return alpha.where(adv20 < d['volume'], -1)


def alpha008(d):
    """-1 * rank(((sum(open,5)*sum(returns,5)) - delay((sum(open,5)*sum(returns,5)),10)))"""
    inner = ts_sum(d['open'], 5) * ts_sum(d['returns'], 5)
    return -1 * rank(inner - delay(inner, 10))


def alpha009(d):
    """(0<ts_min(delta(close,1),5))?delta(close,1):((ts_max(delta(close,1),5)<0)?delta(close,1):(-1*delta(close,1)))"""
    dc = delta(d['close'], 1)
    cond = (ts_min(dc, 5) > 0) | (ts_max(dc, 5) < 0)
    return (-1 * dc).where(~cond, dc)


def alpha010(d):
    """rank(alpha009 but window 4)"""
    dc = delta(d['close'], 1)
    cond = (ts_min(dc, 4) > 0) | (ts_max(dc, 4) < 0)
    return rank((-1 * dc).where(~cond, dc))


def alpha011(d):
    """(rank(ts_max((vwap-close),3)) + rank(ts_min((vwap-close),3))) * rank(delta(volume,3))"""
    return (rank(ts_max(d['vwap'] - d['close'], 3)) + rank(ts_min(d['vwap'] - d['close'], 3))) * rank(delta(d['volume'], 3))


def alpha012(d):
    """sign(delta(volume,1)) * (-1 * delta(close,1))"""
    return np.sign(delta(d['volume'], 1)) * (-1 * delta(d['close'], 1))


def alpha013(d):
    """-1 * rank(covariance(rank(close), rank(volume), 5))"""
    return -1 * rank(covariance(rank(d['close']), rank(d['volume']), 5))


def alpha014(d):
    """(-1 * rank(delta(returns,3))) * correlation(open, volume, 10)"""
    return -1 * rank(delta(d['returns'], 3)) * _inf_fill(correlation(d['open'], d['volume'], 10))


def alpha015(d):
    """-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)"""
    return -1 * ts_sum(rank(_inf_fill(correlation(rank(d['high']), rank(d['volume']), 3))), 3)


def alpha016(d):
    """-1 * rank(covariance(rank(high), rank(volume), 5))"""
    return -1 * rank(covariance(rank(d['high']), rank(d['volume']), 5))


def alpha017(d):
    """((-1*rank(ts_rank(close,10)))*rank(delta(delta(close,1),1)))*rank(ts_rank((volume/adv20),5))"""
    adv20 = sma(d['volume'], 20)
    return -1 * rank(ts_rank(d['close'], 10)) * rank(delta(delta(d['close'], 1), 1)) * rank(ts_rank(d['volume'] / adv20.replace(0, np.nan), 5))


def alpha018(d):
    """-1*rank(((stddev(abs((close-open)),5)+(close-open))+correlation(close,open,10)))"""
    return -1 * rank(stddev(np.abs(d['close'] - d['open']), 5) + (d['close'] - d['open']) + _inf_fill(correlation(d['close'], d['open'], 10)))


def alpha019(d):
    """(-1*sign(((close-delay(close,7))+delta(close,7))))*(1+rank(1+sum(returns,250)))"""
    return -1 * np.sign((d['close'] - delay(d['close'], 7)) + delta(d['close'], 7)) * (1 + rank(1 + ts_sum(d['returns'], 250)))


def alpha020(d):
    """(-1*rank((open-delay(high,1))))*rank((open-delay(close,1)))*rank((open-delay(low,1)))"""
    return -1 * rank(d['open'] - delay(d['high'], 1)) * rank(d['open'] - delay(d['close'], 1)) * rank(d['open'] - delay(d['low'], 1))


def alpha021(d):
    """((sum(close,8)/8+stddev(close,8))<(sum(close,2)/2))?(-1):(((sum(close,2)/2)<((sum(close,8)/8)-stddev(close,8)))?1:(((1<(volume/adv20))||((volume/adv20)==1))?1:(-1)))"""
    cond1 = sma(d['close'], 8) + stddev(d['close'], 8) < sma(d['close'], 2)
    cond2 = sma(d['volume'], 20) / d['volume'].replace(0, np.nan) < 1
    return pd.DataFrame(-1, index=d['close'].index, columns=d['close'].columns).where(~(cond1 | cond2), 1)


def alpha022(d):
    """-1*(delta(correlation(high,volume,5),5)*rank(stddev(close,20)))"""
    return -1 * delta(_inf_fill(correlation(d['high'], d['volume'], 5)), 5) * rank(stddev(d['close'], 20))


def alpha023(d):
    """((sum(high,20)/20)<high)?(-1*delta(high,2)):0"""
    cond = sma(d['high'], 20) < d['high']
    return (-1 * delta(d['high'], 2).fillna(0)).where(cond, 0)


def alpha024(d):
    """((delta((sum(close,100)/100),100)/delay(close,100))<=0.05)?(-1*(close-ts_min(close,100))):(-1*delta(close,3))"""
    cond = delta(sma(d['close'], 100), 100) / delay(d['close'], 100).replace(0, np.nan) <= 0.05
    return (-1 * (d['close'] - ts_min(d['close'], 100))).where(cond, -1 * delta(d['close'], 3))


def alpha025(d):
    """rank((((-1*returns)*adv20)*vwap)*(high-close))"""
    adv20 = sma(d['volume'], 20)
    return rank((-1 * d['returns'] * adv20 * d['vwap']) * (d['high'] - d['close']))


def alpha026(d):
    """-1*ts_max(correlation(ts_rank(volume,5),ts_rank(high,5),5),3)"""
    return -1 * ts_max(_inf_fill(correlation(ts_rank(d['volume'], 5), ts_rank(d['high'], 5), 5)), 3)


def alpha027(d):
    """(0.5<rank((sum(correlation(rank(volume),rank(vwap),6),2)/2.0)))?(-1):1"""
    a = rank(sma(_inf_fill(correlation(rank(d['volume']), rank(d['vwap']), 6)), 2) / 2.0)
    return a.where(a <= 0.5, -1).where(a > 0.5, 1)


def alpha028(d):
    """scale(((correlation(adv20,low,5)+((high+low)/2))-close))"""
    adv20 = sma(d['volume'], 20)
    return scale(_inf_fill(correlation(adv20, d['low'], 5)) + (d['high'] + d['low']) / 2 - d['close'])


def alpha029(d):
    """min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1*rank(delta((close-1),5))))),2),1))))),1),5)+ts_rank(delay((-1*returns),6),5)"""
    inner = rank(rank(-1 * rank(delta(d['close'] - 1, 5))))
    inner = ts_min(inner, 2)
    inner = rank(rank(scale(np.log(ts_sum(inner, 1).replace(0, np.nan)))))
    return ts_min(product(inner, 1), 5) + ts_rank(delay(-1 * d['returns'], 6), 5)


def alpha030(d):
    """((1.0-rank(sign(delta(close,1))+sign(delay(delta(close,1),1))+sign(delay(delta(close,1),2))))*sum(volume,5))/sum(volume,20)"""
    dc = delta(d['close'], 1)
    inner = np.sign(dc) + np.sign(delay(dc, 1)) + np.sign(delay(dc, 2))
    return (1.0 - rank(inner)) * ts_sum(d['volume'], 5) / ts_sum(d['volume'], 20).replace(0, np.nan)


def alpha031(d):
    """(rank(rank(rank(decay_linear((-1*rank(rank(delta(close,10)))),10))))+rank((-1*delta(close,3))))+sign(scale(correlation(adv20,low,12)))"""
    adv20 = sma(d['volume'], 20)
    p1 = rank(rank(rank(decay_linear(rank(rank(delta(d['close'], 10))) * -1, 10))))
    p2 = rank(-1 * delta(d['close'], 3))
    p3 = np.sign(scale(_inf_fill(correlation(adv20, d['low'], 12))))
    return p1 + p2 + p3


def alpha032(d):
    """scale(((sum(close,7)/7)-close))+(20*scale(correlation(vwap,delay(close,5),230)))"""
    return scale(sma(d['close'], 7) - d['close']) + 20 * scale(correlation(d['vwap'], delay(d['close'], 5), 230))


def alpha033(d):
    """rank(-1+((1-(open/close))))"""
    return rank(-1 + (d['open'] / d['close'].replace(0, np.nan)))


def alpha034(d):
    """rank(((1-rank((stddev(returns,2)/stddev(returns,5))))+(1-rank(delta(close,1)))))"""
    inner = (stddev(d['returns'], 2) / stddev(d['returns'], 5).replace(0, np.nan)).fillna(1)
    return rank(2 - rank(inner) - rank(delta(d['close'], 1)))


def alpha035(d):
    """((Ts_Rank(volume,32)*(1-Ts_Rank(((close+high)-low),16)))*(1-Ts_Rank(returns,32)))"""
    return ts_rank(d['volume'], 32) * (1 - ts_rank(d['close'] + d['high'] - d['low'], 16)) * (1 - ts_rank(d['returns'], 32))


def alpha036(d):
    """(2.21*rank(corr(close-open,delay(vol,1),15))+0.7*rank(open-close)+0.73*rank(Ts_Rank(delay(-1*ret,6),5))+rank(abs(corr(vwap,adv20,6)))+0.6*rank(((sum(close,200)/200-open)*(close-open))))"""
    adv20 = sma(d['volume'], 20)
    return (2.21 * rank(correlation(d['close'] - d['open'], delay(d['volume'], 1), 15)) +
            0.7 * rank(d['open'] - d['close']) +
            0.73 * rank(ts_rank(delay(-1 * d['returns'], 6), 5)) +
            rank(np.abs(correlation(d['vwap'], adv20, 6))) +
            0.6 * rank((sma(d['close'], 200) - d['open']) * (d['close'] - d['open'])))


def alpha037(d):
    """rank(correlation(delay((open-close),1),close,200))+rank((open-close))"""
    return rank(correlation(delay(d['open'] - d['close'], 1), d['close'], 200)) + rank(d['open'] - d['close'])


def alpha038(d):
    """(-1*rank(Ts_Rank(close,10)))*rank((close/open))"""
    inner = (d['close'] / d['open'].replace(0, np.nan)).fillna(1)
    return -1 * rank(ts_rank(d['open'], 10)) * rank(inner)


def alpha039(d):
    """(-1*rank(delta(close,7)*(1-rank(decay_linear((volume/adv20),9)))))*(1+rank(sum(returns,250)))"""
    adv20 = sma(d['volume'], 20)
    return -1 * rank(delta(d['close'], 7) * (1 - rank(decay_linear(d['volume'] / adv20.replace(0, np.nan), 9)))) * (1 + rank(sma(d['returns'], 250)))


def alpha040(d):
    """(-1*rank(stddev(high,10)))*correlation(high,volume,10)"""
    return -1 * rank(stddev(d['high'], 10)) * correlation(d['high'], d['volume'], 10)


def alpha041(d):
    """(((high*low)^0.5)-vwap)"""
    return np.sqrt(d['high'] * d['low']) - d['vwap']


def alpha042(d):
    """rank((vwap-close))/rank((vwap+close))"""
    return rank(d['vwap'] - d['close']) / rank(d['vwap'] + d['close']).replace(0, np.nan)


def alpha043(d):
    """ts_rank((volume/adv20),20)*ts_rank((-1*delta(close,7)),8)"""
    adv20 = sma(d['volume'], 20)
    return ts_rank(d['volume'] / adv20.replace(0, np.nan), 20) * ts_rank(-1 * delta(d['close'], 7), 8)


def alpha044(d):
    """-1*correlation(high,rank(volume),5)"""
    return -1 * _inf_fill(correlation(d['high'], rank(d['volume']), 5))


def alpha045(d):
    """-1*((rank(sum(delay(close,5),20)/20))*correlation(close,volume,2)*rank(correlation(sum(close,5),sum(close,20),2)))"""
    inner = _inf_fill(correlation(d['close'], d['volume'], 2))
    return -1 * rank(sma(delay(d['close'], 5), 20)) * inner * rank(correlation(ts_sum(d['close'], 5), ts_sum(d['close'], 20), 2))


def alpha046(d):
    """Conditional: (inner>0.25)?-1:(inner<0)?1:(-1*delta(close))"""
    inner = (delay(d['close'], 20) - delay(d['close'], 10)) / 10 - (delay(d['close'], 10) - d['close']) / 10
    alpha = -1 * delta(d['close'], 1)
    alpha[inner < 0] = 1
    alpha[inner > 0.25] = -1
    return alpha


def alpha047(d):
    """(((rank(1/close)*volume)/adv20)*((high*rank(high-close))/(sum(high,5)/5)))-rank(vwap-delay(vwap,5))"""
    adv20 = sma(d['volume'], 20)
    return (rank(1 / d['close'].replace(0, np.nan)) * d['volume'] / adv20.replace(0, np.nan)) * (d['high'] * rank(d['high'] - d['close']) / (sma(d['high'], 5))).replace(0, np.nan) - rank(d['vwap'] - delay(d['vwap'], 5))


def alpha048(d):
    """SKIP: 需要 industry neutralization + subindustry 分类"""
    return None


def alpha049(d):
    """(inner<-0.1)?1:(-1*delta(close))"""
    inner = (delay(d['close'], 20) - delay(d['close'], 10)) / 10 - (delay(d['close'], 10) - d['close']) / 10
    alpha = -1 * delta(d['close'], 1)
    alpha[inner < -0.1] = 1
    return alpha


def alpha050(d):
    """-1*ts_max(rank(correlation(rank(volume),rank(vwap),5)),5)"""
    return -1 * ts_max(rank(correlation(rank(d['volume']), rank(d['vwap']), 5)), 5)


def alpha051(d):
    """(inner<-0.05)?1:(-1*delta(close))"""
    inner = (delay(d['close'], 20) - delay(d['close'], 10)) / 10 - (delay(d['close'], 10) - d['close']) / 10
    alpha = -1 * delta(d['close'], 1)
    alpha[inner < -0.05] = 1
    return alpha


def alpha052(d):
    """((-1*ts_min(low,5)+delay(ts_min(low,5),5))*rank(((sum(returns,240)-sum(returns,20))/220)))*ts_rank(volume,5)"""
    return (-1 * delta(ts_min(d['low'], 5), 5)) * rank((ts_sum(d['returns'], 240) - ts_sum(d['returns'], 20)) / 220) * ts_rank(d['volume'], 5)


def alpha053(d):
    """-1*delta((((close-low)-(high-close))/(close-low)),9)"""
    denom = (d['close'] - d['low']).replace(0, 0.0001)
    return -1 * delta((d['close'] - d['low'] - (d['high'] - d['close'])) / denom, 9)


def alpha054(d):
    """-1*((low-close)*(open^5))/((low-high)*(close^5))"""
    denom = (d['low'] - d['high']).replace(0, -0.0001)
    return -1 * (d['low'] - d['close']) * (d['open'] ** 5) / (denom * (d['close'] ** 5))


def alpha055(d):
    """-1*correlation(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))),rank(volume),6)"""
    denom = (ts_max(d['high'], 12) - ts_min(d['low'], 12)).replace(0, 0.0001)
    inner = (d['close'] - ts_min(d['low'], 12)) / denom
    return -1 * _inf_fill(correlation(rank(inner), rank(d['volume']), 6))


def alpha056(d):
    """SKIP: 需要市值(cap)数据"""
    return None


def alpha057(d):
    """-1*((close-vwap)/decay_linear(rank(ts_argmax(close,30)),2))"""
    denom = decay_linear(rank(ts_argmax(d['close'], 30)), 2).replace(0, np.nan)
    return -1 * (d['close'] - d['vwap']) / denom


def alpha058(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha059(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha060(d):
    """-((2*scale(rank((((close-low)-(high-close))/(high-low)*volume))))-scale(rank(ts_argmax(close,10))))"""
    denom = (d['high'] - d['low']).replace(0, 0.0001)
    inner = (d['close'] - d['low'] - (d['high'] - d['close'])) * d['volume'] / denom
    return -(2 * scale(rank(inner)) - scale(rank(ts_argmax(d['close'], 10))))


def alpha061(d):
    """rank((vwap-ts_min(vwap,16)))<rank(correlation(vwap,adv180,18))"""
    adv180 = sma(d['volume'], 180)
    return rank(d['vwap'] - ts_min(d['vwap'], 16)).lt(rank(correlation(d['vwap'], adv180, 18)))


def alpha062(d):
    """((rank(correlation(vwap,sum(adv20,22),10))<rank(((rank(open)+rank(open))<(rank(((high+low)/2))+rank(high)))))*-1)"""
    adv20 = sma(d['volume'], 20)
    return -1 * rank(correlation(d['vwap'], sma(adv20, 22), 10)).lt(rank((rank(d['open']) + rank(d['open'])).lt(rank((d['high'] + d['low']) / 2) + rank(d['high']))))


def alpha063(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha064(d):
    """((rank(correlation(sum((open*0.178404+low*(1-0.178404)),13),sum(adv120,13),17))<rank(delta((((high+low)/2*0.178404+vwap*(1-0.178404)),4))))*-1)"""
    adv120 = sma(d['volume'], 120)
    return -1 * rank(correlation(sma(d['open'] * 0.178404 + d['low'] * (1 - 0.178404), 13), sma(adv120, 13), 17)).lt(rank(delta((d['high'] + d['low']) / 2 * 0.178404 + d['vwap'] * (1 - 0.178404), 4)))


def alpha065(d):
    """((rank(correlation((open*0.00817205+vwap*(1-0.00817205)),sum(adv60,9),6))<rank((open-ts_min(open,14))))*-1)"""
    adv60 = sma(d['volume'], 60)
    return -1 * rank(correlation(d['open'] * 0.00817205 + d['vwap'] * (1 - 0.00817205), sma(adv60, 9), 6)).lt(rank(d['open'] - ts_min(d['open'], 14)))


def alpha066(d):
    """((rank(decay_linear(delta(vwap,4),7))+Ts_Rank(decay_linear(((((low*0.96633+low*(1-0.96633))-vwap)/(open-((high+low)/2))),11),7)))*-1)"""
    denom = (d['open'] - (d['high'] + d['low']) / 2).replace(0, np.nan)
    p1 = rank(decay_linear(delta(d['vwap'], 4), 7))
    p2 = ts_rank(decay_linear((d['low'] - d['vwap']) / denom, 11), 7)
    return -1 * (p1 + p2)


def alpha067(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha068(d):
    """((Ts_Rank(correlation(rank(high),rank(adv15),9),14)<rank(delta(((close*0.518371)+(low*(1-0.518371))),1)))*-1)"""
    adv15 = sma(d['volume'], 15)
    return -1 * ts_rank(correlation(rank(d['high']), rank(adv15), 9), 14).lt(rank(delta(d['close'] * 0.518371 + d['low'] * 0.481629, 1)))


def alpha069(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha070(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha071(d):
    """max(Ts_Rank(decay_linear(corr(Ts_Rank(close,3),Ts_Rank(adv180,12),18),4),16),Ts_Rank(decay_linear((rank(((low+open)-(vwap+vwap)))^2),16),4))"""
    adv180 = sma(d['volume'], 180)
    p1 = ts_rank(decay_linear(correlation(ts_rank(d['close'], 3), ts_rank(adv180, 12), 18), 4), 16)
    p2 = ts_rank(decay_linear(rank((d['low'] + d['open'] - 2 * d['vwap']) ** 2), 16), 4)
    return np.maximum(p1, p2)


def alpha072(d):
    """(rank(decay_linear(corr((high+low)/2,adv40,9),10))/rank(decay_linear(corr(Ts_Rank(vwap,4),Ts_Rank(vol,19),7),3)))"""
    adv40 = sma(d['volume'], 40)
    num = rank(decay_linear(correlation((d['high'] + d['low']) / 2, adv40, 9), 10))
    den = rank(decay_linear(correlation(ts_rank(d['vwap'], 4), ts_rank(d['volume'], 19), 7), 3)).replace(0, np.nan)
    return num / den


def alpha073(d):
    """-1*max(rank(decay_linear(delta(vwap,5),3)),Ts_Rank(decay_linear(((delta((open*0.147155+low*(1-0.147155)),2)/(open*0.147155+low*(1-0.147155)))*-1),3),17))"""
    p1 = rank(decay_linear(delta(d['vwap'], 5), 3))
    inner = d['open'] * 0.147155 + d['low'] * 0.852845
    p2 = ts_rank(decay_linear(-1 * delta(inner, 2) / inner.replace(0, np.nan), 3), 17)
    return -1 * np.maximum(p1, p2)


def alpha074(d):
    """((rank(corr(close,sum(adv30,37),15))<rank(corr(rank((high*0.0261661+vwap*(1-0.0261661))),rank(vol),11)))*-1)"""
    adv30 = sma(d['volume'], 30)
    return -1 * rank(correlation(d['close'], sma(adv30, 37), 15)).lt(rank(correlation(rank(d['high'] * 0.0261661 + d['vwap'] * 0.9738339), rank(d['volume']), 11)))


def alpha075(d):
    """rank(corr(vwap,vol,4))<rank(corr(rank(low),rank(adv50),12))"""
    adv50 = sma(d['volume'], 50)
    return rank(correlation(d['vwap'], d['volume'], 4)).lt(rank(correlation(rank(d['low']), rank(adv50), 12)))


def alpha076(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha077(d):
    """min(rank(decay_linear(((high+low)/2+high-(vwap+high)),20)),rank(decay_linear(corr((high+low)/2,adv40,3),6)))"""
    adv40 = sma(d['volume'], 40)
    p1 = rank(decay_linear((d['high'] + d['low']) / 2 - d['vwap'], 20))
    p2 = rank(decay_linear(correlation((d['high'] + d['low']) / 2, adv40, 3), 6))
    return np.minimum(p1, p2)


def alpha078(d):
    """rank(corr(sum((low*0.352233+vwap*0.647767),20),sum(adv40,20),7))^rank(corr(rank(vwap),rank(vol),6))"""
    adv40 = sma(d['volume'], 40)
    return rank(correlation(ts_sum(d['low'] * 0.352233 + d['vwap'] * 0.647767, 20), ts_sum(adv40, 20), 7)).pow(rank(correlation(rank(d['vwap']), rank(d['volume']), 6)))


def alpha079(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha080(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha081(d):
    """((rank(Log(product(rank((rank(corr(vwap,sum(adv10,50),8))^4)),15)))<rank(corr(rank(vwap),rank(vol),5)))*-1)"""
    adv10 = sma(d['volume'], 10)
    p1 = rank(np.log(product(rank(rank(correlation(d['vwap'], ts_sum(adv10, 50), 8)).pow(4)), 15).replace(0, np.nan)))
    p2 = rank(correlation(rank(d['vwap']), rank(d['volume']), 5))
    return -1 * p1.lt(p2)


def alpha082(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha083(d):
    """((rank(delay(((high-low)/(sum(close,5)/5)),2))*rank(rank(volume)))/(((high-low)/(sum(close,5)/5))/(vwap-close)))"""
    inner = (d['high'] - d['low']) / (ts_sum(d['close'], 5) / 5).replace(0, np.nan)
    denom = (inner / (d['vwap'] - d['close'])).replace(0, np.nan)
    return rank(delay(inner, 2)) * rank(rank(d['volume'])) / denom


def alpha084(d):
    """SignedPower(Ts_Rank((vwap-ts_max(vwap,15)),21),delta(close,5))"""
    return ts_rank(d['vwap'] - ts_max(d['vwap'], 15), 21).pow(delta(d['close'], 5))


def alpha085(d):
    """rank(corr((high*0.876703+close*(1-0.876703)),adv30,10))^rank(corr(Ts_Rank((high+low)/2,4),Ts_Rank(vol,10),7))"""
    adv30 = sma(d['volume'], 30)
    return rank(correlation(d['high'] * 0.876703 + d['close'] * 0.123297, adv30, 10)).pow(rank(correlation(ts_rank((d['high'] + d['low']) / 2, 4), ts_rank(d['volume'], 10), 7)))


def alpha086(d):
    """((Ts_Rank(corr(close,sum(adv20,15),6),20)<rank(((open+close)-(vwap+open))))*-1)"""
    adv20 = sma(d['volume'], 20)
    return -1 * ts_rank(correlation(d['close'], sma(adv20, 15), 6), 20).lt(rank(d['close'] - d['vwap']))


def alpha087(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha088(d):
    """min(rank(decay_linear(((rank(open)+rank(low))-(rank(high)+rank(close))),8)),Ts_Rank(decay_linear(corr(Ts_Rank(close,8),Ts_Rank(adv60,21),8),7),3))"""
    adv60 = sma(d['volume'], 60)
    p1 = rank(decay_linear(rank(d['open']) + rank(d['low']) - rank(d['high']) - rank(d['close']), 8))
    p2 = ts_rank(decay_linear(correlation(ts_rank(d['close'], 8), ts_rank(adv60, 21), 8), 7), 3)
    return np.minimum(p1, p2)


def alpha089(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha090(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha091(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha092(d):
    """min(Ts_Rank(decay_linear(((((high+low)/2+close)<(low+open)),15),19),Ts_Rank(decay_linear(corr(rank(low),rank(adv30),8),7),7))"""
    adv30 = sma(d['volume'], 30)
    p1 = ts_rank(decay_linear(((d['high'] + d['low']) / 2 + d['close']).lt(d['low'] + d['open']), 15), 19)
    p2 = ts_rank(decay_linear(correlation(rank(d['low']), rank(adv30), 8), 7), 7)
    return np.minimum(p1, p2)


def alpha093(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha094(d):
    """((rank((vwap-ts_min(vwap,12)))^Ts_Rank(corr(Ts_Rank(vwap,20),Ts_Rank(adv60,4),18),3))*-1)"""
    adv60 = sma(d['volume'], 60)
    return -1 * rank(d['vwap'] - ts_min(d['vwap'], 12)).pow(ts_rank(correlation(ts_rank(d['vwap'], 20), ts_rank(adv60, 4), 18), 3))


def alpha095(d):
    """rank((open-ts_min(open,12)))<Ts_Rank((rank(corr(sma((high+low)/2,19),sma(adv40,19),13))^5),12)"""
    adv40 = sma(d['volume'], 40)
    return rank(d['open'] - ts_min(d['open'], 12)).lt(ts_rank(rank(correlation(sma((d['high'] + d['low']) / 2, 19), sma(adv40, 19), 13)).pow(5), 12))


def alpha096(d):
    """-1*max(Ts_Rank(decay_linear(corr(rank(vwap),rank(vol),4),4),8),Ts_Rank(decay_linear(ts_argmax(corr(Ts_Rank(close,7),Ts_Rank(adv60,4),4),13),14),13))"""
    adv60 = sma(d['volume'], 60)
    p1 = ts_rank(decay_linear(correlation(rank(d['vwap']), rank(d['volume']), 4), 4), 8)
    p2 = ts_rank(decay_linear(ts_argmax(correlation(ts_rank(d['close'], 7), ts_rank(adv60, 4), 4), 13), 14), 13)
    return -1 * np.maximum(p1, p2)


def alpha097(d):
    """SKIP: 需要 industry neutralization"""
    return None


def alpha098(d):
    """(rank(decay_linear(corr(vwap,sum(adv5,26),5),7))-rank(decay_linear(Ts_Rank(Ts_ArgMin(corr(rank(open),rank(adv15),21),9),7),8)))"""
    adv5 = sma(d['volume'], 5)
    adv15 = sma(d['volume'], 15)
    p1 = rank(decay_linear(correlation(d['vwap'], sma(adv5, 26), 5), 7))
    p2 = rank(decay_linear(ts_rank(ts_argmin(correlation(rank(d['open']), rank(adv15), 21), 9), 7), 8))
    return p1 - p2


def alpha099(d):
    """((rank(corr(sum((high+low)/2,20),sum(adv60,20),9))<rank(corr(low,vol,6)))*-1)"""
    adv60 = sma(d['volume'], 60)
    return -1 * rank(correlation(ts_sum((d['high'] + d['low']) / 2, 20), ts_sum(adv60, 20), 9)).lt(rank(correlation(d['low'], d['volume'], 6)))


def alpha100(d):
    """SKIP: 需要 industry neutralization + subindustry + market cap"""
    return None


def alpha101(d):
    """(close-open)/((high-low)+0.001)"""
    return (d['close'] - d['open']) / (d['high'] - d['low'] + 0.001)


# ═══════════════════════════════════════════════════════
# Registry + compute
# ═══════════════════════════════════════════════════════

ALPHA_FUNCTIONS: dict[str, callable] = {}
for i in range(1, 102):
    name = f"alpha{i:03d}"
    fn_name = name
    fn = globals().get(fn_name)
    if fn:
        ALPHA_FUNCTIONS[name] = fn


def compute_all_wq101(start_date=None, end_date=None) -> dict[str, pd.DataFrame]:
    """一次性计算全部可实现的 WQ101 因子.

    Returns:
        {alpha001: DataFrame, alpha002: ..., ...}
        跳过的因子返回空 DataFrame
    """
    print("Loading OHLCV data...")
    data = _prepare_data(start_date, end_date)
    if data['close'].empty:
        print("ERROR: No OHLCV data")
        return {}

    results = {}
    n = len(ALPHA_FUNCTIONS)
    for i, (name, fn) in enumerate(ALPHA_FUNCTIONS.items()):
        print(f"  [{i+1:3d}/{n}] {name} ...", end=" ")
        try:
            df = fn(data)
            if df is None:
                print("SKIP (needs industry/cap)")
                results[name] = pd.DataFrame()
                continue
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            if df.empty:
                print("EMPTY")
                results[name] = df
            else:
                df = process_factor(df.replace([np.inf, -np.inf], np.nan))
                results[name] = df
                print(f"{df.shape[0]}d × {df.shape[1]}s")
        except Exception as e:
            print(f"ERROR: {e}")
            results[name] = pd.DataFrame()

    return results
