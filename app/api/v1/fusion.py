"""Fusion intelligence endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.deps import get_current_verified_user, limiter
from app.core.database import get_session
from sqlmodel import Session
from app.models.user import User
from app.schemas.fusion import (
    FinetuneRequest, FusionRequest, FusionResponse,
    SentimentBlock, LLMAnalysisBlock,
)
from app.services.fusion_service import get_fusion

router = APIRouter()


@router.get("/{symbol}", response_model=FusionResponse)
@limiter.limit("20/minute")
async def fusion_signal(
    request: Request,
    symbol: str,
    db: Session = Depends(get_session),
    include_sentiment: bool = Query(default=True, description="Include FinBERT news sentiment"),
    include_llm: bool = Query(default=False, description="Include Claude LLM analysis (opt-in, uses API credits)"),
    _: User = Depends(get_current_verified_user),
):
    """
    Run LSTM + PatchTST Agreement Algorithm for all configured timeframes.
    Returns Master Fusion Score, verdict, per-timeframe confidence breakdown,
    and optionally FinBERT sentiment and Claude LLM analysis.
    """
    try:
        return get_fusion(
            db,
            symbol.upper(),
            include_sentiment=include_sentiment,
            include_llm=include_llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion analysis failed: {e}")


@router.get("/{symbol}/sentiment", response_model=SentimentBlock)
@limiter.limit("30/minute")
async def symbol_sentiment(
    request: Request,
    symbol: str,
    _: User = Depends(get_current_verified_user),
):
    """
    Standalone FinBERT sentiment analysis for a symbol.
    Faster than the full fusion endpoint — no ML model inference.
    """
    try:
        from intelligence.news_service import get_news_for_symbol
        from intelligence.sentiment_service import get_sentiment

        news_items = get_news_for_symbol(symbol.upper(), limit=15)
        raw = get_sentiment(symbol.upper(), news_items)
        if not raw:
            raise HTTPException(status_code=503, detail="Sentiment analysis unavailable — FinBERT may still be loading.")

        return SentimentBlock(
            overall_sentiment=raw.get("overall_sentiment", "neutral"),
            overall_score=round(raw.get("overall_score", 0.0), 3),
            trading_bias=raw.get("trading_bias", "NEUTRAL"),
            bias_strength=raw.get("bias_strength", "none"),
            positive_count=raw.get("positive_count", 0),
            negative_count=raw.get("negative_count", 0),
            neutral_count=raw.get("neutral_count", 0),
            news_count=raw.get("news_count", len(news_items)),
            top_headlines=[
                {
                    "title": h.get("title", ""),
                    "source": h.get("source", ""),
                    "summary": h.get("summary", ""),
                    "published": h.get("published", ""),
                    "link": h.get("link", ""),
                }
                for h in news_items[:10]
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {e}")


@router.post("/{symbol}/llm-analysis", response_model=LLMAnalysisBlock)
@limiter.limit("5/minute")
async def llm_analysis(
    request: Request,
    symbol: str,
    body: FusionRequest,
    db: Session = Depends(get_session),
    _: User = Depends(get_current_verified_user),
):
    """
    Standalone Claude LLM analysis using the two-phase unbiased prompt.
    Phase 1: Claude forms independent view from price + news + sentiment.
    Phase 2: Claude validates or challenges the ML model predictions.
    Slower (~5–10s) and uses Claude API credits.
    """
    try:
        result = get_fusion(
            db,
            symbol.upper(),
            timeframes=body.timeframes,
            include_sentiment=True,
            include_llm=True,
        )
        if not result.llm_analysis:
            raise HTTPException(status_code=503, detail="LLM analysis unavailable. Check CLAUDE_API_KEY.")
        return result.llm_analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {e}")


@router.post("/analyze", response_model=FusionResponse)
@limiter.limit("10/minute")
async def fusion_analyze(
    request: Request,
    body: FusionRequest,
    db: Session = Depends(get_session),
    _: User = Depends(get_current_verified_user),
):
    """
    POST version of GET /{symbol} for frontend convenience.
    Accepts optional timeframe override and include_sentiment/include_llm flags.
    """
    try:
        return get_fusion(
            db,
            body.symbol.upper(),
            timeframes=body.timeframes,
            include_sentiment=body.include_sentiment,
            include_llm=body.include_llm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion analysis failed: {e}")


@router.post("/finetune")
@limiter.limit("2/hour")
async def trigger_finetune(
    request: Request,
    body: FinetuneRequest,
    _: User = Depends(get_current_verified_user),
):
    """
    Queue a background transfer-learning job.
    Freezes source_model_id encoder and retrains heads on target_symbol.
    """
    from workers.celery_app import celery_app
    task = celery_app.send_task(
        "workers.tasks.finetune.run_finetune",
        kwargs={
            "target_symbol": body.target_symbol,
            "source_model_id": body.source_model_id,
            "epochs": body.epochs,
        },
    )
    return {"task_id": task.id, "status": "queued", "message": f"Fine-tune for {body.target_symbol} started."}
