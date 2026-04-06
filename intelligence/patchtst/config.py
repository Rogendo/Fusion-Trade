"""
transformers/config_cpu.py

A CPU-optimized version of config.py.
Reduces model complexity and adjusts training parameters for faster iteration on CPU.
To use this, you can temporarily rename it to config.py.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR        = Path(__file__).parent
CHECKPOINTS_DIR = ROOT_DIR / "checkpoints"
EXPORTS_DIR     = ROOT_DIR / "exports"
DATA_CACHE_DIR  = ROOT_DIR / "data_cache"
LOGS_DIR        = ROOT_DIR / "logs"

for _d in (CHECKPOINTS_DIR, EXPORTS_DIR, DATA_CACHE_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# HuggingFace
# ---------------------------------------------------------------------------

HF_LSTM_REPO  = "rogendo/forex-lstm-models"
HF_TST_REPO   = "rogendo/forex-patchtst-models"

# ---------------------------------------------------------------------------
# Symbols
# ---------------------------------------------------------------------------

SYMBOLS: List[str] = [
    # --- Major FX ---
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X", "NZDUSD=X", "USDCAD=X", "DX-Y.NYB",
    # --- Major Crosses ---
    "AUDJPY=X", "EURJPY=X", "GBPJPY=X", "EURGBP=X", "EURAUD=X", "EURCAD=X", "GBPEUR=X", "AUDNZD=X",
    "CADJPY=X", "NZDJPY=X", "CHFJPY=X", "GBPCAD=X", "GBPCHF=X", "EURNZD=X",
    # --- Exotics ---
    "USDCNY=X", "USDZAR=X", "USDMXN=X", "USDTRY=X", "USDSGD=X",
    # --- Crypto & Commodities ---
    "BTC-USD", "ETH-USD", "GC=F", "CL=F",
    # --- Indices ---
    "^GSPC", "^IXIC", "^DJI", "^FTSE", "^N225"
]

INTERVALS: List[str] = ["15m", "30m", "1h", "4h"]

FX_PAIRS_ZERO_VOLUME: List[str] = [s for s in SYMBOLS if s.endswith("=X")]

# ---------------------------------------------------------------------------
# Per-interval configuration
# ---------------------------------------------------------------------------

@dataclass
class IntervalConfig:
    lookback:        int
    patch_len:       int
    stride:          int
    max_fetch_days:  int
    candles_per_day: int
    min_candles:     int = 0

    def __post_init__(self):
        if self.min_candles == 0:
            self.min_candles = self.lookback * 10

    @property
    def num_patches(self) -> int:
        return (self.lookback - self.patch_len) // self.stride + 1


INTERVAL_CONFIG: Dict[str, IntervalConfig] = {
    "5m": IntervalConfig(lookback=96, patch_len=8, stride=4, max_fetch_days=55, candles_per_day=288),
    "15m": IntervalConfig(lookback=96, patch_len=16, stride=8, max_fetch_days=55, candles_per_day=96),
    "30m": IntervalConfig(lookback=96, patch_len=16, stride=8, max_fetch_days=55, candles_per_day=48),
    "1h": IntervalConfig(lookback=96, patch_len=16, stride=8, max_fetch_days=720, candles_per_day=24),
    "4h": IntervalConfig(lookback=60, patch_len=10, stride=5, max_fetch_days=720, candles_per_day=6),
}

# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

FEATURE_NAMES: List[str] = [
    "Open", "High", "Low", "Close", "Volume",
    "Returns", "HL_Range", "Close_Position",
    "RSI", "MACD_hist", "ROC", "MOM",
    "ATR", "BB_width", "SMA_ratio",
    "hour_sin", "hour_cos",
]

NUM_FEATURES: int = len(FEATURE_NAMES)

RSI_PERIOD:    int = 14
MACD_FAST:     int = 12
MACD_SLOW:     int = 26
MACD_SIGNAL:   int = 9
ATR_PERIOD:    int = 14
BB_PERIOD:     int = 20
SMA_PERIOD:    int = 50
ROC_PERIOD:    int = 10
MOM_PERIOD:    int = 10

INDICATOR_WARMUP: int = SMA_PERIOD + 5

DIRECTION_THRESHOLD: Dict[str, float] = {
    "5m":  0.0001, "15m": 0.0002, "30m": 0.0003, "1h":  0.0005, "4h":  0.0010,
}

DIRECTION_CLASSES = {0: "DOWN", 1: "FLAT", 2: "UP"}
NUM_CLASSES: int = 3

# ---------------------------------------------------------------------------
# Model Architecture (CPU OPTIMIZED)
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    d_model:    int   = 256   # matches HuggingFace saved models
    num_heads:  int   = 4
    num_layers: int   = 4     # matches HuggingFace saved models
    d_ff:       int   = 512   # matches HuggingFace saved models
    dropout:    float = 0.20
    head_dim:   int   = 64    # matches HuggingFace saved models

    def __post_init__(self):
        assert self.d_model % self.num_heads == 0

MODEL_CONFIG = ModelConfig()

# ---------------------------------------------------------------------------
# Training (CPU OPTIMIZED)
# ---------------------------------------------------------------------------

@dataclass
class TrainConfig:
    train_ratio: float = 0.70
    val_ratio:   float = 0.15
    batch_size:    int  = 128     # INCREASED for CPU
    num_workers:   int  = 0       # CPU stable
    pin_memory:    bool = False   # CPU stable
    peak_lr:       float = 2e-4
    weight_decay:  float = 1e-4
    warmup_ratio:  float = 0.05
    max_epochs:    int   = 50
    patience:      int   = 10
    grad_clip:     float = 1.0
    alpha: float = 0.30
    beta:  float = 0.70

    def __post_init__(self):
        assert abs(self.alpha + self.beta - 1.0) < 1e-6

TRAIN_CONFIG = TrainConfig()

# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

NOISE_THRESHOLD:         float = 0.0005
STRONG_SIGNAL_THRESHOLD: float = 0.005
MIN_DIRECTION_PROB: float = 0.45

# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def sanitize_symbol(symbol: str) -> str:
    return symbol.replace("=", "_")

def model_filename(symbol: str, interval: str) -> str:
    return f"{sanitize_symbol(symbol)}_{interval}_patchtst.pt"

def scaler_filename(symbol: str, interval: str) -> str:
    return f"{sanitize_symbol(symbol)}_{interval}_scaler.pkl"

def meta_filename(symbol: str, interval: str) -> str:
    return f"{sanitize_symbol(symbol)}_{interval}_meta.json"

def checkpoint_path(symbol: str, interval: str) -> Path:
    from pathlib import Path
    return CHECKPOINTS_DIR / model_filename(symbol, interval)

def export_path(symbol: str, interval: str) -> Path:
    from pathlib import Path
    return EXPORTS_DIR / model_filename(symbol, interval)
