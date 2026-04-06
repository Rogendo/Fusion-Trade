"""Schemas for trading journal endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JournalEntryResponse(BaseModel):
    id: str
    symbol: str
    interval: str
    signal: str
    lstm_signal: Optional[str]
    patchtst_signal: Optional[str]
    fusion_score: Optional[float]
    entry_price: Optional[float]
    take_profit_1: Optional[float]
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    stop_loss: Optional[float]
    confidence: Optional[float]
    status: str
    outcome: Optional[str]
    exit_price: Optional[float]
    pips: Optional[float]
    created_at: datetime
    verified_at: Optional[datetime]

    model_config = {"from_attributes": True}


class JournalStatsResponse(BaseModel):
    total_trades: int
    wins: int
    losses: int
    pending: int
    win_rate: float
    profit_factor: float
    total_pips: float
    max_drawdown: float


class JournalListResponse(BaseModel):
    entries: list[JournalEntryResponse]
    stats: JournalStatsResponse
    page: int
    page_size: int
    total: int
