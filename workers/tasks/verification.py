"""
Verification worker — checks PENDING journal entries against live market data.

Logic per entry:
  - Fetch OHLCV for the symbol/interval since entry creation.
  - Walk candle-by-candle in chronological order.
  - First hit wins: TP1 → TP1_HIT (WIN), SL → SL_HIT (LOSS).
  - Entries older than 7 days without a hit → EXPIRED.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import yfinance as yf
from celery import shared_task
from sqlmodel import Session, select

from app.core.database import engine
from app.models.journal import PredictionJournal

logger = logging.getLogger(__name__)

EXPIRY_DAYS = 7


@shared_task(name="workers.tasks.verification.verify_pending_journals", bind=True, max_retries=3)
def verify_pending_journals(self):
    """Check all PENDING journal entries and update their status."""
    with Session(engine) as db:
        pending = db.exec(
            select(PredictionJournal).where(
                PredictionJournal.status == "PENDING"
            )
        ).all()

        logger.info("Verification worker: checking %d pending entries", len(pending))

        for entry in pending:
            try:
                _verify_entry(db, entry)
            except Exception as e:
                logger.error("Error verifying entry %s: %s", entry.id, e)

        db.commit()
    return {"verified": len(pending)}


def _verify_entry(db: Session, entry: PredictionJournal) -> None:
    now = datetime.now(timezone.utc)

    # Expire stale entries
    age = now - entry.created_at.replace(tzinfo=timezone.utc) if entry.created_at.tzinfo is None else now - entry.created_at
    if age > timedelta(days=EXPIRY_DAYS):
        entry.status = "EXPIRED"
        entry.verified_at = now
        logger.info("Expired: %s %s %s", entry.symbol, entry.interval, entry.id[:8])
        return

    # Skip entries without TP/SL
    if not entry.take_profit_1 and not entry.stop_loss:
        return
    if not entry.entry_price:
        return

    # Fetch OHLCV since entry creation
    since = entry.created_at.strftime("%Y-%m-%d") if entry.created_at else None
    try:
        ticker = yf.Ticker(entry.symbol)
        period_map = {
            "5m": "5d", "15m": "60d", "30m": "60d",
            "1h": "3mo", "4h": "6mo",
        }
        period = period_map.get(entry.interval, "1mo")
        df = ticker.history(period=period, interval=entry.interval)
    except Exception as e:
        logger.warning("yfinance fetch failed for %s: %s", entry.symbol, e)
        return

    if df.empty:
        return

    # Filter to candles after entry time
    if entry.created_at:
        entry_ts = entry.created_at
        if entry_ts.tzinfo is None:
            entry_ts = entry_ts.replace(tzinfo=timezone.utc)
        df = df[df.index > entry_ts]

    if df.empty:
        return

    is_long = entry.signal in ("BUY", "STRONG BUY")
    tp1 = entry.take_profit_1
    sl = entry.stop_loss

    for ts, row in df.iterrows():
        high = row["High"]
        low = row["Low"]

        if is_long:
            if sl and low <= sl:
                _mark(entry, "SL_HIT", "LOSS", float(sl), now, entry.entry_price)
                return
            if tp1 and high >= tp1:
                _mark(entry, "TP1_HIT", "WIN", float(tp1), now, entry.entry_price)
                return
        else:
            if sl and high >= sl:
                _mark(entry, "SL_HIT", "LOSS", float(sl), now, entry.entry_price)
                return
            if tp1 and low <= tp1:
                _mark(entry, "TP1_HIT", "WIN", float(tp1), now, entry.entry_price)
                return


def _mark(
    entry: PredictionJournal,
    status: str,
    outcome: str,
    exit_price: float,
    now: datetime,
    entry_price: float,
) -> None:
    pip_multiplier = 10000 if "JPY" not in entry.symbol else 100
    raw_diff = exit_price - entry_price
    if entry.signal in ("SELL", "STRONG SELL"):
        raw_diff = -raw_diff
    pips = round(raw_diff * pip_multiplier, 1)

    entry.status = status
    entry.outcome = outcome
    entry.exit_price = exit_price
    entry.pips = pips
    entry.verified_at = now
    logger.info(
        "Journal %s → %s %s | pips=%.1f",
        entry.id[:8], status, outcome, pips
    )
