"""
data/features.py — Feature engineering for PatchTST.
(Copied from FX/transformers/data/features.py — uses relative package imports)
"""

import numpy as np
import pandas as pd

from ..config import (
    FEATURE_NAMES, RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    ATR_PERIOD, BB_PERIOD, SMA_PERIOD, ROC_PERIOD, MOM_PERIOD, INDICATOR_WARMUP,
)

import logging
logger = logging.getLogger("fx_transformers.features")

try:
    import talib
    _TALIB_AVAILABLE = True
except ImportError:
    _TALIB_AVAILABLE = False
    logger.warning("TA-Lib not found — falling back to pandas-based indicators")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    _check_columns(df)
    o = df["Open"].values.astype("float64")
    h = df["High"].values.astype("float64")
    l = df["Low"].values.astype("float64")
    c = df["Close"].values.astype("float64")
    v = df["Volume"].values.astype("float64")

    out = pd.DataFrame(index=df.index)
    out["Open"]   = o
    out["High"]   = h
    out["Low"]    = l
    out["Close"]  = c
    out["Volume"] = v

    close_s = pd.Series(c, index=df.index)
    out["Returns"] = close_s.pct_change()
    out["HL_Range"] = (h - l) / np.where(c != 0, c, np.nan)
    hl_diff = h - l
    out["Close_Position"] = np.where(hl_diff > 1e-10, (c - l) / np.maximum(hl_diff, 1e-10), 0.5)

    out["RSI"]       = _rsi(c)
    out["MACD_hist"] = _macd_hist(c)
    out["ROC"]       = _roc(c)
    out["MOM"]       = _mom(c)
    out["ATR"]       = _atr_normalised(h, l, c)
    out["BB_width"]  = _bb_width(c)
    out["SMA_ratio"] = _sma_ratio(c)

    hours = df.index.hour + df.index.minute / 60.0
    out["hour_sin"] = np.sin(2 * np.pi * hours / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hours / 24.0)

    out = out[FEATURE_NAMES]
    out = out.dropna()
    if out.empty:
        raise ValueError("No rows remain after building features.")
    logger.info(f"Features built: {len(out)} rows × {len(out.columns)} cols")
    return out


def _rsi(close):
    if _TALIB_AVAILABLE:
        return talib.RSI(close, timeperiod=RSI_PERIOD)
    delta = pd.Series(close).diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD).mean()
    avg_loss = loss.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).values


def _macd_hist(close):
    if _TALIB_AVAILABLE:
        _, _, hist = talib.MACD(close, fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL)
        return hist
    s = pd.Series(close)
    ema_fast  = s.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow  = s.ewm(span=MACD_SLOW, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal    = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    return (macd_line - signal).values


def _roc(close):
    if _TALIB_AVAILABLE:
        return talib.ROC(close, timeperiod=ROC_PERIOD)
    s = pd.Series(close)
    return ((s - s.shift(ROC_PERIOD)) / s.shift(ROC_PERIOD) * 100).values


def _mom(close):
    if _TALIB_AVAILABLE:
        return talib.MOM(close, timeperiod=MOM_PERIOD)
    s = pd.Series(close)
    return (s - s.shift(MOM_PERIOD)).values


def _atr_normalised(high, low, close):
    if _TALIB_AVAILABLE:
        atr = talib.ATR(high, low, close, timeperiod=ATR_PERIOD)
    else:
        h, l, c = pd.Series(high), pd.Series(low), pd.Series(close)
        prev_c = c.shift(1)
        tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / ATR_PERIOD, min_periods=ATR_PERIOD).mean().values
    return atr / np.where(close != 0, close, np.nan)


def _bb_width(close):
    if _TALIB_AVAILABLE:
        upper, middle, lower = talib.BBANDS(close, timeperiod=BB_PERIOD)
    else:
        s      = pd.Series(close)
        middle = s.rolling(BB_PERIOD).mean().values
        std    = s.rolling(BB_PERIOD).std(ddof=0).values
        upper  = middle + 2 * std
        lower  = middle - 2 * std
    return np.where(middle != 0, (upper - lower) / middle, np.nan)


def _sma_ratio(close):
    if _TALIB_AVAILABLE:
        sma = talib.SMA(close, timeperiod=SMA_PERIOD)
    else:
        sma = pd.Series(close).rolling(SMA_PERIOD).mean().values
    return np.where(sma != 0, close / sma, np.nan)


def _check_columns(df):
    required = {"Open", "High", "Low", "Close", "Volume"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"build_features() missing required columns: {missing}")
