"""ML management endpoints — model registry, worker triggers, runtime config."""

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_verified_user, limiter
from app.models.model_registry import ModelRegistry
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "data" / "model_config.json"


# ── Config helpers ─────────────────────────────────────────────────────────────

def _load_config() -> Dict[str, Any]:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception as exc:
        logger.warning("Could not load model_config.json: %s", exc)
        return {}


def _save_config(cfg: Dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base (overlay wins on conflicts)."""
    result = copy.deepcopy(base)
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/registry")
async def list_registry(
    model_type: str = Query(default=None),
    _: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    """List all registered models with their performance stats."""
    query = select(ModelRegistry).where(ModelRegistry.is_active == True)  # noqa: E712
    if model_type:
        query = query.where(ModelRegistry.model_type == model_type)
    models = db.exec(query).all()
    return {"models": models}


@router.get("/config")
async def get_model_config(
    _: User = Depends(get_current_verified_user),
):
    """Return the current runtime model configuration."""
    cfg = _load_config()
    # Strip internal comment key before returning
    cfg.pop("_comment", None)
    return cfg


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


@router.put("/config")
@limiter.limit("30/minute")
async def update_model_config(
    request: Request,
    body: ConfigUpdateRequest,
    _: User = Depends(get_current_verified_user),
):
    """
    Merge-update model configuration. Accepts a partial config dict —
    only provided keys are overwritten; missing keys keep existing values.
    Changes take effect on the NEXT fusion/sentiment call (no restart needed).
    """
    try:
        current = _load_config()
        merged = _deep_merge(current, body.config)
        _save_config(merged)
        merged.pop("_comment", None)
        return {"status": "saved", "config": merged}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {exc}")


@router.post("/config/reset")
@limiter.limit("5/minute")
async def reset_model_config(
    request: Request,
    _: User = Depends(get_current_verified_user),
):
    """Reset all model parameters to factory defaults."""
    defaults = {
        "lstm": {
            "period_map": {"5m": "5d", "15m": "60d", "30m": "60d", "1h": "3mo", "4h": "6mo", "1d": "1y"},
            "confidence_threshold": 0.55,
            "direction_confidence_threshold": 0.50,
        },
        "patchtst": {
            "min_direction_prob": 0.45,
            "noise_threshold": 0.0005,
            "strong_signal_threshold": 0.005,
            "direction_threshold": {"5m": 0.0001, "15m": 0.0002, "30m": 0.0003, "1h": 0.0005, "4h": 0.0010},
            "interval_lookback": {"5m": 96, "15m": 96, "30m": 96, "1h": 96, "4h": 60},
            "interval_patch_len": {"5m": 8, "15m": 16, "30m": 16, "1h": 16, "4h": 10},
        },
        "technical_indicators": {
            "rsi_period": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
            "atr_period": 14, "bb_period": 20, "sma_period": 50,
            "roc_period": 10, "mom_period": 10,
        },
        "news": {
            "fetch_limit": 15, "headlines_in_response": 10, "headlines_for_llm": 10,
            "sentiment_threshold_bullish": 0.15, "sentiment_threshold_bearish": -0.15,
        },
        "fusion": {
            "agreement_threshold": 0.80,
            "high_conviction_threshold": 70,
            "moderate_threshold": 50,
            "timeframes": ["15m", "30m", "1h", "4h"],
        },
    }
    _save_config(defaults)
    return {"status": "reset", "config": defaults}


@router.post("/backtest/trigger")
async def trigger_backtest(
    symbol: str = Query(...),
    interval: str = Query(...),
    _: User = Depends(get_current_verified_user),
):
    """Queue a backtest job for the specified symbol/interval."""
    from workers.celery_app import celery_app
    task = celery_app.send_task(
        "workers.tasks.backtest.run_backtest",
        kwargs={"symbol": symbol, "interval": interval},
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/predict/trigger")
async def trigger_predictions(
    _: User = Depends(get_current_verified_user),
):
    """Manually trigger the scheduled prediction worker."""
    from workers.tasks.predictions import run_scheduled_predictions
    task = run_scheduled_predictions.delay()
    return {"task_id": task.id, "status": "queued"}
