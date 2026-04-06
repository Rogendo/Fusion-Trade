"""
data/preprocessor.py — Scaler utilities for PatchTST.
(Copied from FX/transformers/data/preprocessor.py — uses relative package imports)
"""

import pickle
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from ..config import FEATURE_NAMES, TRAIN_CONFIG

import logging
logger = logging.getLogger("fx_transformers.preprocessor")


def load_scaler(path) -> RobustScaler:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Scaler not found at {path}")
    with open(path, "rb") as f:
        scaler = pickle.load(f)
    logger.info(f"Scaler loaded ← {path}")
    return scaler


def save_scaler(scaler: RobustScaler, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info(f"Scaler saved → {path}")


def fit_scaler(train_df: pd.DataFrame) -> RobustScaler:
    scaler = RobustScaler()
    scaler.fit(train_df[FEATURE_NAMES].values)
    logger.info(f"Scaler fitted on {len(train_df)} training rows")
    return scaler


def transform(df: pd.DataFrame, scaler: RobustScaler) -> np.ndarray:
    return scaler.transform(df[FEATURE_NAMES].values).astype("float32")


def temporal_split(df, train_ratio=TRAIN_CONFIG.train_ratio, val_ratio=TRAIN_CONFIG.val_ratio):
    n = len(df)
    train_end = int(n * train_ratio)
    val_end   = int(n * (train_ratio + val_ratio))
    return df.iloc[:train_end].copy(), df.iloc[train_end:val_end].copy(), df.iloc[val_end:].copy()
