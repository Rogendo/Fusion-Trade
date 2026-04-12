"""
PatchTST inference service.

Uses the local intelligence.patchtst package — fully independent of the
FX project directory. Models are downloaded from HuggingFace on first use.

Returns all 3 softmax class probabilities (prob_up, prob_flat, prob_down)
so the fusion layer and frontend can show the full distribution.

Confidence fields:
  - confidence: probability of the predicted class
  - direction_confidence: same as confidence (PatchTST has no separate direction head)
  - prob_up / prob_flat / prob_down: full softmax distribution
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from intelligence.lstm_service import SignalResult

logger = logging.getLogger(__name__)

# Local exports directory for downloaded model files
_EXPORTS_DIR = Path(__file__).parent / "patchtst" / "exports"


def _ensure_model_files(exports_dir: Path, sym_safe: str, interval: str) -> bool:
    """Download model files from HuggingFace if not present locally."""
    model_path  = exports_dir / f"{sym_safe}_{interval}_patchtst.pt"
    scaler_path = exports_dir / f"{sym_safe}_{interval}_scaler.pkl"
    if model_path.exists() and scaler_path.exists():
        return True
    try:
        from huggingface_hub import hf_hub_download  # type: ignore[import]
        exports_dir.mkdir(parents=True, exist_ok=True)
        for fname in [f"{sym_safe}_{interval}_patchtst.pt", f"{sym_safe}_{interval}_scaler.pkl"]:
            hf_hub_download(
                repo_id="Rogendo/forex-patchtst-models",
                filename=fname,
                local_dir=str(exports_dir),
            )
        logger.info("Downloaded PatchTST model for %s %s from HuggingFace", sym_safe, interval)
        return True
    except Exception as e:
        logger.debug("PatchTST model unavailable for %s %s: %s", sym_safe, interval, e)
        return False


def _normalise_direction(
    probs,  # numpy array [prob_down, prob_flat, prob_up]
    min_direction_prob: float = 0.45,
) -> tuple[str, float, float, float, float]:
    """
    Returns (signal, top_class_confidence, prob_up, prob_flat, prob_down).
    DIRECTION_CLASSES = {0: "DOWN", 1: "FLAT", 2: "UP"}

    Signals with a winning class probability below min_direction_prob are
    demoted to HOLD — this threshold is read from model_config.json at
    runtime (patchtst.min_direction_prob).
    """
    import numpy as np
    prob_down = float(probs[0])
    prob_flat = float(probs[1])
    prob_up   = float(probs[2])
    cls_idx   = int(np.argmax(probs))

    if cls_idx == 2:
        if prob_up < min_direction_prob:
            return "HOLD", 0.0, prob_up, prob_flat, prob_down
        return "BUY",  prob_up,   prob_up, prob_flat, prob_down
    if cls_idx == 0:
        if prob_down < min_direction_prob:
            return "HOLD", 0.0, prob_up, prob_flat, prob_down
        return "SELL", prob_down, prob_up, prob_flat, prob_down
    # FLAT — emit HOLD with 0.0 confidence (signal not actionable)
    return "HOLD", 0.0, prob_up, prob_flat, prob_down


def get_patchtst_signal(symbol: str, interval: str) -> Optional[SignalResult]:
    """
    Run PatchTST inference for one symbol/interval.
    Returns None if the model is not available.
    """
    try:
        import torch   # type: ignore[import]
        import numpy as np  # type: ignore[import]

        # Import from the local package — no sys.path manipulation needed
        from intelligence.patchtst.config import sanitize_symbol, INTERVAL_CONFIG, FEATURE_NAMES
        from intelligence.patchtst.models.patchtst import build_model
        from intelligence.patchtst.data.fetcher import fetch_ohlcv
        from intelligence.patchtst.data.features import build_features
        from intelligence.patchtst.data.preprocessor import load_scaler

        sym_safe = sanitize_symbol(symbol)

        if not _ensure_model_files(_EXPORTS_DIR, sym_safe, interval):
            return None

        model_path  = _EXPORTS_DIR / f"{sym_safe}_{interval}_patchtst.pt"
        scaler_path = _EXPORTS_DIR / f"{sym_safe}_{interval}_scaler.pkl"

        device = torch.device("cpu")
        model  = build_model(interval, device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()

        scaler = load_scaler(str(scaler_path))
        cfg    = INTERVAL_CONFIG[interval]

        df_raw = fetch_ohlcv(symbol, interval)
        if df_raw is None or len(df_raw) < cfg.lookback + 50:
            return None

        df_feat = build_features(df_raw)
        df_feat = df_feat.dropna()
        if len(df_feat) < cfg.lookback:
            return None

        window        = df_feat[FEATURE_NAMES].values[-cfg.lookback:]
        window_scaled = scaler.transform(window)
        x = torch.tensor(window_scaled, dtype=torch.float32).unsqueeze(0).to(device)

        with torch.no_grad():
            price_pred, dir_logits = model(x)

        from intelligence.runtime_config import get_patchtst_cfg
        ptst_cfg = get_patchtst_cfg()
        min_dir_prob = float(ptst_cfg.get("min_direction_prob", 0.45))

        probs = torch.softmax(dir_logits[0], dim=-1).cpu().numpy()
        signal, confidence, prob_up, prob_flat, prob_down = _normalise_direction(probs, min_dir_prob)

        current_price   = float(df_feat["Close"].iloc[-1])
        predicted_price = float(price_pred[0, 0].item()) if price_pred is not None else current_price

        return SignalResult(
            signal=signal,
            confidence=confidence,
            direction_confidence=confidence,  # PatchTST has no separate direction head
            current_price=current_price,
            predicted_price=predicted_price,
            prob_up=round(prob_up, 4),
            prob_flat=round(prob_flat, 4),
            prob_down=round(prob_down, 4),
        )

    except Exception as e:
        logger.warning("PatchTST inference failed for %s %s: %s", symbol, interval, e)
        return None
