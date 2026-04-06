"""
Standalone LSTM inference engine for FusionTrade.

Reproduces the inference pipeline from FX/model_service.py without any
dependency on the FX project directory. All code is self-contained here.

Downloads models from Rogendo/forex-lstm-models on HuggingFace Hub.
Feature engineering mirrors the original model_service.py exactly.
"""
from __future__ import annotations

import logging
import os
import pickle
import threading
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from huggingface_hub import hf_hub_download
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

HF_REPO_ID   = "Rogendo/forex-lstm-models"
DEFAULT_LOOKBACK = 25

# Feature set the LSTM was trained on
DEFAULT_FEATURES = [
    "Open", "High", "Low", "Close", "Volume",
    "Returns", "HL_Range", "SMA_20", "EMA_10",
    "RSI", "MACD", "MACD_Signal", "MACD_Hist",
    "ATR", "BB_Upper", "BB_Middle", "BB_Lower",
    "Volume_SMA", "Price_Change", "High_Low_Ratio",
]

# Technical indicator parameters (match training config)
RSI_PERIOD   = 14
MACD_FAST    = 12
MACD_SLOW    = 26
MACD_SIGNAL  = 9
ATR_PERIOD   = 14
BB_PERIOD    = 20
SMA_PERIOD   = 20
EMA_PERIOD   = 10

# Signal generation thresholds
NOISE_THRESHOLD  = 0.0005
STRONG_THRESHOLD = 0.005

# ATR multipliers for SL/TP per timeframe
ATR_MULTIPLIERS = {
    "5m": 1.0, "15m": 1.2, "30m": 1.5,
    "1h": 2.0, "4h": 2.5, "1d": 3.0,
}


class LSTMInferenceEngine:
    """Loads LSTM models from HuggingFace and runs inference."""

    def __init__(self):
        self._cache: Dict[Tuple[str, str], Dict] = {}
        self._lock  = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Model loading                                                       #
    # ------------------------------------------------------------------ #

    def _load_model(self, symbol: str, interval: str) -> Dict:
        key = (symbol, interval)
        with self._lock:
            if key in self._cache:
                return self._cache[key]

        sym_safe = symbol.replace("=", "_").replace("-", "_")
        model_file   = f"{sym_safe}_{interval}_model.h5"
        feature_file = f"{sym_safe}_{interval}_features.pkl"
        scaler_file  = f"{sym_safe}_{interval}_scaler.pkl"

        logger.info("Fetching %s (%s) from HuggingFace...", symbol, interval)

        from tensorflow.keras.models import load_model as keras_load  # type: ignore

        model_path   = hf_hub_download(repo_id=HF_REPO_ID, filename=model_file)
        feature_path = hf_hub_download(repo_id=HF_REPO_ID, filename=feature_file)

        logger.info("Loading LSTM model from cache: %s", model_path)
        model = keras_load(model_path, compile=False)

        feature_info = {}
        try:
            with open(feature_path, "rb") as f:
                feature_info = pickle.load(f)
        except Exception as e:
            logger.warning("Could not load feature info for %s (%s): %s", symbol, interval, e)

        saved_scaler = None
        try:
            scaler_path = hf_hub_download(repo_id=HF_REPO_ID, filename=scaler_file)
            with open(scaler_path, "rb") as f:
                saved_scaler = pickle.load(f)
            logger.info("Loaded scaler for %s (%s)", symbol, interval)
        except Exception as e:
            logger.warning("Could not load scaler for %s (%s): %s. Will fit fresh.", symbol, interval, e)

        model_data = {
            "model":         model,
            "feature_names": feature_info.get("feature_names", DEFAULT_FEATURES),
            "lookback":      feature_info.get("lookback", DEFAULT_LOOKBACK),
            "scaler":        saved_scaler,
        }

        with self._lock:
            self._cache[key] = model_data
        return model_data

    # ------------------------------------------------------------------ #
    #  Data fetching                                                       #
    # ------------------------------------------------------------------ #

    def _fetch_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        import time
        for attempt in range(3):
            try:
                data = yf.download(symbol, period=period, interval=interval,
                                   progress=False, threads=False, timeout=30)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    data = data.astype(np.float64)
                    data = self._ensure_volume(data, symbol, interval)
                    return data
                logger.warning("Attempt %d: Empty data for %s. Retrying...", attempt + 1, symbol)
            except Exception as e:
                logger.warning("Attempt %d failed for %s: %s", attempt + 1, symbol, e)
            time.sleep(2 ** (attempt + 1))
        raise RuntimeError(f"Failed to fetch data for {symbol} after 3 attempts.")

    def _ensure_volume(self, data: pd.DataFrame, symbol: str, interval: str) -> pd.DataFrame:
        is_fx = symbol.endswith("=X")
        if is_fx or data["Volume"].sum() == 0:
            tv = self._tick_volume(data)
            data = data.copy()
            data["Volume"] = tv
        else:
            zero_mask = data["Volume"] == 0
            if zero_mask.any():
                data = data.copy()
                data.loc[zero_mask, "Volume"] = self._tick_volume(data)[zero_mask]
        return data

    @staticmethod
    def _tick_volume(data: pd.DataFrame) -> pd.Series:
        price_range  = data["High"] - data["Low"]
        price_change = (data["Close"] - data["Open"]).abs()
        avg_price    = (data["High"] + data["Low"] + data["Close"] + data["Open"]) / 4
        return ((price_range + price_change) / avg_price) * 1_000_000

    # ------------------------------------------------------------------ #
    #  Feature engineering                                                 #
    # ------------------------------------------------------------------ #

    def _build_features(self, data: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
        df = data.copy()

        # Price-derived
        df["Returns"]       = df["Close"].pct_change()
        df["Price_Change"]  = df["Close"] - df["Open"]
        df["High_Low_Ratio"] = (df["High"] - df["Low"]) / df["Close"].replace(0, np.nan)
        df["HL_Range"]      = df["High"] - df["Low"]

        # Moving averages
        df["SMA_20"]  = df["Close"].rolling(SMA_PERIOD).mean()
        df["EMA_10"]  = df["Close"].ewm(span=EMA_PERIOD, adjust=False).mean()
        df["Volume_SMA"] = df["Volume"].rolling(20).mean()

        close = df["Close"].values
        high  = df["High"].values
        low   = df["Low"].values

        try:
            import talib
            df["RSI"]       = talib.RSI(close, timeperiod=RSI_PERIOD)
            macd, sig, hist = talib.MACD(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
            df["MACD"]      = macd
            df["MACD_Signal"] = sig
            df["MACD_Hist"] = hist
            df["ATR"]       = talib.ATR(high, low, close, timeperiod=ATR_PERIOD)
            upper, mid, lower = talib.BBANDS(close, timeperiod=BB_PERIOD)
            df["BB_Upper"]  = upper
            df["BB_Middle"] = mid
            df["BB_Lower"]  = lower
        except ImportError:
            # Pandas fallback (no talib)
            delta = df["Close"].diff()
            gain  = delta.clip(lower=0).ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD).mean()
            loss  = (-delta).clip(lower=0).ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD).mean()
            rs    = gain / loss.replace(0, np.nan)
            df["RSI"] = 100 - (100 / (1 + rs))

            ema_f = df["Close"].ewm(span=MACD_FAST, adjust=False).mean()
            ema_s = df["Close"].ewm(span=MACD_SLOW, adjust=False).mean()
            df["MACD"]       = ema_f - ema_s
            df["MACD_Signal"] = df["MACD"].ewm(span=MACD_SIGNAL, adjust=False).mean()
            df["MACD_Hist"]  = df["MACD"] - df["MACD_Signal"]

            hh = pd.Series(high); ll = pd.Series(low); cc = pd.Series(close)
            tr = pd.concat([hh - ll, (hh - cc.shift(1)).abs(), (ll - cc.shift(1)).abs()], axis=1).max(axis=1)
            df["ATR"] = tr.ewm(alpha=1/ATR_PERIOD, min_periods=ATR_PERIOD).mean()

            mid   = df["Close"].rolling(BB_PERIOD).mean()
            std   = df["Close"].rolling(BB_PERIOD).std()
            df["BB_Upper"]  = mid + 2 * std
            df["BB_Middle"] = mid
            df["BB_Lower"]  = mid - 2 * std

        # Only keep columns that the model was trained on
        available = [f for f in feature_names if f in df.columns]
        out = df[available].dropna()
        return out

    # ------------------------------------------------------------------ #
    #  Sequence preparation                                                #
    # ------------------------------------------------------------------ #

    def _prepare_sequences(self, data: pd.DataFrame, lookback: int,
                            feature_names: List[str],
                            saved_scaler=None) -> Tuple[np.ndarray, RobustScaler]:
        missing = [f for f in feature_names if f not in data.columns]
        if missing:
            raise ValueError(f"Missing features: {missing}")

        if saved_scaler is not None:
            scaled = saved_scaler.transform(data[feature_names])
            scaler = saved_scaler
        else:
            scaler = RobustScaler()
            scaled = scaler.fit_transform(data[feature_names])

        X = []
        for i in range(lookback, len(scaled)):
            X.append(scaled[i - lookback : i])
        return np.array(X), scaler

    # ------------------------------------------------------------------ #
    #  Technical indicators for LLM prompt                                #
    # ------------------------------------------------------------------ #

    def _calc_indicators(self, data: pd.DataFrame) -> Dict:
        try:
            close = data["Close"].values
            high  = data["High"].values
            low   = data["Low"].values
            try:
                import talib
                rsi  = float(talib.RSI(close, RSI_PERIOD)[-1])
                macd_v, _, _ = talib.MACD(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
                macd_v = float(macd_v[-1]) if not np.isnan(macd_v[-1]) else 0.0
                atr  = float(talib.ATR(high, low, close, ATR_PERIOD)[-1])
                upper, _, lower = talib.BBANDS(close, BB_PERIOD)
                support    = float(lower[-1])
                resistance = float(upper[-1])
                sma20 = float(talib.SMA(close, 20)[-1])
                sma50 = float(talib.SMA(close, 50)[-1]) if len(close) >= 50 else sma20
            except ImportError:
                rsi        = 50.0
                macd_v     = 0.0
                atr        = float(data["Close"].rolling(ATR_PERIOD).std().iloc[-1] or 0)
                resistance = float(data["High"].rolling(BB_PERIOD).mean().iloc[-1] + 2 * data["Close"].rolling(BB_PERIOD).std().iloc[-1])
                support    = float(data["Low"].rolling(BB_PERIOD).mean().iloc[-1])
                sma20      = float(data["Close"].rolling(20).mean().iloc[-1])
                sma50      = float(data["Close"].rolling(50).mean().iloc[-1])

            cur = close[-1]
            if cur > sma20 > sma50:
                trend = "Strong Uptrend"
            elif cur > sma20:
                trend = "Uptrend"
            elif cur < sma20 < sma50:
                trend = "Strong Downtrend"
            elif cur < sma20:
                trend = "Downtrend"
            else:
                trend = "Sideways"

            return {"rsi": round(rsi, 2), "macd": round(macd_v, 6),
                    "atr": round(atr, 5), "support": round(support, 5),
                    "resistance": round(resistance, 5), "trend": trend}
        except Exception as e:
            logger.warning("Indicator calculation failed: %s", e)
            return {"rsi": 50.0, "macd": 0.0, "atr": 0.0,
                    "support": 0.0, "resistance": 0.0, "trend": "Unknown"}

    # ------------------------------------------------------------------ #
    #  Signal generation                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_signal(pred_change: float, dir_conf: float) -> Tuple[str, float]:
        abs_change = abs(pred_change)
        if abs_change < NOISE_THRESHOLD:
            return "HOLD", 0.0
        if pred_change > STRONG_THRESHOLD:
            return "STRONG BUY", min(abs_change * 100, 1.0)
        if pred_change > 0:
            return "BUY", min(abs_change * 80, 0.8)
        if pred_change < -STRONG_THRESHOLD:
            return "STRONG SELL", min(abs_change * 100, 1.0)
        return "SELL", min(abs_change * 80, 0.8)

    # ------------------------------------------------------------------ #
    #  Risk levels                                                         #
    # ------------------------------------------------------------------ #

    def _calc_risk_levels(self, current_price: float, predicted_price: float,
                          signal: str, atr: float, interval: str) -> Dict:
        if atr <= 0:
            atr = current_price * 0.001

        sl_mult = ATR_MULTIPLIERS.get(interval, 2.0)
        sl_dist = atr * sl_mult

        if signal in ("BUY", "STRONG BUY"):
            sl  = current_price - sl_dist
            tp1 = current_price + sl_dist
            tp2 = current_price + sl_dist * 1.5
            tp3 = current_price + max(predicted_price - current_price, sl_dist * 2.0)
        elif signal in ("SELL", "STRONG SELL"):
            sl  = current_price + sl_dist
            tp1 = current_price - sl_dist
            tp2 = current_price - sl_dist * 1.5
            tp3 = current_price - max(current_price - predicted_price, sl_dist * 2.0)
        else:
            return {"stop_loss": 0.0, "take_profit": 0.0, "tp1": 0.0, "tp2": 0.0, "tp3": 0.0}

        return {"stop_loss": sl, "take_profit": tp2, "tp1": tp1, "tp2": tp2, "tp3": tp3}

    # ------------------------------------------------------------------ #
    #  Main inference entry point                                          #
    # ------------------------------------------------------------------ #

    def make_predictions(self, symbol: str, period: str, interval: str) -> Dict:
        """
        Run LSTM inference for a symbol/interval.
        Returns a dict compatible with what lstm_service.py expects:
          result['latest']      — current prediction
          result['metrics']     — direction_accuracy_percent etc.
          result['ohlc_data']   — last 30 OHLCV candles
        """
        model_data   = self._load_model(symbol, interval)
        model        = model_data["model"]
        feature_names = model_data["feature_names"]
        lookback     = model_data["lookback"]
        saved_scaler = model_data.get("scaler")

        data = self._fetch_data(symbol, period, interval)
        feat = self._build_features(data, feature_names)

        X, _ = self._prepare_sequences(feat, lookback, feature_names, saved_scaler)
        if len(X) == 0:
            raise RuntimeError("Not enough data to make predictions")

        price_pred, direction_pred = model.predict(X, verbose=0)

        actual_prices = data["Close"].values[lookback:]
        # Align with feature-dropped rows
        feat_start = len(data) - len(feat)
        actual_prices = feat["Close"].values[lookback:]

        base_prices       = feat["Close"].values[lookback - 1 : -1]
        predicted_changes = price_pred.flatten()
        predicted_prices  = base_prices * (1 + predicted_changes)

        latest_idx   = -1
        pred_change  = float(predicted_changes[latest_idx])
        dir_conf     = float(direction_pred.flatten()[latest_idx])
        signal, conf = self._generate_signal(pred_change, dir_conf)
        current_price = float(actual_prices[latest_idx])
        predicted_price = float(predicted_prices[latest_idx])

        # Technical indicators from raw data
        indicators = self._calc_indicators(data)
        risk       = self._calc_risk_levels(current_price, predicted_price, signal,
                                             indicators["atr"], interval)

        # Historical direction accuracy
        if len(actual_prices) > 1:
            act_dir  = (np.diff(actual_prices) > 0).astype(int)
            pred_dir = (predicted_changes[:-1] > 0).astype(int)
            min_len  = min(len(act_dir), len(pred_dir))
            dir_acc  = float(np.mean(act_dir[:min_len] == pred_dir[:min_len]) * 100)
        else:
            dir_acc = 0.0

        # OHLCV for LLM prompt (last 30 candles)
        ohlc_data = []
        for idx, row in data.tail(30).iterrows():
            ohlc_data.append({
                "time":   str(idx),
                "open":   round(float(row.get("Open",  0)), 5),
                "high":   round(float(row.get("High",  0)), 5),
                "low":    round(float(row.get("Low",   0)), 5),
                "close":  round(float(row.get("Close", 0)), 5),
                "volume": int(row.get("Volume", 0)),
            })

        latest = {
            "signal":             signal,
            "confidence":         round(conf, 4),
            "direction_confidence": round(dir_conf, 4),
            "current_price":      current_price,
            "predicted_price":    predicted_price,
            "predicted_change":   round(pred_change, 6),
            "stop_loss":          risk["stop_loss"],
            "take_profit":        risk["take_profit"],
            "tp1":                risk["tp1"],
            "tp2":                risk["tp2"],
            "tp3":                risk["tp3"],
            **indicators,
        }

        metrics = {"direction_accuracy_percent": dir_acc}

        return {
            "symbol":   symbol,
            "interval": interval,
            "latest":   latest,
            "metrics":  metrics,
            "ohlc_data": ohlc_data,
        }


# ── Singleton ────────────────────────────────────────────────────────────────
_instance: Optional[LSTMInferenceEngine] = None


def get_lstm_engine() -> LSTMInferenceEngine:
    global _instance
    if _instance is None:
        _instance = LSTMInferenceEngine()
    return _instance
