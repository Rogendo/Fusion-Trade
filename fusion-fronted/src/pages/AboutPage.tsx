import { Zap, Brain, BarChart2, Shield, AlertTriangle, Target, Cpu, TrendingUp } from 'lucide-react'
import { MODEL_COVERAGE, getLabel } from '../utils/symbolMeta'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6 space-y-3">
      <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
      {children}
    </div>
  )
}

function Feature({ icon: Icon, title, desc }: { icon: any; title: string; desc: string }) {
  return (
    <div className="flex gap-3">
      <div className="shrink-0 mt-0.5">
        <Icon className="h-4 w-4 text-emerald-400" />
      </div>
      <div>
        <p className="text-sm font-medium text-slate-200">{title}</p>
        <p className="text-xs text-slate-400 leading-relaxed mt-0.5">{desc}</p>
      </div>
    </div>
  )
}

export function AboutPage() {
  const trainedSymbols = Object.keys(MODEL_COVERAGE)

  return (
    <div className="flex-1 overflow-y-auto">
    <div className="p-6 space-y-4 max-w-3xl mx-auto">
      {/* Hero */}
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-emerald-500/20 border border-emerald-500/30 rounded-xl">
            <Zap className="h-6 w-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-200">FusionTrade AI</h1>
            <p className="text-xs text-slate-400">Multi-model trading intelligence platform</p>
          </div>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">
          FusionTrade AI combines two independent machine learning models — LSTM (Long Short-Term Memory) and PatchTST
          (Patch Time-Series Transformer) — with FinBERT news sentiment analysis and Claude AI's independent reasoning
          to generate high-confidence trading signals across major FX pairs and commodities.
        </p>
      </div>

      {/* What it does */}
      <Section title="How It Works">
        <div className="space-y-4">
          <Feature
            icon={Cpu}
            title="LSTM Neural Network"
            desc="A sequence model trained on historical OHLCV data for 7 FX pairs across 5 timeframes (5m, 15m, 30m, 1h, 4h). Produces directional signals (BUY/SELL/HOLD), confidence scores, and price predictions with key technical levels."
          />
          <Feature
            icon={BarChart2}
            title="PatchTST Transformer"
            desc="A patch-based time-series transformer trained for EUR/USD and Gold across 4 timeframes. Outputs directional probabilities (UP/FLAT/DOWN) that complement and challenge LSTM signals."
          />
          <Feature
            icon={TrendingUp}
            title="Fusion Scoring"
            desc="A weighted consensus engine that compares LSTM and PatchTST across all available timeframes. When both models agree, the Fusion Score rises (0–100). A score above 70 signals HIGH CONVICTION. Below 50 is DIVERGENT."
          />
          <Feature
            icon={Brain}
            title="Claude AI Two-Phase Analysis"
            desc="Claude independently forms its own market view from raw price data and news — without seeing the ML signals first. Only in phase 2 does it compare its view against the models, explicitly noting whether it validates or challenges them."
          />
          <Feature
            icon={Shield}
            title="FinBERT Sentiment"
            desc="Financial BERT analyses recent news headlines for each instrument, producing a sentiment score, trading bias, and categorised headline list. Sentiment is an input to the fusion picture, not the primary signal."
          />
        </div>
      </Section>

      {/* Trained models */}
      <Section title="Trained Model Coverage">
        <p className="text-xs text-slate-400 mb-3">
          Only instruments with trained models are available for analysis. Signals are not generated for untrained symbols.
        </p>
        <div className="space-y-2">
          {trainedSymbols.map(sym => {
            const cov = MODEL_COVERAGE[sym]
            return (
              <div key={sym} className="flex items-center gap-3 py-1.5 border-b border-terminal-border last:border-0">
                <span className="text-xs font-medium text-slate-200 w-24">{getLabel(sym)}</span>
                <div className="flex gap-2 flex-1">
                  {cov.lstm.length > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] text-slate-500 uppercase">LSTM</span>
                      <div className="flex gap-1">
                        {cov.lstm.map(tf => (
                          <span key={tf} className="text-[9px] px-1.5 py-0.5 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded">
                            {tf}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {cov.patchtst.length > 0 && (
                    <div className="flex items-center gap-1.5 ml-auto">
                      <span className="text-[9px] text-slate-500 uppercase">PatchTST</span>
                      <div className="flex gap-1">
                        {cov.patchtst.map(tf => (
                          <span key={tf} className="text-[9px] px-1.5 py-0.5 bg-violet-500/10 text-violet-400 border border-violet-500/20 rounded">
                            {tf}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </Section>

      {/* Who it's for */}
      <Section title="Who This Is For">
        <div className="space-y-2 text-sm text-slate-400 leading-relaxed">
          <p>FusionTrade AI is designed for:</p>
          <ul className="space-y-1.5 ml-4">
            {[
              'Retail FX and commodities traders who want ML-assisted signal generation',
              'Traders who want independent AI review before placing a trade — not just a raw signal',
              'Analysts who want multi-timeframe confluence confirmation before acting',
              'Anyone who wants to understand *why* a signal was generated, not just what it says',
            ].map((item, i) => (
              <li key={i} className="flex gap-2">
                <Target className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
          <p className="pt-1">
            This platform is built for informed traders who use AI as a co-analyst, not a replacement for
            their own judgement. The Claude analysis step explicitly mirrors how a human analyst would
            cross-check their view against a model — then decide whether to trust or challenge it.
          </p>
        </div>
      </Section>

      {/* Market sessions reference */}
      <Section title="FX Market Sessions (UTC)">
        <div className="space-y-2">
          {[
            { name: 'Sydney',   open: '22:00', close: '07:00', note: 'AUD, NZD pairs most active', color: 'text-sky-400' },
            { name: 'Tokyo',    open: '00:00', close: '09:00', note: 'JPY pairs most active', color: 'text-violet-400' },
            { name: 'London',   open: '08:00', close: '17:00', note: 'EUR, GBP most active — highest volume session', color: 'text-amber-400' },
            { name: 'New York', open: '13:00', close: '22:00', note: 'USD pairs most active; overlaps London 13–17 UTC', color: 'text-emerald-400' },
          ].map(s => (
            <div key={s.name} className="flex items-start gap-3 py-1.5 border-b border-terminal-border last:border-0">
              <span className={`text-xs font-medium w-20 ${s.color}`}>{s.name}</span>
              <span className="text-xs font-mono text-slate-300 w-28">{s.open} – {s.close}</span>
              <span className="text-xs text-slate-500 flex-1">{s.note}</span>
            </div>
          ))}
        </div>
        <div className="mt-2 p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg">
          <p className="text-xs text-emerald-300 font-medium">London / New York Overlap: 13:00–17:00 UTC</p>
          <p className="text-xs text-slate-400 mt-1">
            The highest-liquidity window of the trading day. Signals generated during this overlap carry the most
            market depth and are typically the most reliable for short-term execution.
          </p>
        </div>
      </Section>

      {/* Disclaimer */}
      <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-5 space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
          <h2 className="text-sm font-semibold text-amber-300">Important Disclaimers</h2>
        </div>
        <div className="space-y-2 text-xs text-slate-400 leading-relaxed">
          <p>
            <strong className="text-slate-300">Not financial advice.</strong> FusionTrade AI provides machine learning–generated
            signals and AI analysis for informational and educational purposes only. Nothing on this platform constitutes
            financial advice, investment advice, or a recommendation to buy or sell any financial instrument.
          </p>
          <p>
            <strong className="text-slate-300">Past performance is not indicative of future results.</strong> ML models are
            trained on historical data. Markets change, models can and do fail, and historical accuracy statistics shown in
            the platform do not guarantee future performance.
          </p>
          <p>
            <strong className="text-slate-300">Trading involves substantial risk.</strong> Forex and commodity trading
            involves significant risk of loss and may not be suitable for all investors. You should only trade with capital
            you can afford to lose. Never risk money that you cannot lose entirely.
          </p>
          <p>
            <strong className="text-slate-300">AI models can be wrong.</strong> Both the LSTM and PatchTST models produce
            probabilistic outputs — not certainties. The Claude AI analysis may also be incorrect or miss important context.
            Always conduct your own research and apply your own risk management before trading.
          </p>
          <p>
            <strong className="text-slate-300">Market data latency.</strong> Price data is sourced from Yahoo Finance and
            may be delayed by up to 15 minutes. Do not rely on this platform's prices for live order execution. Use your
            broker's platform for real-time pricing.
          </p>
          <p className="pt-1 border-t border-amber-500/10 text-slate-500">
            By using FusionTrade AI, you acknowledge that you have read and understood these disclaimers and accept full
            responsibility for your own trading decisions.
          </p>
        </div>
      </div>

      {/* Version */}
      <div className="text-center py-4">
        <p className="text-[10px] text-slate-700">
          FusionTrade AI · LSTM v1 (HuggingFace: Rogendo/forex-lstm-models) ·
          PatchTST v1 (HuggingFace: Rogendo/forex-patchtst-models)
        </p>
      </div>
    </div>
    </div>
  )
}
