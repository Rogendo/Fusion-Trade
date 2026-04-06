"""Celery application — broker: Redis, backend: Redis."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the fusion_trade package root is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "fusion_trade",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.tasks.verification",
        "workers.tasks.predictions",
        "workers.tasks.newsletter",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_redirect_stdouts_level="INFO",
)

# ── Beat schedule ────────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Verify pending journal entries every 15 minutes
    "verify-pending-journals": {
        "task": "workers.tasks.verification.verify_pending_journals",
        "schedule": 60 * 15,  # every 15 minutes
    },
    # Generate scheduled predictions at 06:00 UTC daily
    "daily-predictions": {
        "task": "workers.tasks.predictions.run_scheduled_predictions",
        "schedule": crontab(hour=6, minute=0),
    },
    # Send daily newsletter at 07:00 UTC
    "daily-newsletter": {
        "task": "workers.tasks.newsletter.send_newsletter_task",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"period": "daily", "include_llm": False},
    },
}

if __name__ == "__main__":
    celery_app.start()
