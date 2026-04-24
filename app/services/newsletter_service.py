"""
Fusion newsletter service — generates and sends HTML email summaries.

Content per symbol:
  - Fusion verdict badge + score
  - Per-timeframe LSTM vs PatchTST confluence grid
  - FinBERT sentiment bar
  - Claude LLM synopsis paragraph (if include_llm=True)
  - TP1/SL levels
  - Top 3 news headlines
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import settings
from app.core.database import engine
from app.services.email_service import email_service
from app.services.fusion_service import get_fusion
from sqlmodel import Session

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["EURUSD=X", "GBPUSD=X", "GC=F", "BTC-USD"]


def _verdict_color(verdict: str) -> str:
    v = verdict.upper()
    if "BUY" in v:
        return "#00ff88"
    if "SELL" in v:
        return "#ff4444"
    return "#ffaa00"


def _signal_badge(signal: str) -> str:
    color = {"BUY": "#00ff88", "SELL": "#ff4444", "HOLD": "#888888", "N/A": "#555555"}.get(signal.upper(), "#888888")
    return f'<span style="background:{color};color:#000;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold;">{signal}</span>'


def _score_bar(score: float) -> str:
    color = "#00ff88" if score >= 65 else "#ffaa00" if score >= 45 else "#ff4444"
    pct = int(score)
    return (
        f'<div style="background:#1a1a1a;border-radius:4px;height:8px;width:100%;">'
        f'<div style="background:{color};width:{pct}%;height:8px;border-radius:4px;"></div>'
        f'</div><small style="color:{color};">{score:.0f}/100</small>'
    )


def _build_symbol_block(symbol: str, include_llm: bool) -> str:
    """Generate the HTML block for one symbol."""
    try:
        with Session(engine) as db:
            result = get_fusion(db, symbol, include_sentiment=True, include_llm=include_llm)
    except Exception as e:
        logger.error("Fusion failed for %s in newsletter: %s", symbol, e)
        return f'<div style="margin:16px 0;padding:12px;background:#1a0000;border-radius:8px;">⚠️ Failed to generate signal for <b>{symbol}</b>: {e}</div>'

    v_color = _verdict_color(result.verdict)
    score_html = _score_bar(result.master_fusion_score)

    # Timeframe grid
    tf_rows = ""
    for tf, sig in result.timeframes.items():
        lstm_html = _signal_badge(sig.lstm)
        ptst_html = _signal_badge(sig.patchtst or "N/A")
        agree_pct = int(sig.agreement * 100)
        lstm_confs = f"{sig.lstm_confidence:.0%}"
        if sig.lstm_direction_confidence is not None:
            lstm_confs += f" / dir={sig.lstm_direction_confidence:.0%}"
        ptst_probs = ""
        if sig.patchtst_prob_up is not None:
            ptst_probs = f"↑{sig.patchtst_prob_up:.0%} →{sig.patchtst_prob_flat:.0%} ↓{sig.patchtst_prob_down:.0%}"
        tf_rows += f"""
        <tr style="border-bottom:1px solid #222;">
          <td style="padding:4px 8px;color:#aaa;">{tf}</td>
          <td style="padding:4px 8px;">{lstm_html}<br><small style="color:#666;">{lstm_confs}</small></td>
          <td style="padding:4px 8px;">{ptst_html}<br><small style="color:#666;">{ptst_probs}</small></td>
          <td style="padding:4px 8px;color:{'#00ff88' if agree_pct==100 else '#ffaa00' if agree_pct>=50 else '#ff4444'};">{agree_pct}%</td>
        </tr>"""

    # Sentiment block
    sentiment_html = ""
    if result.sentiment:
        s = result.sentiment
        s_color = "#00ff88" if "bull" in s.overall_sentiment else "#ff4444" if "bear" in s.overall_sentiment else "#888"
        sentiment_html = f"""
        <div style="margin-top:12px;padding:8px;background:#111;border-radius:4px;">
          <b style="color:#aaa;">📰 Sentiment (FinBERT):</b>
          <span style="color:{s_color};font-weight:bold;"> {s.overall_sentiment.upper()}</span>
          (score: {s.overall_score:+.2f}) — Bias: {s.trading_bias} ({s.bias_strength})<br>
          <small style="color:#666;">+{s.positive_count} bullish / -{s.negative_count} bearish / {s.neutral_count} neutral from {s.news_count} headlines</small>
        </div>"""

    # LLM block — full reasoning
    llm_html = ""
    if result.llm_analysis:
        llm = result.llm_analysis
        llm_color = _verdict_color(llm.action)
        agree_label = "✅ Validates Fusion" if llm.validates_fusion else "⚠️ Challenges Fusion"
        agree_bg = "#0a1a0a" if llm.validates_fusion else "#1a0e00"

        # Key levels
        kl = llm.key_levels or {}
        kl_parts = []
        if kl.get("tp1"):   kl_parts.append(f'TP1: <b style="color:#00ff88;">{kl["tp1"]}</b>')
        if kl.get("tp2"):   kl_parts.append(f'TP2: <b style="color:#00cc66;">{kl["tp2"]}</b>')
        if kl.get("stop_loss"): kl_parts.append(f'SL: <b style="color:#ff4444;">{kl["stop_loss"]}</b>')
        kl_html = " &nbsp;|&nbsp; ".join(kl_parts)

        # Risk warnings
        warnings = llm.warnings or []
        warnings_html = ""
        if warnings:
            w_items = "".join(f'<li style="margin:2px 0;color:#ff8800;">⚠️ {w}</li>' for w in warnings)
            warnings_html = f'<ul style="margin:6px 0 0 0;padding-left:16px;font-size:11px;">{w_items}</ul>'

        # Divergence reason
        divergence_html = ""
        if llm.divergence_reason:
            divergence_html = f'<div style="margin-top:6px;padding:6px 8px;background:#1a0800;border-radius:4px;color:#ff8800;font-size:12px;">⚠️ {llm.divergence_reason}</div>'

        llm_html = f"""
        <div style="margin-top:14px;padding:12px;background:{agree_bg};border-left:4px solid {llm_color};border-radius:6px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <b style="color:#ccc;font-size:13px;">🤖 Claude AI Analysis</b>
            <span style="font-size:11px;color:#888;">{agree_label}</span>
          </div>

          <div style="margin-bottom:8px;">
            <span style="color:{llm_color};font-weight:bold;font-size:16px;">{llm.action}</span>
            <span style="color:#888;font-size:12px;margin-left:8px;">{llm.confidence_level.upper()} confidence</span>
            <span style="color:#666;font-size:12px;margin-left:8px;">· Independent bias: <b style="color:#aaa;">{llm.independent_bias}</b></span>
          </div>

          {divergence_html}

          <div style="margin-top:10px;">
            <div style="color:#888;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Market Structure</div>
            <div style="color:#ccc;font-size:12px;line-height:1.5;">{llm.market_structure}</div>
          </div>

          <div style="margin-top:10px;">
            <div style="color:#888;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">News Impact</div>
            <div style="color:#ccc;font-size:12px;line-height:1.5;">{llm.news_impact}</div>
          </div>

          <div style="margin-top:10px;">
            <div style="color:#888;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Entry Strategy</div>
            <div style="color:#ccc;font-size:12px;line-height:1.5;">{llm.entry_strategy}</div>
          </div>

          {f'<div style="margin-top:10px;font-size:12px;color:#aaa;">{kl_html}</div>' if kl_html else ''}

          {warnings_html}
        </div>"""

    # Targets
    t = result.targets
    targets_html = ""
    if t.tp1 or t.sl:
        targets_html = f"""
        <div style="margin-top:8px;color:#aaa;font-size:12px;">
          {'TP1: <b style="color:#00ff88;">' + str(round(t.tp1, 5)) + '</b>' if t.tp1 else ''}
          {'&nbsp;|&nbsp;' if t.tp1 and t.sl else ''}
          {'SL: <b style="color:#ff4444;">' + str(round(t.sl, 5)) + '</b>' if t.sl else ''}
          {'&nbsp;|&nbsp;ATR: ' + str(round(t.atr, 5)) if t.atr else ''}
        </div>"""

    return f"""
    <div style="margin:20px 0;padding:16px;background:#111;border-radius:8px;border:1px solid #222;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <h3 style="margin:0;color:#fff;">{symbol}</h3>
        <span style="color:{v_color};font-weight:bold;font-size:14px;">{result.verdict}</span>
      </div>
      <div style="margin:8px 0;">{score_html}</div>
      <table style="width:100%;border-collapse:collapse;margin-top:12px;">
        <thead>
          <tr style="color:#666;font-size:11px;text-transform:uppercase;">
            <th style="text-align:left;padding:4px 8px;">TF</th>
            <th style="text-align:left;padding:4px 8px;">LSTM</th>
            <th style="text-align:left;padding:4px 8px;">PatchTST</th>
            <th style="text-align:left;padding:4px 8px;">Agreement</th>
          </tr>
        </thead>
        <tbody>{tf_rows}</tbody>
      </table>
      {targets_html}
      {sentiment_html}
      {llm_html}
      <p style="color:#555;font-size:11px;margin-top:12px;">{result.reasoning}</p>
    </div>"""


def generate_newsletter_html(
    symbols: list[str],
    include_llm: bool = False,
    period: str = "daily",
) -> tuple[str, dict]:
    """
    Build the full newsletter HTML and return (html, stats).
    stats = {symbols_analyzed, bullish, bearish, divergent}
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stats = {"symbols_analyzed": 0, "bullish": 0, "bearish": 0, "divergent": 0}

    symbol_blocks = ""
    for sym in symbols:
        try:
            with Session(engine) as db:
                result = get_fusion(db, sym, include_sentiment=False, include_llm=False)
            v = result.verdict.upper()
            if "BUY" in v:
                stats["bullish"] += 1
            elif "SELL" in v:
                stats["bearish"] += 1
            else:
                stats["divergent"] += 1
            stats["symbols_analyzed"] += 1
        except Exception:
            pass
        symbol_blocks += _build_symbol_block(sym, include_llm=include_llm)

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:monospace;color:#fff;">
  <div style="max-width:680px;margin:0 auto;padding:24px;">
    <div style="text-align:center;margin-bottom:24px;">
      <h1 style="color:#00ff88;margin:0;font-size:22px;">⚡ FusionTrade AI</h1>
      <p style="color:#666;margin:4px 0;">{period.upper()} INTELLIGENCE BRIEF — {now}</p>
      <div style="margin-top:8px;font-size:12px;color:#aaa;">
        📊 {stats['symbols_analyzed']} pairs |
        <span style="color:#00ff88;">🟢 {stats['bullish']} bullish</span> |
        <span style="color:#ff4444;">🔴 {stats['bearish']} bearish</span> |
        <span style="color:#ffaa00;">🟡 {stats['divergent']} divergent</span>
      </div>
    </div>
    {symbol_blocks}
    <div style="margin-top:32px;padding-top:16px;border-top:1px solid #222;text-align:center;color:#444;font-size:11px;">
      FusionTrade AI · Powered by LSTM + PatchTST + FinBERT + Claude<br>
      This is not financial advice. Always manage your risk.
    </div>
  </div>
</body>
</html>"""
    return html, stats


def send_newsletter(
    symbols: list[str],
    recipients: list[str],
    include_llm: bool = False,
    period: str = "daily",
) -> dict:
    """Generate and send the newsletter. Returns status dict."""
    target_recipients = recipients or settings.SMTP_FROM_ADDRESS.split(",")
    if not target_recipients or not target_recipients[0]:
        return {"status": "error", "message": "No recipients configured"}

    html, stats = generate_newsletter_html(symbols, include_llm=include_llm, period=period)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"FusionTrade AI — {period.capitalize()} Brief {now}"

    success_count = 0
    for recipient in target_recipients:
        if email_service._send(recipient.strip(), subject, html):
            success_count += 1

    return {
        "status": "sent" if success_count > 0 else "failed",
        "recipients": success_count,
        **stats,
    }
