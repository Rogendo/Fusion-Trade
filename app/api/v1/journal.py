"""Trading journal endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.deps import get_current_verified_user
from app.core.database import get_session
from app.models.journal import PredictionJournal
from app.models.user import User
from app.schemas.journal import JournalEntryResponse, JournalListResponse
from app.services.journal_service import JournalService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=JournalListResponse)
async def list_journal(
    symbol: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    svc = JournalService(db)
    entries, total = svc.list(
        user_id=current_user.id,
        symbol=symbol,
        status=status,
        page=page,
        page_size=page_size,
    )
    stats = svc.stats(user_id=current_user.id)
    return JournalListResponse(
        entries=[JournalEntryResponse.model_validate(e) for e in entries],
        stats=stats,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/stats")
async def journal_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    svc = JournalService(db)
    return svc.stats(user_id=current_user.id)


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_entry(
    entry_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    svc = JournalService(db)
    entry = svc.get(entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/verify-now")
async def trigger_verification(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    """
    Manually verify all PENDING journal entries against live market data.
    Runs inline — no Celery broker required.
    """
    # Import only the pure logic function, not the Celery task
    from workers.tasks.verification import _verify_entry

    pending = db.exec(
        select(PredictionJournal).where(PredictionJournal.status == "PENDING")
    ).all()

    checked = len(pending)
    errors = 0
    for entry in pending:
        try:
            _verify_entry(db, entry)
        except Exception as e:
            logger.warning("Verification failed for entry %s: %s", entry.id[:8], e)
            errors += 1

    db.commit()
    logger.info("Manual verification: checked=%d errors=%d", checked, errors)

    return {
        "status": "completed",
        "result": {
            "verified": checked,
            "errors": errors,
        },
    }
