"""Request/response schemas for Fusion intelligence endpoints."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class TimeframeSignal(BaseModel):
    # Signal
    lstm: str                                       # BUY | SELL | HOLD
    patchtst: Optional[str] = None                  # BUY | SELL | HOLD | N/A
    agreement: float                                # 0.0 | 0.25 | 0.5 | 1.0

    # LSTM confidence (two distinct values — see intelligence/lstm_service.py)
    lstm_confidence: float                          # magnitude-based: abs_change × 80–100
    lstm_direction_confidence: Optional[float] = None  # LSTM direction head probability
    lstm_direction_accuracy: Optional[float] = None    # historical model accuracy %

    # PatchTST confidence (full softmax distribution)
    patchtst_confidence: Optional[float] = None
    patchtst_prob_up: Optional[float] = None
    patchtst_prob_flat: Optional[float] = None
    patchtst_prob_down: Optional[float] = None

    # Prices
    current_price: float
    predicted_price: Optional[float] = None


class FusionTargets(BaseModel):
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    sl: Optional[float] = None
    atr: Optional[float] = None


class SentimentBlock(BaseModel):
    overall_sentiment: str          # bullish | bearish | neutral
    overall_score: float            # -1.0 to +1.0
    trading_bias: str               # BUY | SELL | NEUTRAL
    bias_strength: str              # strong | moderate | weak | none
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    news_count: int = 0
    top_headlines: List[Dict] = []  # [{title, source}]


class LLMAnalysisBlock(BaseModel):
    action: str                     # BUY | SELL | HOLD | WAIT
    confidence_level: str           # high | medium | low
    independent_bias: str           # Claude's own view BEFORE seeing model predictions
    validates_fusion: bool          # True = Claude agrees with fusion verdict
    divergence_reason: Optional[str] = None  # Why Claude disagrees (if applicable)
    market_structure: str
    news_impact: str
    entry_strategy: str
    key_levels: Dict = {}
    warnings: List[str] = []
    raw_response: str = ""


class FusionResponse(BaseModel):
    symbol: str
    master_fusion_score: float      # 0–100
    verdict: str                    # HIGH CONVICTION BUY | MODERATE SELL | DIVERGENT (HOLD) | HOLD
    logic: Dict                     # primary_lstm, secondary_patchtst, confluence bool
    timeframes: Dict[str, TimeframeSignal]
    targets: FusionTargets
    reasoning: str

    # Optional enrichments (populated based on query params)
    sentiment: Optional[SentimentBlock] = None
    llm_analysis: Optional[LLMAnalysisBlock] = None


class FusionRequest(BaseModel):
    symbol: str
    timeframes: Optional[list] = None
    include_sentiment: bool = True
    include_llm: bool = False


class FinetuneRequest(BaseModel):
    target_symbol: str
    source_model_id: str            # e.g. "GC_F_30m_patchtst"
    epochs: int = 10


class NewsletterRequest(BaseModel):
    symbols: List[str] = ["EURUSD=X", "GBPUSD=X", "GC=F", "BTC-USD"]
    recipients: List[str] = []
    include_llm: bool = False
    period: str = "daily"
