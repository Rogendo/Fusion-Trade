"""Model registry — tracks deployed model versions and their live performance."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ModelRegistry(SQLModel, table=True):
    __tablename__ = "model_registry"

    id: Optional[int] = Field(default=None, primary_key=True)

    symbol: str = Field(max_length=20, index=True)
    interval: str = Field(max_length=5)
    model_type: str = Field(max_length=20)  # lstm | patchtst

    # HF Hub reference
    repo_id: Optional[str] = Field(default=None, max_length=255)
    filename: Optional[str] = Field(default=None, max_length=255)

    # Performance from blind simulation / backtest
    win_rate: Optional[float] = Field(default=None)
    profit_factor: Optional[float] = Field(default=None)
    max_drawdown: Optional[float] = Field(default=None)
    total_trades: Optional[int] = Field(default=None)
    direction_accuracy: Optional[float] = Field(default=None)

    # Metadata
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
