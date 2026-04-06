"""ML management endpoints — model registry, worker triggers."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_verified_user
from app.models.model_registry import ModelRegistry
from app.models.user import User

router = APIRouter()


@router.get("/registry")
async def list_registry(
    model_type: str = Query(default=None),
    _: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
):
    """List all registered models with their performance stats."""
    query = select(ModelRegistry).where(ModelRegistry.is_active == True)  # noqa: E712
    if model_type:
        query = query.where(ModelRegistry.model_type == model_type)
    models = db.exec(query).all()
    return {"models": models}


@router.post("/backtest/trigger")
async def trigger_backtest(
    symbol: str = Query(...),
    interval: str = Query(...),
    _: User = Depends(get_current_verified_user),
):
    """Queue a backtest job for the specified symbol/interval."""
    from workers.celery_app import celery_app
    task = celery_app.send_task(
        "workers.tasks.backtest.run_backtest",
        kwargs={"symbol": symbol, "interval": interval},
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/predict/trigger")
async def trigger_predictions(
    _: User = Depends(get_current_verified_user),
):
    """Manually trigger the scheduled prediction worker."""
    from workers.tasks.predictions import run_scheduled_predictions
    task = run_scheduled_predictions.delay()
    return {"task_id": task.id, "status": "queued"}
