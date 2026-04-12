"""
LSTM inference wrapper.

Delegates to intelligence.vendors.lstm_engine — a self-contained engine
with no dependency on the FX project directory.

Confidence fields:
  - confidence: magnitude-based (abs_change × 80–100, capped at 0.8–1.0)
  - direction_confidence: LSTM direction head probability (binary output)
  - direction_accuracy: historical model accuracy % computed at runtime
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    signal: str                              # BUY | SELL | HOLD
    confidence: float                        # magnitude-based price-change confidence (0–1)
    direction_confidence: float              # LSTM direction head prob / PatchTST top-class prob
    current_price: float
    predicted_price: float

    # PatchTST full class probabilities (None for LSTM)
    prob_up: Optional[float] = None
    prob_flat: Optional[float] = None
    prob_down: Optional[float] = None

    # Historical model accuracy (from metadata)
    direction_accuracy: Optional[float] = None

    # Technical indicators (from LSTM output — used to build LLM prompt)
    rsi: Optional[float] = None
    macd: Optional[float] = None
    atr: Optional[float] = None
    support: Optional[float] = None
    resistance: Optional[float] = None
    trend: Optional[str] = None

    # Risk levels
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # OHLCV candles for LLM prompt (last 30 candles)
    ohlcv: list = field(default_factory=list)


def _normalise_signal(raw: str) -> str:
    """Map STRONG BUY / STRONG SELL → BUY / SELL."""
    raw = (raw or "").upper()
    if "BUY" in raw:
        return "BUY"
    if "SELL" in raw:
        return "SELL"
    return "HOLD"


def get_lstm_signal(symbol: str, interval: str) -> Optional[SignalResult]:
    """
    Run LSTM inference for one symbol/interval.
    Returns None if the model is unavailable or inference fails.
    """
    try:
        from intelligence.vendors.lstm_engine import get_lstm_engine
        from intelligence.runtime_config import get_lstm_cfg

        engine = get_lstm_engine()

        period_map = get_lstm_cfg().get("period_map", {
            "5m": "5d", "15m": "60d", "30m": "60d",
            "1h": "3mo", "4h": "6mo", "1d": "1y",
        })
        period = period_map.get(interval, "3mo")
        result = engine.make_predictions(symbol=symbol, period=period, interval=interval)

        latest  = result.get("latest", {})
        metrics = result.get("metrics", {})
        ohlcv   = result.get("ohlc_data", [])

        return SignalResult(
            signal=_normalise_signal(latest.get("signal", "HOLD")),
            confidence=float(latest.get("confidence", 0.0)),
            direction_confidence=float(latest.get("direction_confidence", 0.0)),
            current_price=float(latest.get("current_price", 0.0)),
            predicted_price=float(latest.get("predicted_price", 0.0)),
            direction_accuracy=float(metrics.get("direction_accuracy_percent", 0.0)) if metrics else None,
            rsi=latest.get("rsi"),
            macd=latest.get("macd"),
            atr=latest.get("atr"),
            support=latest.get("support"),
            resistance=latest.get("resistance"),
            trend=latest.get("trend"),
            stop_loss=latest.get("stop_loss"),
            take_profit=latest.get("take_profit"),
            ohlcv=ohlcv,
        )
    except Exception as e:
        logger.warning("LSTM inference failed for %s %s: %s", symbol, interval, e)
        return None
