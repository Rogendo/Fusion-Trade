"""
Runtime model configuration loader.

Reads model_config.json at call time so that changes made via
PUT /api/v1/ml/config take effect on the next inference call
without any service restart.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "data" / "model_config.json"

_DEFAULTS: Dict[str, Any] = {
    "lstm": {
        "period_map": {
            "5m": "5d", "15m": "60d", "30m": "60d",
            "1h": "3mo", "4h": "6mo", "1d": "1y",
        },
        "confidence_threshold": 0.55,
        "direction_confidence_threshold": 0.50,
    },
    "patchtst": {
        "min_direction_prob": 0.45,
        "noise_threshold": 0.0005,
        "strong_signal_threshold": 0.005,
        "direction_threshold": {
            "5m": 0.0001, "15m": 0.0002, "30m": 0.0003,
            "1h": 0.0005, "4h": 0.0010,
        },
        "interval_lookback": {"5m": 96, "15m": 96, "30m": 96, "1h": 96, "4h": 60},
        "interval_patch_len": {"5m": 8, "15m": 16, "30m": 16, "1h": 16, "4h": 10},
    },
    "technical_indicators": {
        "rsi_period": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
        "atr_period": 14, "bb_period": 20, "sma_period": 50,
        "roc_period": 10, "mom_period": 10,
    },
    "news": {
        "fetch_limit": 15,
        "headlines_in_response": 10,
        "headlines_for_llm": 10,
        "sentiment_threshold_bullish": 0.15,
        "sentiment_threshold_bearish": -0.15,
    },
    "fusion": {
        "agreement_threshold": 0.80,
        "high_conviction_threshold": 70,
        "moderate_threshold": 50,
        "timeframes": ["15m", "30m", "1h", "4h"],
    },
}


def get_model_config() -> Dict[str, Any]:
    """
    Load and return model_config.json. Falls back to _DEFAULTS if the
    file is missing or unreadable.  Re-reads on every call so UI changes
    take effect immediately (no caching).
    """
    try:
        cfg = json.loads(_CONFIG_PATH.read_text())
        cfg.pop("_comment", None)
        return cfg
    except Exception as exc:
        logger.warning("runtime_config: could not read model_config.json (%s) — using defaults", exc)
        return _DEFAULTS


def get_lstm_cfg() -> Dict[str, Any]:
    return get_model_config().get("lstm", _DEFAULTS["lstm"])


def get_patchtst_cfg() -> Dict[str, Any]:
    return get_model_config().get("patchtst", _DEFAULTS["patchtst"])


def get_news_cfg() -> Dict[str, Any]:
    return get_model_config().get("news", _DEFAULTS["news"])


def get_fusion_cfg() -> Dict[str, Any]:
    return get_model_config().get("fusion", _DEFAULTS["fusion"])
