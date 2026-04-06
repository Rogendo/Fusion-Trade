"""Newsletter background task — called by Celery Beat for scheduled sends."""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="workers.tasks.newsletter.send_newsletter_task", bind=True, max_retries=2)
def send_newsletter_task(
    self,
    symbols: list = None,
    recipients: list = None,
    include_llm: bool = False,
    period: str = "daily",
    force: bool = False,
):
    """
    Send the FusionTrade newsletter.

    Called by Celery Beat (scheduled) or manually via POST /api/v1/newsletter/trigger.

    - When called by Beat, it checks NEWSLETTER_ENABLED env var. If False, it
      skips silently (Beat schedule is always registered but the task is a no-op).
    - When called manually (force=True), it always sends regardless of the flag.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.config import settings
    from app.services.newsletter_service import send_newsletter, DEFAULT_SYMBOLS

    if not force and not settings.NEWSLETTER_ENABLED:
        logger.info("Newsletter skipped: NEWSLETTER_ENABLED=false. "
                    "Set NEWSLETTER_ENABLED=true in .env or use the manual trigger endpoint.")
        return {"status": "skipped", "reason": "NEWSLETTER_ENABLED=false"}

    result = send_newsletter(
        symbols=symbols or DEFAULT_SYMBOLS,
        recipients=recipients or [],
        include_llm=include_llm,
        period=period,
    )
    logger.info("Newsletter task complete: %s", result)
    return result
