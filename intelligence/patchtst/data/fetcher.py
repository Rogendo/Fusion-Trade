"""
data/fetcher.py — OHLCV fetcher for PatchTST.
(Copied from FX/transformers/data/fetcher.py — uses relative package imports)
"""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from ..config import INTERVAL_CONFIG, FX_PAIRS_ZERO_VOLUME, DATA_CACHE_DIR

import logging
logger = logging.getLogger("fx_transformers.fetcher")

CHUNK_DAYS      = 55
OVERLAP_DAYS    = 2
MAX_RETRIES     = 3
RETRY_BASE_SLEEP = 2


def fetch_ohlcv(symbol: str, interval: str, use_cache: bool = True,
                force_refresh: bool = False) -> pd.DataFrame:
    if interval not in INTERVAL_CONFIG:
        raise ValueError(f"Unsupported interval '{interval}'. Choose from: {list(INTERVAL_CONFIG.keys())}")

    cfg = INTERVAL_CONFIG[interval]
    cache_path = _cache_path(symbol, interval)
    if use_cache and not force_refresh and cache_path.exists():
        df = pd.read_parquet(cache_path)
        logger.info(f"Loaded {symbol} ({interval}) from cache: {len(df)} candles")
        _validate(df, symbol, interval, cfg.min_candles)
        return df

    if interval == "4h":
        df = _fetch_and_resample_4h(symbol, cfg.max_fetch_days)
    else:
        df = _fetch_single(symbol, interval, cfg.max_fetch_days)

    df = _ensure_volume(df, symbol, interval)
    df = _clean(df)
    _validate(df, symbol, interval, cfg.min_candles)

    if use_cache:
        df.to_parquet(cache_path)
        logger.info(f"Cached {symbol} ({interval}): {len(df)} candles → {cache_path.name}")

    return df


def _fetch_single(symbol: str, interval: str, max_days: int) -> pd.DataFrame:
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=max_days)
    logger.info(f"Fetching {symbol} ({interval}): {start.date()} → {end.date()}")
    df = _yf_download(symbol, interval, start, end)
    logger.info(f"  Got {len(df)} candles")
    return df


def _fetch_and_resample_4h(symbol: str, max_days: int) -> pd.DataFrame:
    df_1h = _fetch_single(symbol, "1h", max_days)
    df_4h = df_1h.resample("4h", label="left", closed="left").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
    }).dropna(subset=["Open", "Close"])
    logger.info(f"  Resampled 1h → 4h: {len(df_1h)} → {len(df_4h)} candles")
    return df_4h


def _yf_download(symbol: str, interval: str, start: datetime, end: datetime) -> pd.DataFrame:
    for attempt in range(MAX_RETRIES):
        try:
            raw = yf.download(symbol, start=start, end=end, interval=interval,
                              auto_adjust=True, progress=False, timeout=30)
            if raw.empty:
                raise ValueError("Empty response from yfinance")
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.droplevel(1)
            raw = raw[["Open", "High", "Low", "Close", "Volume"]].astype("float64")
            if raw.index.tz is None:
                raw.index = raw.index.tz_localize("UTC")
            else:
                raw.index = raw.index.tz_convert("UTC")
            return raw
        except Exception as e:
            wait = RETRY_BASE_SLEEP ** (attempt + 1)
            logger.warning(f"yfinance attempt {attempt + 1}/{MAX_RETRIES} failed for "
                           f"{symbol} ({interval}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"yfinance download failed after {MAX_RETRIES} attempts for {symbol} ({interval})")


def _ensure_volume(df: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
    is_fx    = symbol in FX_PAIRS_ZERO_VOLUME
    has_volume = df["Volume"].sum() > 0

    if not is_fx and has_volume:
        zero_mask = df["Volume"] == 0
        if zero_mask.any():
            df = df.copy()
            df.loc[zero_mask, "Volume"] = _tick_volume_from_ohlc(df)[zero_mask]
            logger.info(f"Filled {zero_mask.sum()} zero-volume candles for {symbol}")
        return df

    logger.info(f"Calculating tick volume for {symbol} ({interval})")
    interval_minutes = _interval_to_minutes(interval)
    if interval_minutes and interval_minutes > 5:
        tv = _aggregate_tick_volume_from_5m(df, symbol, interval, interval_minutes)
        if tv is not None:
            df = df.copy()
            df["Volume"] = tv
            logger.info(f"✓ Tick volume from 5m aggregation for {symbol}: avg={tv.mean():.0f}")
            return df

    tv = _tick_volume_from_ohlc(df)
    df = df.copy()
    df["Volume"] = tv
    logger.info(f"✓ Tick volume from OHLC formula for {symbol}: avg={tv.mean():.0f}")
    return df


def _tick_volume_from_ohlc(df: pd.DataFrame) -> pd.Series:
    price_range  = df["High"] - df["Low"]
    price_change = (df["Close"] - df["Open"]).abs()
    avg_price    = (df["High"] + df["Low"] + df["Close"] + df["Open"]) / 4
    return ((price_range + price_change) / avg_price) * 1_000_000


def _aggregate_tick_volume_from_5m(df, symbol, interval, interval_minutes) -> Optional[pd.Series]:
    try:
        end   = df.index[-1] + timedelta(minutes=interval_minutes)
        start = df.index[0]
        raw_5m = _yf_download(symbol, "5m", start, end)
        if raw_5m.empty:
            return None
        tv_5m = _tick_volume_from_ohlc(raw_5m)
        aggregated = []
        for idx in df.index:
            candle_end = idx + timedelta(minutes=interval_minutes)
            mask = (raw_5m.index >= idx) & (raw_5m.index < candle_end)
            period_tvs = tv_5m[mask]
            aggregated.append(float(period_tvs.sum()) if len(period_tvs) > 0
                              else float(_tick_volume_from_ohlc(df.loc[[idx]]).iloc[0]))
        return pd.Series(aggregated, index=df.index, dtype="float64")
    except Exception as e:
        logger.error(f"5m tick-volume aggregation error for {symbol}: {e}")
        return None


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()
    df = df.dropna()
    return df.astype("float64")


def _validate(df, symbol, interval, min_candles):
    if len(df) < min_candles:
        raise RuntimeError(f"Insufficient data for {symbol} ({interval}): "
                           f"got {len(df)} candles, need {min_candles}.")


def _interval_to_minutes(interval: str) -> Optional[int]:
    mapping = {"1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30,
               "60m": 60, "1h": 60, "2h": 120, "4h": 240, "1d": 1440}
    return mapping.get(interval)


def _cache_path(symbol: str, interval: str) -> Path:
    safe = symbol.replace("=", "_").replace("-", "_")
    return DATA_CACHE_DIR / f"{safe}_{interval}.parquet"
