"""
Claude LLM analysis service — two-phase unbiased prompt design.

Phase 1: Claude sees ONLY price data, technicals, news, sentiment.
         Forms an INDEPENDENT view before seeing any ML predictions.

Phase 2: ML model predictions revealed. Claude explicitly validates
         or challenges the fusion verdict based on its own analysis.

This prevents the LLM from simply rubber-stamping the trained models.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an independent institutional forex and commodities analyst.
You are rigorous, objective, and willing to contradict AI model outputs when data does not support them.

You will be given:
1. Raw OHLCV price data (candlestick history)
2. Technical indicators (RSI, MACD, ATR, support/resistance)
3. Recent market news headlines
4. FinBERT news sentiment analysis

Your task has TWO phases:
- Phase 1: Form your OWN independent directional view from the raw data and news.
  Do NOT be influenced by any AI model predictions yet — they will be revealed later.
- Phase 2: Review the AI model predictions, then VALIDATE or CHALLENGE them.
  Explicitly state whether the models agree with your independent view, and why.

Rules:
- Never guarantee profits. Always quantify risk.
- Be concise. Use structured sections with clear headers.
- If data is insufficient, say so rather than guessing.
- Prioritise risk management over potential upside.
"""


@dataclass
class FusionLLMInput:
    symbol: str
    interval: str                          # Primary timeframe (e.g. "4h")
    ohlcv: list[dict]                      # Last 30 candles {time, open, high, low, close, volume}
    technical_indicators: dict             # rsi, macd, atr, support, resistance, trend
    news_headlines: list[dict]             # {title, source, published}
    sentiment: Optional[dict]             # FinBERT result or None
    # ML model context (revealed in Phase 2)
    lstm_signals: dict                     # per-TF {signal, confidence, direction_confidence, predicted_price}
    patchtst_signals: dict                 # per-TF {signal, prob_up, prob_flat, prob_down}
    fusion_verdict: str                    # HIGH CONVICTION BUY / SELL / DIVERGENT (HOLD)
    fusion_score: float                    # 0–100
    targets: dict                          # tp1, sl, atr


@dataclass
class LLMAnalysis:
    action: str                            # BUY | SELL | HOLD | WAIT
    confidence_level: str                  # high | medium | low
    independent_bias: str                  # Claude's own bias BEFORE seeing models (Bullish/Bearish/Neutral)
    validates_fusion: bool                 # True if Claude agrees with fusion verdict
    divergence_reason: Optional[str]       # Why Claude disagrees (if applicable)
    market_structure: str                  # Price action reading
    news_impact: str                       # How news shapes the view
    entry_strategy: str
    key_levels: dict                       # {entry, stop_loss, tp1, tp2}
    warnings: list[str]                    # Top 3 risk warnings
    raw_response: str                      # Full Claude response


def _build_ohlcv_table(ohlcv: list[dict]) -> str:
    if not ohlcv:
        return "No price data available."
    lines = ["Time                | Open      | High      | Low       | Close     | Volume"]
    lines.append("-" * 80)
    for c in ohlcv[-30:]:
        t = str(c.get("time", c.get("x", "")))[:19]
        o = f"{c.get('open', c.get('o', 0)):.5f}"
        h = f"{c.get('high', c.get('h', 0)):.5f}"
        l = f"{c.get('low',  c.get('l', 0)):.5f}"
        cl = f"{c.get('close',c.get('c', 0)):.5f}"
        v = str(c.get("volume", c.get("v", 0)))
        lines.append(f"{t:<20}| {o:<10}| {h:<10}| {l:<10}| {cl:<10}| {v}")
    return "\n".join(lines)


def _build_prompt(inp: FusionLLMInput) -> str:
    ti = inp.technical_indicators

    # ── Sentiment block ───────────────────────────────────────────────────────
    if inp.sentiment:
        s = inp.sentiment
        sentiment_block = (
            f"Overall: **{s.get('overall_sentiment','N/A').upper()}** "
            f"(score: {s.get('overall_score', 0):.2f} | range -1 bearish to +1 bullish)\n"
            f"Trading Bias: {s.get('trading_bias','N/A')} ({s.get('bias_strength','N/A')})\n"
            f"Positive: {s.get('positive_count',0)} | Negative: {s.get('negative_count',0)} "
            f"| Neutral: {s.get('neutral_count',0)} headlines"
        )
    else:
        sentiment_block = "Sentiment data unavailable."

    # ── News headlines ────────────────────────────────────────────────────────
    def _fmt_headline(h: dict) -> str:
        line = f"- [{h.get('source', '?')}] {h.get('title', '')}"
        summary = (h.get("summary") or "").strip()
        if summary:
            line += f"\n  → {summary[:200]}"
        pub = (h.get("published") or "")[:16]
        if pub:
            line += f"  ({pub})"
        return line

    headlines = "\n".join(
        _fmt_headline(h) for h in inp.news_headlines[:10]
    ) or "No recent news available."

    # ── LSTM signals table ────────────────────────────────────────────────────
    lstm_rows = []
    for tf, sig in inp.lstm_signals.items():
        lstm_rows.append(
            f"  {tf:>4} | {sig.get('signal','?'):>5} | "
            f"mag_conf={sig.get('confidence',0):.2f} | "
            f"dir_conf={sig.get('direction_confidence',0):.2f} | "
            f"predicted={sig.get('predicted_price',0):.5f}"
        )
    lstm_table = "\n".join(lstm_rows) or "  No LSTM signals available."

    # ── PatchTST signals table ────────────────────────────────────────────────
    ptst_rows = []
    for tf, sig in inp.patchtst_signals.items():
        ptst_rows.append(
            f"  {tf:>4} | {sig.get('signal','?'):>5} | "
            f"↑ UP={sig.get('prob_up',0):.2f} | "
            f"→ FLAT={sig.get('prob_flat',0):.2f} | "
            f"↓ DOWN={sig.get('prob_down',0):.2f}"
        )
    ptst_table = "\n".join(ptst_rows) or "  PatchTST models not yet trained for this pair."

    prompt = f"""\
# TRADING ANALYSIS — {inp.symbol} ({inp.interval})

---

## PART 1: RAW MARKET DATA
*(Form your independent view from this data only)*

### Price Action — Last 30 Candles
```
{_build_ohlcv_table(inp.ohlcv)}
```

### Technical Indicators
- RSI (14):      {ti.get('rsi', 'N/A')}
- MACD:          {ti.get('macd', 'N/A')}
- ATR (14):      {ti.get('atr', 'N/A')}
- Support:       {ti.get('support', 'N/A')}
- Resistance:    {ti.get('resistance', 'N/A')}
- Trend:         {ti.get('trend', 'N/A')}

### Latest Market News
{headlines}

### FinBERT News Sentiment
{sentiment_block}

---

## YOUR TASK — PHASE 1: INDEPENDENT ANALYSIS

Based **only** on the price data, technical indicators, news, and sentiment above,
provide your independent view for **{inp.symbol}**.
Do NOT mention AI model predictions yet.

Please answer:
**A) Market Structure:** What is the current trend, key support/resistance, and any notable patterns?
**B) News & Sentiment View:** How does the news and FinBERT sentiment shape the picture?
**C) Independent Bias:** Bullish / Bearish / Neutral — and why?
**D) Key Risks:** What are the top risks to any directional trade right now?

---

## PART 2: AI MODEL PREDICTIONS (Revealed)
*(Now compare these against your independent analysis)*

### LSTM Model (Primary — LSTM trained on historical FX data)
```
  TF  | Signal | Mag.Conf | Dir.Conf | Predicted Price
{lstm_table}
```
*(Mag.Conf = magnitude confidence based on predicted price change size)*
*(Dir.Conf = LSTM direction head classification probability)*

### PatchTST Model (Transformer — Channel-independent attention)
```
  TF  | Signal |  ↑ UP prob  |  → FLAT prob  |  ↓ DOWN prob
{ptst_table}
```

### Fusion Verdict: **{inp.fusion_verdict}** (Score: {inp.fusion_score:.0f}/100)
Targets: TP1={inp.targets.get('tp1', 'N/A')} | SL={inp.targets.get('sl', 'N/A')} | ATR={inp.targets.get('atr', 'N/A')}

---

## YOUR TASK — PHASE 2: VALIDATE OR CHALLENGE

**E) Alignment Check:** Do the ML models ALIGN or CONTRADICT your independent Phase 1 analysis? Be explicit.
**F) Trust Assessment:** If there is contradiction — which do you trust more and why?
**G) Final Recommendation:** BUY | SELL | HOLD | WAIT
**H) Confidence Level:** High | Medium | Low
**I) Entry Strategy:** Market or limit? What conditions should be met first?
**J) Key Price Levels:** Entry, Stop Loss, TP1, TP2
**K) Top 3 Warnings:** What could make this trade fail?
"""
    return prompt


def _parse_response(raw: str, inp: FusionLLMInput) -> LLMAnalysis:
    """
    Parse Claude's structured response into LLMAnalysis.
    Falls back to safe defaults if parsing fails.
    """
    raw_upper = raw.upper()

    # Extract final action
    action = "HOLD"
    for keyword in ["WAIT", "BUY", "SELL", "HOLD"]:
        if keyword in raw_upper:
            action = keyword
            break

    # Extract confidence level
    confidence_level = "medium"
    if "HIGH CONFIDENCE" in raw_upper or "HIGH | " in raw_upper or "**HIGH**" in raw_upper:
        confidence_level = "high"
    elif "LOW CONFIDENCE" in raw_upper or "LOW |" in raw_upper or "**LOW**" in raw_upper:
        confidence_level = "low"

    # Extract independent bias from Phase 1
    independent_bias = "Neutral"
    for bias in ["Bullish", "Bearish", "Neutral"]:
        if bias.upper() in raw_upper:
            independent_bias = bias
            break

    # Check if Claude validates the fusion verdict
    fusion_action = inp.fusion_verdict.split()[-1] if inp.fusion_verdict else "HOLD"
    validates_fusion = (action == fusion_action) or (
        action in ("BUY", "SELL") and fusion_action in action
    )
    divergence_reason = None
    if not validates_fusion:
        # Try to extract the contradiction reason from Phase 2
        if "contradict" in raw.lower() or "disagree" in raw.lower() or "conflict" in raw.lower():
            divergence_reason = "Model predictions contradict independent price/news analysis."
        else:
            divergence_reason = f"Claude recommends {action} while Fusion says {fusion_action}."

    # Extract warnings — look for bullet points or numbered list near "Warning"
    warnings: list[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and any(
            kw in line.lower() for kw in ["warning", "risk", "caution", "watch out", "danger"]
        ):
            cleaned = line.lstrip("*-•123456789. ").strip()
            if cleaned and len(cleaned) > 10:
                warnings.append(cleaned[:200])
        if len(warnings) >= 3:
            break

    return LLMAnalysis(
        action=action,
        confidence_level=confidence_level,
        independent_bias=independent_bias,
        validates_fusion=validates_fusion,
        divergence_reason=divergence_reason,
        market_structure=_extract_section(raw, ["Market Structure", "A)", "trend"]),
        news_impact=_extract_section(raw, ["News", "Sentiment", "B)"]),
        entry_strategy=_extract_section(raw, ["Entry Strategy", "I)", "entry"]),
        key_levels={
            "tp1": inp.targets.get("tp1"),
            "sl": inp.targets.get("sl"),
        },
        warnings=warnings or ["Review position sizing", "Monitor news flow", "Respect stop loss"],
        raw_response=raw,
    )


def _extract_section(text: str, keywords: list[str]) -> str:
    """Extract a short excerpt near one of the keywords."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if any(kw.lower() in line.lower() for kw in keywords):
            excerpt = " ".join(lines[i : i + 3]).strip()
            return excerpt[:500] if excerpt else "See full analysis."
    return "See full analysis."


def get_llm_analysis(inp: FusionLLMInput) -> Optional[LLMAnalysis]:
    """
    Run Claude analysis with the two-phase unbiased prompt.
    Returns None if Claude API is unavailable.
    """
    from app.config import settings

    if not settings.CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY not set — LLM analysis skipped")
        return None

    try:
        import anthropic  # type: ignore[import]

        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        prompt = _build_prompt(inp)

        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text
        return _parse_response(raw_text, inp)

    except Exception as e:
        logger.error("Claude API call failed: %s", e)
        return None
