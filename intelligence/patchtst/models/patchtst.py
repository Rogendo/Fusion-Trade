"""
models/patchtst.py — Channel-Independent PatchTST for financial time series.
(Copied from FX/transformers/models/patchtst.py — uses relative package imports)
"""

import math
from pathlib import Path
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config import MODEL_CONFIG, NUM_FEATURES, INTERVAL_CONFIG, NUM_CLASSES

import logging
logger = logging.getLogger("fx_transformers.model")


class PatchEmbedding(nn.Module):
    def __init__(self, patch_len: int, stride: int, d_model: int) -> None:
        super().__init__()
        self.patch_len = patch_len
        self.stride    = stride
        self.projection = nn.Linear(patch_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        patches = x.unfold(dimension=1, size=self.patch_len, step=self.stride)
        return self.projection(patches)


class LearnablePositionalEncoding(nn.Module):
    def __init__(self, num_patches: int, d_model: int) -> None:
        super().__init__()
        self.pe = nn.Embedding(num_patches, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(x.size(1), device=x.device)
        return x + self.pe(positions)


class TransformerEncoderBlock(nn.Module):
    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn  = nn.MultiheadAttention(embed_dim=d_model, num_heads=num_heads,
                                            dropout=dropout, batch_first=True)
        self.drop1 = nn.Dropout(dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn   = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.GELU(), nn.Dropout(dropout), nn.Linear(d_ff, d_model),
        )
        self.drop2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        normed = self.norm1(x)
        attn_out, _ = self.attn(normed, normed, normed)
        x = x + self.drop1(attn_out)
        x = x + self.drop2(self.ffn(self.norm2(x)))
        return x


class PatchTST(nn.Module):
    def __init__(self, interval: str, cfg=None, n_features: int = NUM_FEATURES) -> None:
        super().__init__()
        if cfg is None:
            cfg = MODEL_CONFIG

        iv_cfg      = INTERVAL_CONFIG[interval]
        patch_len   = iv_cfg.patch_len
        stride      = iv_cfg.stride
        num_patches = iv_cfg.num_patches
        d_model     = cfg.d_model
        num_heads   = cfg.num_heads
        num_layers  = cfg.num_layers
        d_ff        = cfg.d_ff
        dropout     = cfg.dropout

        self.n_features = n_features
        self.interval   = interval

        self.patch_embed   = PatchEmbedding(patch_len, stride, d_model)
        self.pos_enc       = LearnablePositionalEncoding(num_patches, d_model)
        self.encoder       = nn.ModuleList([
            TransformerEncoderBlock(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.encoder_norm  = nn.LayerNorm(d_model)
        self.input_dropout = nn.Dropout(dropout)

        from .heads import RegressionHead, ClassificationHead
        self.price_head = RegressionHead(d_model, cfg.head_dim)
        self.dir_head   = ClassificationHead(d_model, cfg.head_dim, NUM_CLASSES)

        n_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        logger.info(f"PatchTST ({interval}) — params: {n_params:,}")

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, C = x.shape
        x = x.permute(0, 2, 1)
        x = x.reshape(B * C, T)
        x = self.patch_embed(x)
        x = self.input_dropout(x)
        x = self.pos_enc(x)
        for block in self.encoder:
            x = block(x)
        x = self.encoder_norm(x)
        x = x.mean(dim=1)
        x = x.reshape(B, C, -1)
        x = x.mean(dim=1)
        price_pred = self.price_head(x)
        dir_logits = self.dir_head(x)
        return price_pred, dir_logits


def build_model(interval: str, device: torch.device = None) -> PatchTST:
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PatchTST(interval=interval).to(device)
    logger.info(f"Model on device: {device}")
    return model
