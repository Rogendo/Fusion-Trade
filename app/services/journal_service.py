"""Prediction journal CRUD and statistics."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, and_, func, select

from app.models.journal import PredictionJournal
from app.schemas.journal import JournalStatsResponse

logger = logging.getLogger(__name__)


class JournalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, entry: PredictionJournal) -> PredictionJournal:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get(self, entry_id: str) -> Optional[PredictionJournal]:
        return self.db.get(PredictionJournal, entry_id)

    def list(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PredictionJournal], int]:
        query = select(PredictionJournal)
        conditions = []
        if user_id:
            conditions.append(PredictionJournal.user_id == user_id)
        if symbol:
            conditions.append(PredictionJournal.symbol == symbol)
        if status:
            conditions.append(PredictionJournal.status == status)
        if conditions:
            query = query.where(and_(*conditions))

        total = self.db.exec(
            select(func.count()).select_from(query.subquery())
        ).one()

        entries = self.db.exec(
            query.order_by(PredictionJournal.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(entries), total

    def stats(self, user_id: Optional[str] = None) -> JournalStatsResponse:
        query = select(PredictionJournal)
        if user_id:
            query = query.where(PredictionJournal.user_id == user_id)
        entries = self.db.exec(query).all()

        wins = [e for e in entries if e.outcome == "WIN"]
        losses = [e for e in entries if e.outcome == "LOSS"]
        pending = [e for e in entries if e.status == "PENDING"]

        total_trades = len(wins) + len(losses)
        win_rate = len(wins) / total_trades if total_trades else 0.0

        gross_profit = sum(e.pips or 0 for e in wins)
        gross_loss = abs(sum(e.pips or 0 for e in losses))
        profit_factor = gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0)

        total_pips = sum(e.pips or 0 for e in entries if e.pips is not None)

        # Simple drawdown: running equity curve from pips
        running = 0.0
        peak = 0.0
        max_dd = 0.0
        for e in sorted(entries, key=lambda x: x.created_at):
            if e.pips is not None:
                running += e.pips
                if running > peak:
                    peak = running
                dd = peak - running
                if dd > max_dd:
                    max_dd = dd

        return JournalStatsResponse(
            total_trades=total_trades,
            wins=len(wins),
            losses=len(losses),
            pending=len(pending),
            win_rate=round(win_rate * 100, 2),
            profit_factor=round(profit_factor, 2),
            total_pips=round(total_pips, 2),
            max_drawdown=round(max_dd, 2),
        )

    def update_status(
        self,
        entry_id: str,
        status: str,
        outcome: Optional[str] = None,
        exit_price: Optional[float] = None,
        pips: Optional[float] = None,
    ) -> Optional[PredictionJournal]:
        entry = self.db.get(PredictionJournal, entry_id)
        if not entry:
            return None
        entry.status = status
        if outcome:
            entry.outcome = outcome
        if exit_price is not None:
            entry.exit_price = exit_price
        if pips is not None:
            entry.pips = pips
        entry.verified_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(entry)
        return entry
