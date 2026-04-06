"""
Fusion intelligence service — Agreement Algorithm + Fusion Score + Sentiment + LLM.

Agreement Algorithm:
  - BUY   only if LSTM == BUY  AND PatchTST == BUY
  - SELL  only if LSTM == SELL AND PatchTST == SELL
  - Otherwise → DIVERGENT (HOLD)

Fusion Score (0–100):
  - Base: 55 (directional) or 30 (HOLD/DIVERGENT)
  - Boosted by weighted confidence of both models per timeframe
  - 4h carries most weight (0.35), 15m least (0.15)
"""
from __future__ import annotations

import logging
from typing import Optional

from app.config import settings
from sqlmodel import Session
from app.services.sentiment_cache_service import SentimentCacheService
from app.schemas.fusion import (
    FusionResponse, FusionTargets, TimeframeSignal,
    SentimentBlock, LLMAnalysisBlock,
)
from intelligence.lstm_service import SignalResult, get_lstm_signal
from intelligence.patchtst_service import get_patchtst_signal

logger = logging.getLogger(__name__)

LSTM_WEIGHT = 0.60
PTST_WEIGHT = 0.40


def _agreement(lstm: str, ptst: Optional[str]) -> float:
    if ptst is None:
        return 0.5
    if lstm == ptst:
        return 1.0
    if "HOLD" in (lstm, ptst):
        return 0.25
    return 0.0


def _compute_fusion_score(
    timeframe_signals: dict[str, tuple],
    verdict: str,
) -> float:
    base = 30.0 if ("HOLD" in verdict or "DIVERGENT" in verdict) else 55.0
    tf_weights = {"15m": 0.15, "30m": 0.20, "1h": 0.30, "4h": 0.35}
    total_weight = 0.0
    weighted_sum = 0.0

    for tf, (lstm, ptst) in timeframe_signals.items():
        w = tf_weights.get(tf, 0.25)
        total_weight += w
        if lstm is None:
            continue
        lstm_contrib = lstm.confidence * LSTM_WEIGHT
        ptst_contrib = (ptst.confidence if ptst else 0.0) * PTST_WEIGHT
        agree = _agreement(lstm.signal, ptst.signal if ptst else None)
        weighted_sum += w * (lstm_contrib + ptst_contrib) * agree

    if total_weight:
        score = base + (weighted_sum / total_weight) * 50
    else:
        score = base

    return min(max(round(score, 1), 0.0), 100.0)


def _build_verdict(dominant: str, score: float) -> str:
    if dominant == "HOLD":
        return "HOLD"
    if dominant == "DIVERGENT":
        return "DIVERGENT (HOLD)"
    conviction = "HIGH CONVICTION" if score >= 70 else "MODERATE" if score >= 50 else "WEAK"
    return f"{conviction} {dominant}"


def _build_reasoning(verdict: str, timeframe_signals: dict, dominant: str) -> str:
    lines = []
    if "DIVERGENT" in verdict:
        lines.append("LSTM and PatchTST signals are in conflict across timeframes.")
    elif "HOLD" in verdict:
        lines.append("No clear directional bias across timeframes.")
    else:
        lines.append(f"LSTM (Primary) and PatchTST confirm {dominant} across key timeframes.")

    agreements = [
        tf for tf, (l, p) in timeframe_signals.items()
        if l and p and l.signal == p.signal and l.signal != "HOLD"
    ]
    if agreements:
        lines.append(f"Full confluence on: {', '.join(agreements)}.")
    return " ".join(lines)


def get_fusion(
    db: Session,
    symbol: str,
    timeframes: Optional[list] = None,
    include_sentiment: bool = True,
    include_llm: bool = False,
) -> FusionResponse:
    """Run LSTM + PatchTST for all timeframes and produce the Fusion verdict."""
    tfs = timeframes or settings.FUSION_TIMEFRAMES
    timeframe_results: dict[str, tuple] = {}
    timeframe_schema: dict[str, TimeframeSignal] = {}

    for tf in tfs:
        lstm = get_lstm_signal(symbol, tf)
        ptst = get_patchtst_signal(symbol, tf)
        timeframe_results[tf] = (lstm, ptst)

        if lstm is None:
            logger.warning("LSTM returned None for %s %s — skipping", symbol, tf)
            continue

        ptst_signal = ptst.signal if ptst else None
        agree = _agreement(lstm.signal, ptst_signal)

        timeframe_schema[tf] = TimeframeSignal(
            lstm=lstm.signal,
            patchtst=ptst_signal or "N/A",
            agreement=agree,
            lstm_confidence=round(lstm.confidence, 4),
            lstm_direction_confidence=round(lstm.direction_confidence, 4) if lstm.direction_confidence is not None else None,
            lstm_direction_accuracy=round(lstm.direction_accuracy, 2) if lstm.direction_accuracy else None,
            patchtst_confidence=round(ptst.confidence, 4) if ptst else None,
            patchtst_prob_up=ptst.prob_up if ptst else None,
            patchtst_prob_flat=ptst.prob_flat if ptst else None,
            patchtst_prob_down=ptst.prob_down if ptst else None,
            current_price=lstm.current_price,
            predicted_price=lstm.predicted_price,
        )

    # ── Agreement Algorithm ───────────────────────────────────────────────────
    tf_weights = {"15m": 1, "30m": 2, "1h": 3, "4h": 4}
    buy_score = sell_score = hold_score = 0.0

    for tf, (lstm, ptst) in timeframe_results.items():
        if lstm is None:
            continue
        w = tf_weights.get(tf, 1)
        if ptst is not None:
            if lstm.signal == "BUY" and ptst.signal == "BUY":
                buy_score += w
            elif lstm.signal == "SELL" and ptst.signal == "SELL":
                sell_score += w
            else:
                hold_score += w
        else:
            if lstm.signal == "BUY":
                buy_score += w * 0.5
            elif lstm.signal == "SELL":
                sell_score += w * 0.5
            else:
                hold_score += w

    total = buy_score + sell_score + hold_score
    if total == 0:
        dominant = "HOLD"
    elif buy_score >= sell_score and buy_score > hold_score:
        dominant = "BUY"
    elif sell_score > buy_score and sell_score > hold_score:
        dominant = "SELL"
    else:
        dominant = "DIVERGENT"

    score = _compute_fusion_score(timeframe_results, dominant)
    verdict = _build_verdict(dominant, score)
    reasoning = _build_reasoning(verdict, timeframe_results, dominant)

    # ── Targets from highest-weight available timeframe ───────────────────────
    best_lstm = None
    for tf in ["4h", "1h", "30m", "15m"]:
        lstm, _ = timeframe_results.get(tf, (None, None))
        if lstm and lstm.signal != "HOLD":
            best_lstm = lstm
            break

    targets = FusionTargets(
        tp1=best_lstm.take_profit if best_lstm else None,
        sl=best_lstm.stop_loss if best_lstm else None,
        atr=best_lstm.atr if best_lstm else None,
    )

    # ── News (always fetch when sentiment or LLM is needed) ───────────────────
    sentiment_block: Optional[SentimentBlock] = None
    news_items: list[dict] = []

    if include_sentiment or include_llm:
        try:
            from intelligence.news_service import get_news_for_symbol
            news_items = get_news_for_symbol(symbol, limit=15)
        except Exception as e:
            logger.warning("News fetch failed for %s: %s", symbol, e)

    # ── Sentiment ─────────────────────────────────────────────────────────────
    if include_sentiment:
        try:
            cache_svc = SentimentCacheService(db)
            raw_sentiment = cache_svc.get_cached_sentiment(symbol)
            if not raw_sentiment:
                raw_sentiment = cache_svc.update_cache(symbol)

            if raw_sentiment:
                sentiment_block = SentimentBlock(
                    overall_sentiment=raw_sentiment.get("overall_sentiment", "neutral"),
                    overall_score=round(raw_sentiment.get("overall_score", 0.0), 3),
                    trading_bias=raw_sentiment.get("trading_bias", "NEUTRAL"),
                    bias_strength=raw_sentiment.get("bias_strength", "none"),
                    positive_count=raw_sentiment.get("positive_count", 0),
                    negative_count=raw_sentiment.get("negative_count", 0),
                    neutral_count=raw_sentiment.get("neutral_count", 0),
                    news_count=raw_sentiment.get("news_count", len(news_items)),
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
        except Exception as e:
            logger.warning("Sentiment pipeline failed for %s: %s", symbol, e)

    # ── LLM Analysis ──────────────────────────────────────────────────────────
    llm_block: Optional[LLMAnalysisBlock] = None

    if include_llm:
        try:
            from intelligence.llm_service import FusionLLMInput, get_llm_analysis

            # Build per-TF signal dicts for the LLM prompt
            lstm_signals = {}
            ptst_signals = {}
            best_indicators = {}

            for tf, (lstm, ptst) in timeframe_results.items():
                if lstm:
                    lstm_signals[tf] = {
                        "signal": lstm.signal,
                        "confidence": round(lstm.confidence, 3),
                        "direction_confidence": round(lstm.direction_confidence, 3),
                        "predicted_price": lstm.predicted_price,
                    }
                    if not best_indicators and lstm.rsi is not None:
                        best_indicators = {
                            "rsi": lstm.rsi,
                            "macd": lstm.macd,
                            "atr": lstm.atr,
                            "support": lstm.support,
                            "resistance": lstm.resistance,
                            "trend": lstm.trend,
                        }
                if ptst:
                    ptst_signals[tf] = {
                        "signal": ptst.signal,
                        "prob_up": ptst.prob_up,
                        "prob_flat": ptst.prob_flat,
                        "prob_down": ptst.prob_down,
                    }

            # Use the highest-weight LSTM for OHLCV data
            best_ohlcv = []
            for tf in ["4h", "1h", "30m", "15m"]:
                lstm, _ = timeframe_results.get(tf, (None, None))
                if lstm and lstm.ohlcv:
                    best_ohlcv = lstm.ohlcv
                    break

            # Fallback: fetch OHLCV directly if LSTM didn't provide chart data
            if not best_ohlcv:
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="5d", interval="1h")
                    if not hist.empty:
                        best_ohlcv = [
                            {
                                "time": str(idx),
                                "open": round(float(row.Open), 5),
                                "high": round(float(row.High), 5),
                                "low": round(float(row.Low), 5),
                                "close": round(float(row.Close), 5),
                                "volume": int(row.Volume),
                            }
                            for idx, row in hist.tail(30).iterrows()
                        ]
                except Exception as e:
                    logger.warning("OHLCV fallback fetch failed for %s: %s", symbol, e)

            llm_input = FusionLLMInput(
                symbol=symbol,
                interval="4h",
                ohlcv=best_ohlcv,
                technical_indicators=best_indicators,
                news_headlines=news_items[:10],
                sentiment=vars(sentiment_block) if sentiment_block else None,
                lstm_signals=lstm_signals,
                patchtst_signals=ptst_signals,
                fusion_verdict=verdict,
                fusion_score=score,
                targets={
                    "tp1": targets.tp1,
                    "sl": targets.sl,
                    "atr": targets.atr,
                },
            )

            llm_result = get_llm_analysis(llm_input)
            if llm_result:
                llm_block = LLMAnalysisBlock(
                    action=llm_result.action,
                    confidence_level=llm_result.confidence_level,
                    independent_bias=llm_result.independent_bias,
                    validates_fusion=llm_result.validates_fusion,
                    divergence_reason=llm_result.divergence_reason,
                    market_structure=llm_result.market_structure,
                    news_impact=llm_result.news_impact,
                    entry_strategy=llm_result.entry_strategy,
                    key_levels=llm_result.key_levels,
                    warnings=llm_result.warnings,
                    raw_response=llm_result.raw_response,
                )
        except Exception as e:
            logger.error("LLM analysis failed for %s: %s", symbol, e)

    return FusionResponse(
        symbol=symbol,
        master_fusion_score=score,
        verdict=verdict,
        logic={
            "primary_lstm": dominant if dominant != "DIVERGENT" else "CONFLICT",
            "secondary_patchtst": dominant if dominant not in ("HOLD", "DIVERGENT") else "CONFLICT",
            "confluence": dominant not in ("HOLD", "DIVERGENT"),
        },
        timeframes=timeframe_schema,
        targets=targets,
        reasoning=reasoning,
        sentiment=sentiment_block,
        llm_analysis=llm_block,
    )
