"""Newsletter endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.deps import get_current_verified_user, limiter
from app.models.user import User
from app.schemas.fusion import NewsletterRequest
from app.config import settings

router = APIRouter()


@router.get("/status")
async def newsletter_status(_: User = Depends(get_current_verified_user)):
    """Check newsletter service configuration and NEWSLETTER_ENABLED flag."""
    return {
        "newsletter_enabled": settings.NEWSLETTER_ENABLED,
        "scheduled_time": "07:00 UTC daily (when NEWSLETTER_ENABLED=true)",
        "manual_trigger": "POST /api/v1/newsletter/trigger (always works)",
        "email_configured": bool(settings.SMTP_USERNAME),
        "smtp_server": settings.SMTP_SERVER,
        "from_address": settings.SMTP_FROM_ADDRESS,
        "default_symbols": ["EURUSD=X", "GBPUSD=X", "GC=F", "BTC-USD"],
        "frontend_url": settings.FRONTEND_URL,
    }


@router.post("/preview")
@limiter.limit("5/minute")
async def preview_newsletter(
    request: Request,
    body: NewsletterRequest,
    _: User = Depends(get_current_verified_user),
):
    """Generate newsletter HTML preview without sending."""
    try:
        from app.services.newsletter_service import generate_newsletter_html
        html, stats = generate_newsletter_html(
            symbols=body.symbols,
            include_llm=body.include_llm,
            period=body.period,
        )
        return {"status": "success", "preview_html": html, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Newsletter generation failed: {e}")


@router.post("/send")
@limiter.limit("3/hour")
async def send_newsletter(
    request: Request,
    body: NewsletterRequest,
    _: User = Depends(get_current_verified_user),
):
    """Generate and send newsletter to specified or configured recipients."""
    try:
        from app.services.newsletter_service import send_newsletter as _send
        result = _send(
            symbols=body.symbols,
            recipients=body.recipients,
            include_llm=body.include_llm,
            period=body.period,
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Newsletter send failed: {e}")


@router.post("/trigger")
async def trigger_newsletter(
    body: NewsletterRequest,
    _: User = Depends(get_current_verified_user),
):
    """
    Queue a newsletter send as a Celery background task.
    Always sends regardless of NEWSLETTER_ENABLED setting (manual override).
    """
    from workers.celery_app import celery_app
    task = celery_app.send_task(
        "workers.tasks.newsletter.send_newsletter_task",
        kwargs={
            "symbols": body.symbols,
            "recipients": body.recipients,
            "include_llm": body.include_llm,
            "period": body.period,
            "force": True,  # manual trigger always sends
        },
    )
    return {"task_id": task.id, "status": "queued", "message": "Newsletter queued. Set NEWSLETTER_ENABLED=true in .env for automatic daily sends."}
