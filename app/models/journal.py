"""Prediction journal — every signal logged, outcomes verified."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class PredictionJournal(SQLModel, table=True):
    __tablename__ = "prediction_journal"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
    )

    # Foreign key to user (nullable — legacy rows have no user)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)

    # Signal metadata
    symbol: str = Field(max_length=20, index=True)
    interval: str = Field(max_length=5)
    signal: str = Field(max_length=20)          # BUY / SELL / HOLD / DIVERGENT

    # Both model signals
    lstm_signal: Optional[str] = Field(default=None, max_length=20)
    patchtst_signal: Optional[str] = Field(default=None, max_length=20)
    fusion_score: Optional[float] = Field(default=None)

    # Prices
    entry_price: Optional[float] = Field(default=None)
    predicted_price: Optional[float] = Field(default=None)
    take_profit_1: Optional[float] = Field(default=None)
    take_profit_2: Optional[float] = Field(default=None)
    take_profit_3: Optional[float] = Field(default=None)
    stop_loss: Optional[float] = Field(default=None)

    # Confidence
    confidence: Optional[float] = Field(default=None)

    # Outcome tracking
    status: str = Field(default="PENDING")       # PENDING | TP1_HIT | TP2_HIT | TP3_HIT | SL_HIT | EXPIRED | IGNORED
    outcome: Optional[str] = Field(default=None) # WIN | LOSS | NEUTRAL
    exit_price: Optional[float] = Field(default=None)
    pips: Optional[float] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    verified_at: Optional[datetime] = Field(default=None)
