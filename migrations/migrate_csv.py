"""
Migrate predictions_log.csv from the legacy FX project into the SQLite journal.

Run once:
    cd /home/naynek/Desktop/Backup/FX/fusion_trade
    python migrations/migrate_csv.py
"""
from __future__ import annotations

import csv
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a script
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import Session

from app.core.database import engine, init_db
from app.models.journal import PredictionJournal

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CSV_PATH = Path("/home/naynek/Desktop/Backup/FX/FX/predictions_log.csv")

# Map CSV status → journal status
STATUS_MAP = {
    "Pending": "PENDING",
    "Win": "TP1_HIT",
    "Loss": "SL_HIT",
    "Ignored": "IGNORED",
    "Expired": "EXPIRED",
}

OUTCOME_MAP = {
    "Win": "WIN",
    "Loss": "LOSS",
    "Ignored": None,
    "Expired": None,
    "Pending": None,
}


def _parse_float(val: str) -> float | None:
    try:
        return float(val) if val.strip() else None
    except (ValueError, AttributeError):
        return None


def _parse_dt(val: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S+00:00"):
        try:
            return datetime.strptime(val.strip(), fmt).replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            continue
    return datetime.now(timezone.utc)


def migrate():
    if not CSV_PATH.exists():
        logger.error("CSV not found at %s", CSV_PATH)
        sys.exit(1)

    init_db()

    migrated = 0
    skipped = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info("Found %d rows in CSV", len(rows))

    with Session(engine) as db:
        for row in rows:
            try:
                status = STATUS_MAP.get(row.get("Status", "Pending"), "PENDING")
                outcome = OUTCOME_MAP.get(row.get("Status", "Pending"))

                entry = PredictionJournal(
                    symbol=row.get("Symbol", ""),
                    interval=row.get("Interval", ""),
                    signal=row.get("Signal", "HOLD"),
                    lstm_signal=row.get("Signal"),
                    entry_price=_parse_float(row.get("Current Price", "")),
                    predicted_price=_parse_float(row.get("Predicted Price", "")),
                    take_profit_1=_parse_float(row.get("TP1", "") or row.get("Take Profit", "")),
                    take_profit_2=_parse_float(row.get("TP2", "")),
                    take_profit_3=_parse_float(row.get("TP3", "")),
                    stop_loss=_parse_float(row.get("Stop Loss", "")),
                    confidence=_parse_float(row.get("Confidence", "")),
                    status=status,
                    outcome=outcome,
                    created_at=_parse_dt(row.get("Timestamp", "")),
                )
                db.add(entry)
                migrated += 1

            except Exception as e:
                logger.warning("Skipped row: %s — %s", row, e)
                skipped += 1

        db.commit()

    logger.info("Migration complete — migrated: %d, skipped: %d", migrated, skipped)


if __name__ == "__main__":
    migrate()
