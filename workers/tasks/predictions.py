"""
Scheduled prediction worker — generates LSTM predictions for configured symbols
and logs them to the journal.
"""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GC=F", "BTC-USD"]
DEFAULT_INTERVALS = ["1h", "4h"]


@shared_task(name="workers.tasks.predictions.run_scheduled_predictions", bind=True, max_retries=2)
def run_scheduled_predictions(self, symbols: list = None, intervals: list = None):
    """
    Generate predictions for all symbols × intervals and write to journal.
    Called by Celery Beat at 06:00 UTC daily.
    """
    from app.config import settings
    from app.core.database import engine
    from app.models.journal import PredictionJournal
    from intelligence.lstm_service import get_lstm_signal
    from intelligence.patchtst_service import get_patchtst_signal
    from sqlmodel import Session
    import sys
    from pathlib import Path

    # Ensure FX project is importable
    fx_path = Path(settings.FX_PROJECT_PATH)
    if str(fx_path) not in sys.path:
        sys.path.insert(0, str(fx_path))

    target_symbols = symbols or DEFAULT_SYMBOLS
    target_intervals = intervals or DEFAULT_INTERVALS

    results = []

    with Session(engine) as db:
        for symbol in target_symbols:
            for interval in target_intervals:
                try:
                    lstm = get_lstm_signal(symbol, interval)
                    ptst = get_patchtst_signal(symbol, interval)

                    if lstm is None:
                        continue

                    # Determine fusion signal
                    if ptst and lstm.signal == ptst.signal and lstm.signal != "HOLD":
                        signal = lstm.signal
                        fusion_score = round(
                            (lstm.confidence * 0.6 + ptst.confidence * 0.4) * 100, 1
                        )
                    elif ptst is None:
                        signal = lstm.signal
                        fusion_score = round(lstm.confidence * 50, 1)
                    else:
                        signal = "DIVERGENT"
                        fusion_score = 20.0

                    entry = PredictionJournal(
                        symbol=symbol,
                        interval=interval,
                        signal=signal,
                        lstm_signal=lstm.signal,
                        patchtst_signal=ptst.signal if ptst else None,
                        fusion_score=fusion_score,
                        entry_price=lstm.current_price,
                        predicted_price=lstm.predicted_price,
                        take_profit_1=lstm.take_profit,
                        stop_loss=lstm.stop_loss,
                        confidence=lstm.confidence,
                        status="PENDING" if signal not in ("HOLD", "DIVERGENT") else "IGNORED",
                    )
                    db.add(entry)
                    results.append(f"{symbol}/{interval}={signal}")
                    logger.info("Logged prediction: %s %s → %s", symbol, interval, signal)

                except Exception as e:
                    logger.error("Prediction failed for %s %s: %s", symbol, interval, e)

        db.commit()

    logger.info("Scheduled predictions complete: %d entries", len(results))
    return {"entries": results}
