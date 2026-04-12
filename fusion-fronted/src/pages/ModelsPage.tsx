import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getModelConfig, updateModelConfig, resetModelConfig, triggerPredict, type ModelConfig } from '../api/ml'
import { Button } from '../components/ui/Button'
import { SkeletonCard } from '../components/ui/Skeleton'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import {
  Cpu, Play, BarChart2, ChevronRight, RotateCcw,
  BookOpen, Settings, Grid3X3, Save, Info,
} from 'lucide-react'
import {
  TRAINED_SYMBOLS, SYMBOL_GROUPS, MODEL_COVERAGE,
  getLabel, getCoverage,
} from '../utils/symbolMeta'
import toast from 'react-hot-toast'

// ── Shared ────────────────────────────────────────────────────────────────────

const ALL_TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']

const TABS = [
  { id: 'coverage', label: 'Coverage', icon: Grid3X3 },
  { id: 'config',   label: 'Parameters', icon: Settings },
  { id: 'docs',     label: 'Model Docs', icon: BookOpen },
] as const
type Tab = typeof TABS[number]['id']

// ── Coverage tab ─────────────────────────────────────────────────────────────

function CoverageCell({ has, model }: { has: boolean; model: 'lstm' | 'patchtst' }) {
  if (!has) return <span className="text-slate-700 text-xs">—</span>
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
      model === 'lstm'
        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/20'
        : 'bg-purple-500/20 text-purple-400 border border-purple-500/20'
    }`}>
      {model === 'lstm' ? 'LSTM' : 'TST'}
    </span>
  )
}

function CoverageTab() {
  const navigate = useNavigate()
  const [selectedSymbol, setSelectedSymbol] = useState('')
  const [selectedInterval, setSelectedInterval] = useState('1h')
  const predictMutation = useMutation({
    mutationFn: ({ symbol, interval }: { symbol: string; interval: string }) =>
      triggerPredict(symbol, interval),
    onSuccess: () => toast.success('Prediction triggered! Check back in ~30s.'),
    onError: () => toast.error('Failed. Is Celery running?'),
  })

  const availableTFs = selectedSymbol
    ? [...new Set([...(MODEL_COVERAGE[selectedSymbol]?.lstm ?? []), ...(MODEL_COVERAGE[selectedSymbol]?.patchtst ?? [])])]
    : ALL_TIMEFRAMES

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'LSTM Models', value: '35', sub: '7 FX pairs × 5 timeframes', color: 'text-blue-400' },
          { label: 'PatchTST Models', value: '6', sub: 'EURUSD (2 TFs) + Gold (4 TFs)', color: 'text-purple-400' },
          { label: 'Total', value: '41', sub: 'HuggingFace: Rogendo/forex-*-models', color: 'text-emerald-400' },
          { label: 'Symbols', value: String(TRAINED_SYMBOLS.length), sub: '7 FX pairs + Gold', color: 'text-amber-400' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-[10px] text-slate-600 mt-1">{sub}</p>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs">
        <span className="text-slate-500">Legend:</span>
        <span className="flex items-center gap-1.5">
          <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/20 text-[10px]">LSTM</span>
          <span className="text-slate-400">Keras LSTM — forex-lstm-models</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/20 text-[10px]">TST</span>
          <span className="text-slate-400">PatchTST Transformer — forex-patchtst-models</span>
        </span>
      </div>

      {/* Matrix */}
      <div className="overflow-x-auto rounded-xl border border-terminal-border">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-terminal-border bg-terminal-muted/50">
              <th className="px-4 py-3 text-[10px] text-slate-500 uppercase tracking-wider">Symbol</th>
              {ALL_TIMEFRAMES.map(tf => (
                <th key={tf} className="px-4 py-3 text-[10px] text-slate-500 uppercase text-center">{tf}</th>
              ))}
              <th className="px-4 py-3 text-[10px] text-slate-500 uppercase">Coverage</th>
            </tr>
          </thead>
          <tbody>
            {TRAINED_SYMBOLS.map(symbol => {
              const cov = getCoverage(symbol)
              const total = cov.lstm.length + cov.patchtst.length
              return (
                <tr key={symbol} className="border-b border-terminal-border hover:bg-terminal-muted/30 cursor-pointer"
                  onClick={() => navigate(`/analysis/${encodeURIComponent(symbol)}`)}>
                  <td className="px-4 py-3">
                    <p className="text-xs font-medium text-slate-200">{getLabel(symbol)}</p>
                    <p className="text-[10px] text-slate-600">{symbol}</p>
                  </td>
                  {ALL_TIMEFRAMES.map(tf => (
                    <td key={tf} className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center gap-0.5">
                        <CoverageCell has={cov.lstm.includes(tf)} model="lstm" />
                        <CoverageCell has={cov.patchtst.includes(tf)} model="patchtst" />
                      </div>
                    </td>
                  ))}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <div className="w-20 h-1.5 bg-terminal-muted rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${(total / (ALL_TIMEFRAMES.length * 2)) * 100}%` }} />
                      </div>
                      <span className="text-[10px] text-slate-500">{total}/10</span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Quick launch */}
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Launch Analysis</h2>
        <div className="space-y-3">
          {SYMBOL_GROUPS.map(group => (
            <div key={group.group}>
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">{group.group}</p>
              <div className="flex flex-wrap gap-2">
                {group.symbols.map(sym => {
                  const has = sym in MODEL_COVERAGE
                  return (
                    <button key={sym}
                      onClick={() => has && setSelectedSymbol(sym)}
                      disabled={!has}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors border ${
                        selectedSymbol === sym
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                          : has
                          ? 'text-slate-300 border-terminal-border hover:bg-terminal-muted'
                          : 'text-slate-700 border-terminal-border/30 cursor-default'
                      }`}
                    >
                      {getLabel(sym)}
                      {has && <span className="text-[8px] text-emerald-600 ml-0.5">●</span>}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        {selectedSymbol && (
          <div className="flex items-center gap-3 pt-3 border-t border-terminal-border flex-wrap">
            <div className="flex gap-1">
              {availableTFs.map(tf => (
                <button key={tf} onClick={() => setSelectedInterval(tf)}
                  className={`px-2.5 py-1 text-xs rounded-lg transition-colors border ${
                    selectedInterval === tf
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : 'text-slate-400 border-terminal-border hover:bg-terminal-muted'
                  }`}>
                  {tf}
                </button>
              ))}
            </div>
            <Button variant="primary" size="sm" onClick={() => navigate(`/analysis/${encodeURIComponent(selectedSymbol)}`)}>
              <BarChart2 className="h-3.5 w-3.5" /> View Analysis <ChevronRight className="h-3.5 w-3.5" />
            </Button>
            <Button variant="secondary" size="sm"
              onClick={() => predictMutation.mutate({ symbol: selectedSymbol, interval: selectedInterval })}
              loading={predictMutation.isPending}>
              <Play className="h-3.5 w-3.5" /> Trigger Prediction
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Config tab ────────────────────────────────────────────────────────────────

function NumInput({ label, value, min, max, step, onChange, hint }:
  { label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void; hint?: string }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-xs text-slate-400">{label}</label>
        <span className="text-xs font-mono text-emerald-400">{value}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-terminal-muted rounded-full appearance-none cursor-pointer accent-emerald-500"
      />
      <div className="flex justify-between text-[10px] text-slate-600">
        <span>{min}</span>
        {hint && <span className="text-slate-500 italic">{hint}</span>}
        <span>{max}</span>
      </div>
    </div>
  )
}

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-2 pb-1 border-b border-terminal-border">
        <Icon className="h-4 w-4 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function ConfigTab() {
  const qc = useQueryClient()
  const { data: cfg, isLoading, isError, refetch } = useQuery({
    queryKey: ['model-config'],
    queryFn: getModelConfig,
    staleTime: 60_000,
  })

  const [local, setLocal] = useState<ModelConfig | null>(null)
  const effective = local ?? cfg

  const saveMutation = useMutation({
    mutationFn: (c: Partial<ModelConfig>) => updateModelConfig(c),
    onSuccess: (res) => {
      qc.setQueryData(['model-config'], res.config)
      setLocal(null)
      toast.success('Parameters saved — takes effect on next API call.')
    },
    onError: () => toast.error('Save failed.'),
  })

  const resetMutation = useMutation({
    mutationFn: resetModelConfig,
    onSuccess: (res) => {
      qc.setQueryData(['model-config'], res.config)
      setLocal(null)
      toast.success('Reset to factory defaults.')
    },
    onError: () => toast.error('Reset failed.'),
  })

  const set = (path: string, value: unknown) => {
    const base = local ?? cfg!
    const clone = JSON.parse(JSON.stringify(base)) as ModelConfig
    const keys = path.split('.')
    let obj: any = clone
    for (let i = 0; i < keys.length - 1; i++) obj = obj[keys[i]]
    obj[keys[keys.length - 1]] = value
    setLocal(clone)
  }

  const isDirty = local !== null

  if (isLoading) return <SkeletonCard lines={8} />
  if (isError || !effective) return <ErrorBanner message="Failed to load config." onRetry={() => refetch()} />

  const c = effective

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          Changes take effect on the next API call — no server restart needed.
        </p>
        <div className="flex gap-2">
          {isDirty && (
            <Button variant="ghost" size="sm" onClick={() => setLocal(null)}>
              Discard
            </Button>
          )}
          <Button variant="ghost" size="sm"
            onClick={() => resetMutation.mutate()} loading={resetMutation.isPending}>
            <RotateCcw className="h-3.5 w-3.5" /> Reset defaults
          </Button>
          <Button size="sm" onClick={() => saveMutation.mutate(local!)}
            loading={saveMutation.isPending} disabled={!isDirty}>
            <Save className="h-3.5 w-3.5" /> Save changes
          </Button>
        </div>
      </div>

      {isDirty && (
        <div className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
          Unsaved changes — click Save to apply.
        </div>
      )}

      {/* LSTM */}
      <Section title="LSTM — Data Window" icon={Cpu}>
        <p className="text-xs text-slate-500">
          Controls how much historical data is fetched per timeframe. Longer windows give the model more context but increase load time.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Object.entries(c.lstm.period_map).map(([tf, period]) => (
            <div key={tf} className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-400">{tf} fetch window</label>
                <select
                  value={period}
                  onChange={e => set(`lstm.period_map.${tf}`, e.target.value)}
                  className="text-xs bg-terminal-bg border border-terminal-border rounded px-2 py-0.5 text-emerald-400"
                >
                  {['5d','7d','14d','30d','60d','3mo','6mo','1y','2y'].map(p => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-terminal-border">
          <NumInput
            label="Confidence threshold" value={c.lstm.confidence_threshold}
            min={0.3} max={0.95} step={0.05}
            hint="min to show signal"
            onChange={v => set('lstm.confidence_threshold', v)}
          />
          <NumInput
            label="Direction confidence threshold" value={c.lstm.direction_confidence_threshold}
            min={0.3} max={0.95} step={0.05}
            hint="LSTM direction head"
            onChange={v => set('lstm.direction_confidence_threshold', v)}
          />
        </div>
      </Section>

      {/* PatchTST */}
      <Section title="PatchTST — Context & Patches" icon={Cpu}>
        <p className="text-xs text-slate-500">
          Lookback = how many candles the transformer sees. Patch length = how many candles per patch token.
          These must match the trained model weights — only change if you retrain.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="space-y-3">
            <p className="text-[11px] text-slate-400 font-medium">Lookback (candles)</p>
            {Object.entries(c.patchtst.interval_lookback).map(([tf, val]) => (
              <NumInput key={tf} label={tf} value={val} min={20} max={256} step={8}
                hint="⚠ retrain if changed"
                onChange={v => set(`patchtst.interval_lookback.${tf}`, v)} />
            ))}
          </div>
          <div className="space-y-3">
            <p className="text-[11px] text-slate-400 font-medium">Patch length (candles/token)</p>
            {Object.entries(c.patchtst.interval_patch_len).map(([tf, val]) => (
              <NumInput key={tf} label={tf} value={val} min={4} max={64} step={2}
                hint="⚠ retrain if changed"
                onChange={v => set(`patchtst.interval_patch_len.${tf}`, v)} />
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-terminal-border">
          <NumInput label="Min direction probability" value={c.patchtst.min_direction_prob}
            min={0.33} max={0.80} step={0.01} hint="below = FLAT"
            onChange={v => set('patchtst.min_direction_prob', v)} />
          <NumInput label="Noise threshold" value={c.patchtst.noise_threshold}
            min={0.0001} max={0.005} step={0.0001} hint="price move to count"
            onChange={v => set('patchtst.noise_threshold', v)} />
          <NumInput label="Strong signal threshold" value={c.patchtst.strong_signal_threshold}
            min={0.001} max={0.02} step={0.001} hint="for HIGH confidence"
            onChange={v => set('patchtst.strong_signal_threshold', v)} />
        </div>
      </Section>

      {/* Technical Indicators */}
      <Section title="Technical Indicators (PatchTST features)" icon={Cpu}>
        <p className="text-xs text-slate-500">
          These indicators are computed as input features for PatchTST. Changing periods changes the feature distribution —
          retrain for best results.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <NumInput label="RSI period" value={c.technical_indicators.rsi_period} min={5} max={50} step={1}
            onChange={v => set('technical_indicators.rsi_period', v)} />
          <NumInput label="MACD fast" value={c.technical_indicators.macd_fast} min={5} max={30} step={1}
            onChange={v => set('technical_indicators.macd_fast', v)} />
          <NumInput label="MACD slow" value={c.technical_indicators.macd_slow} min={15} max={60} step={1}
            onChange={v => set('technical_indicators.macd_slow', v)} />
          <NumInput label="MACD signal" value={c.technical_indicators.macd_signal} min={3} max={20} step={1}
            onChange={v => set('technical_indicators.macd_signal', v)} />
          <NumInput label="ATR period" value={c.technical_indicators.atr_period} min={5} max={50} step={1}
            onChange={v => set('technical_indicators.atr_period', v)} />
          <NumInput label="Bollinger period" value={c.technical_indicators.bb_period} min={10} max={50} step={1}
            onChange={v => set('technical_indicators.bb_period', v)} />
          <NumInput label="SMA period" value={c.technical_indicators.sma_period} min={10} max={200} step={5}
            onChange={v => set('technical_indicators.sma_period', v)} />
          <NumInput label="ROC period" value={c.technical_indicators.roc_period} min={3} max={30} step={1}
            onChange={v => set('technical_indicators.roc_period', v)} />
          <NumInput label="Momentum period" value={c.technical_indicators.mom_period} min={3} max={30} step={1}
            onChange={v => set('technical_indicators.mom_period', v)} />
        </div>
      </Section>

      {/* News & Sentiment */}
      <Section title="News & Sentiment" icon={Cpu}>
        <p className="text-xs text-slate-500">
          Controls how many articles are fetched, how many FinBERT analyzes, and how many are shown to Claude.
          More articles = better signal but slower response.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <NumInput label="Articles to fetch" value={c.news.fetch_limit} min={5} max={50} step={1}
            hint="from RSS feeds"
            onChange={v => set('news.fetch_limit', v)} />
          <NumInput label="Headlines in response" value={c.news.headlines_in_response} min={3} max={20} step={1}
            hint="shown in UI"
            onChange={v => set('news.headlines_in_response', v)} />
          <NumInput label="Headlines for Claude" value={c.news.headlines_for_llm} min={3} max={20} step={1}
            hint="sent to LLM prompt"
            onChange={v => set('news.headlines_for_llm', v)} />
        </div>
        <div className="grid grid-cols-2 gap-4 pt-3 border-t border-terminal-border">
          <NumInput label="Bullish threshold" value={c.news.sentiment_threshold_bullish}
            min={0.05} max={0.5} step={0.05} hint="score > this = bullish"
            onChange={v => set('news.sentiment_threshold_bullish', v)} />
          <NumInput label="Bearish threshold" value={c.news.sentiment_threshold_bearish}
            min={-0.5} max={-0.05} step={0.05} hint="score < this = bearish"
            onChange={v => set('news.sentiment_threshold_bearish', v)} />
        </div>
      </Section>

      {/* Fusion scoring */}
      <Section title="Fusion Scoring" icon={Cpu}>
        <p className="text-xs text-slate-500">
          Controls how the master fusion score is interpreted and when models are considered to "agree".
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <NumInput label="Agreement threshold" value={c.fusion.agreement_threshold}
            min={0.5} max={1.0} step={0.05} hint="0–1, when models agree"
            onChange={v => set('fusion.agreement_threshold', v)} />
          <NumInput label="High conviction cutoff" value={c.fusion.high_conviction_threshold}
            min={50} max={95} step={5} hint="score ≥ this = HIGH"
            onChange={v => set('fusion.high_conviction_threshold', v)} />
          <NumInput label="Moderate cutoff" value={c.fusion.moderate_threshold}
            min={30} max={70} step={5} hint="score ≥ this = MODERATE"
            onChange={v => set('fusion.moderate_threshold', v)} />
        </div>
      </Section>
    </div>
  )
}

// ── Docs tab ──────────────────────────────────────────────────────────────────

const MODEL_DOCS = [
  {
    id: 'lstm',
    name: 'LSTM (Long Short-Term Memory)',
    color: 'blue',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    repo: 'Rogendo/forex-lstm-models',
    count: '35 models (7 × 5)',
    architecture: 'Keras CNN-LSTM hybrid. A 1D convolutional front-end extracts local patterns, feeding a stacked LSTM that captures long-range temporal dependencies.',
    inputs: [
      'OHLCV candles (Open, High, Low, Close, Volume)',
      'RSI(14), MACD histogram, ATR(14)',
      'Bollinger Band width, SMA ratio',
      'ROC(10), Momentum(10)',
      'Hour-of-day cyclical encoding (sin/cos)',
      'HL_Range (High−Low), Close_Position (where Close sits in range)',
    ],
    outputs: [
      'predicted_price — next-candle price forecast',
      'signal — BUY / SELL / HOLD derived from predicted vs current price',
      'confidence — magnitude of predicted move scaled 0–1',
      'direction_confidence — LSTM direction head softmax probability',
      'direction_accuracy — historical % correct direction (backtested)',
      'RSI, MACD, ATR, support, resistance, trend, TP1/2/3, SL',
    ],
    strengths: [
      'Excellent at capturing short-term momentum patterns',
      'Fast inference (~50ms per symbol)',
      'Trained on 2+ years of tick data per symbol',
      'Separate direction classification head improves signal quality',
    ],
    improvements: [
      'Add attention mechanism over the LSTM hidden states',
      'Train with an asymmetric loss (penalize false BUY/SELL more than HOLD)',
      'Incorporate order book depth or volume profile features',
      'Ensemble multiple LSTMs trained on different data splits',
    ],
  },
  {
    id: 'patchtst',
    name: 'PatchTST (Patch Time Series Transformer)',
    color: 'purple',
    badge: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    repo: 'Rogendo/forex-patchtst-models',
    count: '6 models (EURUSD + Gold)',
    architecture: 'Pure Transformer encoder. Input candles are split into fixed-length patches (like ViT for images), with positional embeddings — then passed through 4 transformer layers (d_model=256, 4 heads, d_ff=512). Two heads: regression for price, classification for direction.',
    inputs: [
      '17 features: OHLCV + RSI, MACD_hist, ROC, MOM, ATR, BB_width, SMA_ratio + hour sin/cos',
      'Lookback of 96 candles (60 for 4h) divided into patches of 8–16 candles each',
      'RobustScaler normalization per feature',
    ],
    outputs: [
      'patchtst_signal — BUY / SELL / HOLD',
      'patchtst_confidence — regression head certainty',
      'prob_up / prob_flat / prob_down — direction head softmax (3-class)',
    ],
    strengths: [
      'Transformers capture non-local dependencies — sees the full context window at once',
      'Patch design reduces sequence length → more efficient attention',
      'Independent of LSTM; agreement between the two is a strong confluence signal',
      'Full 4-timeframe coverage on Gold (the most actively traded)',
    ],
    improvements: [
      'Train on all 7 FX pairs (currently only EURUSD)',
      'Add cross-symbol attention — train on all pairs jointly',
      'Use a decoder head for multi-step ahead forecasting',
      'Experiment with larger patch sizes (32–64) for 4h/1d timeframes',
    ],
  },
  {
    id: 'finbert',
    name: 'FinBERT (Financial Sentiment)',
    color: 'amber',
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    repo: 'ProsusAI/finbert (HuggingFace)',
    count: 'Singleton — shared across all symbols',
    architecture: 'BERT-base fine-tuned on financial text (10K SEC filings, Reuters, Bloomberg). Classifies text as Positive / Negative / Neutral with softmax probabilities.',
    inputs: [
      'News headlines and summaries fetched from RSS feeds',
      `Up to ${15} articles per symbol (configurable via Parameters tab)`,
      'Each article is independently scored then aggregated',
    ],
    outputs: [
      'overall_score — weighted average sentiment −1.0 to +1.0',
      'overall_sentiment — "Bullish" / "Bearish" / "Neutral" label',
      'trading_bias — directional bias string',
      'positive_count / negative_count / neutral_count',
      'top_headlines — scored articles with title, source, summary',
    ],
    strengths: [
      'Pre-trained on financial vocabulary — understands "hawkish", "dovish", "tapering" etc',
      'Fast after warm-up (~30s first call, instant after)',
      'Runs fully on-device — no external API needed',
    ],
    improvements: [
      'Fine-tune FinBERT specifically on FX news corpora',
      'Add entity recognition to filter news by currency pair',
      'Weight recent articles more heavily (time-decay weighting)',
      'Add social media sentiment (Twitter/Reddit for crypto)',
    ],
  },
  {
    id: 'claude',
    name: 'Claude (Two-Phase LLM Analysis)',
    color: 'emerald',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    repo: 'Anthropic API — claude-sonnet-4-6',
    count: 'On-demand, rate-limited 5/min',
    architecture: 'Two-phase prompt design to eliminate confirmation bias. Phase 1: Claude receives OHLCV data + news WITHOUT seeing model predictions — forms an independent view. Phase 2: Claude sees the ML fusion signals and explicitly validates or challenges them.',
    inputs: [
      'Current price, OHLCV context for each active timeframe',
      `Top ${10} news headlines + summaries (configurable)`,
      'FinBERT sentiment score and label',
      'ML model signals (LSTM + PatchTST per timeframe) — Phase 2 only',
      'Fusion score and verdict — Phase 2 only',
    ],
    outputs: [
      'action — BUY / SELL / WAIT / HOLD',
      'confidence_level — high / medium / low',
      'independent_bias — Claude\'s uninfluenced directional view',
      'validates_fusion — true if Claude agrees with ML signals',
      'divergence_reason — why Claude disagrees (if applicable)',
      'market_structure, news_impact, entry_strategy — prose analysis',
      'key_levels — { tp1, sl } as seen by Claude',
      'warnings — risk factors to watch',
      'raw_response — full unstructured Claude output',
    ],
    strengths: [
      'The only model that can read and interpret news narrative, not just score it',
      'Explicitly designed to challenge ML signals — high divergence_reason value',
      'Covers macro context, geopolitical risk, and calendar events',
      'Self-documenting: raw_response shows full reasoning chain',
    ],
    improvements: [
      'Add economic calendar context (NFP, CPI, FOMC dates)',
      'Feed in historical correlation between past Claude calls and actual outcomes',
      'Add a third phase: Claude reviews its own past prediction accuracy',
      'Use structured output mode for more reliable JSON parsing',
    ],
  },
]

function DocsTab() {
  const [open, setOpen] = useState<string>('lstm')

  return (
    <div className="space-y-3">
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 flex items-start gap-3">
        <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <p className="text-xs text-slate-400 leading-relaxed">
          FusionTrade AI runs <strong className="text-slate-300">four independent intelligence layers</strong> on every signal.
          LSTM and PatchTST are pure ML models — they see only price data.
          FinBERT reads news. Claude reads everything, forms an opinion independently, then challenges the ML.
          The Fusion Score is a weighted agreement measure across all timeframes.
        </p>
      </div>

      {MODEL_DOCS.map(doc => (
        <div key={doc.id} className="bg-terminal-surface border border-terminal-border rounded-xl overflow-hidden">
          <button
            onClick={() => setOpen(open === doc.id ? '' : doc.id)}
            className="w-full flex items-center justify-between px-5 py-4 hover:bg-terminal-muted/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${doc.badge}`}>
                {doc.id.toUpperCase()}
              </span>
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-200">{doc.name}</p>
                <p className="text-[10px] text-slate-500">{doc.count} · {doc.repo}</p>
              </div>
            </div>
            <span className="text-slate-600 text-xs">{open === doc.id ? '▲' : '▼'}</span>
          </button>

          {open === doc.id && (
            <div className="px-5 pb-5 space-y-5 border-t border-terminal-border">
              {/* Architecture */}
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-4 mb-1">Architecture</p>
                <p className="text-xs text-slate-300 leading-relaxed">{doc.architecture}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Inputs */}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Input Features</p>
                  <ul className="space-y-1">
                    {doc.inputs.map((inp, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                        <span className="text-emerald-600 mt-0.5 shrink-0">→</span>
                        {inp}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Outputs */}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Outputs</p>
                  <ul className="space-y-1">
                    {doc.outputs.map((out, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                        <span className="text-blue-500 mt-0.5 shrink-0">←</span>
                        {out}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-3 border-t border-terminal-border">
                {/* Strengths */}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Strengths</p>
                  <ul className="space-y-1">
                    {doc.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                        <span className="text-emerald-500 mt-0.5 shrink-0">✓</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Improvements */}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">How to Improve</p>
                  <ul className="space-y-1">
                    {doc.improvements.map((imp, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                        <span className="text-amber-500 mt-0.5 shrink-0">→</span>
                        {imp}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function ModelsPage() {
  const [tab, setTab] = useState<Tab>('coverage')

  return (
    <div className="flex flex-col flex-1 p-6 space-y-4 w-full max-w-7xl mx-auto">
      <div className="flex items-center gap-2">
        <Cpu className="h-5 w-5 text-slate-400" />
        <h1 className="text-base font-semibold text-slate-200">ML Model Registry</h1>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-terminal-border pb-0">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-t-lg transition-colors border-b-2 -mb-px ${
              tab === id
                ? 'border-emerald-500 text-emerald-400 bg-emerald-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'coverage' && <CoverageTab />}
      {tab === 'config'   && <ConfigTab />}
      {tab === 'docs'     && <DocsTab />}
    </div>
  )
}
