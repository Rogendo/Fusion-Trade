"""
transformers/models/heads.py

Output heads that sit on top of the shared PatchTST backbone.

Both heads receive a (batch, d_model) representation from the backbone
and produce independent predictions. The backbone learns features that
are simultaneously useful for both tasks.

RegressionHead     → predicted next-close price (scaled, float)
ClassificationHead → direction logits (DOWN=0, FLAT=1, UP=2)
"""

import torch
import torch.nn as nn


class RegressionHead(nn.Module):
    """
    Predicts the scaled next-close price.

    Architecture:
        Linear(d_model → head_dim) → GELU → Dropout → Linear(head_dim → 1)

    Output shape: (batch, 1)
    """

    def __init__(self, d_model: int, head_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, head_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(head_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, d_model)
        return self.net(x)   # (batch, 1)


class ClassificationHead(nn.Module):
    """
    Predicts direction logits: DOWN (0), FLAT (1), UP (2).

    Returns raw logits — CrossEntropyLoss expects logits, not softmax.

    Architecture:
        Linear(d_model → head_dim) → GELU → Dropout → Linear(head_dim → n_classes)

    Output shape: (batch, n_classes)
    """

    def __init__(
        self,
        d_model:   int,
        head_dim:  int,
        n_classes: int,
        dropout:   float = 0.1,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, head_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(head_dim, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, d_model)
        return self.net(x)   # (batch, n_classes)
