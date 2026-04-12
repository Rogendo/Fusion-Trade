import { useState, useEffect, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { getLLMAnalysis } from '../../api/fusion'
import type { LLMAnalysis } from '../../types/fusion'
import { LLMActionBadge } from './LLMActionBadge'
import { LLMRawMarkdown } from './LLMRawMarkdown'
import { Button } from '../ui/Button'
import { Bot, CheckCircle, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

interface Props {
  symbol: string
}

function ProgressBar({ active }: { active: boolean }) {
  const [progress, setProgress] = useState(0)
  const ref = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      setProgress(0)
      ref.current = setInterval(() => {
        setProgress(p => p >= 85 ? 85 : p + (85 - p) * 0.04)
      }, 500)
    } else {
      if (ref.current) clearInterval(ref.current)
      setProgress(0)
    }
    return () => { if (ref.current) clearInterval(ref.current) }
  }, [active])

  return (
    <div className="space-y-2">
      <div className="h-1.5 bg-terminal-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-emerald-500 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-xs text-slate-400 animate-pulse">
        Claude is independently analyzing the market…
      </p>
    </div>
  )
}

export function LLMAnalysisPanel({ symbol }: Props) {
  const [result, setResult] = useState<LLMAnalysis | null>(null)

  const mutation = useMutation({
    mutationFn: () => getLLMAnalysis(symbol),
    onSuccess: (data) => setResult(data),
    onError: (err) => {
      if (axios.isAxiosError(err) && err.response?.status === 429) {
        toast.error('Rate limit reached (5/min). Try again shortly.')
      } else if (axios.isAxiosError(err) && err.response?.status === 503) {
        toast.error('Claude API unavailable. Check CLAUDE_API_KEY in .env.')
      } else {
        const detail = axios.isAxiosError(err) ? err.response?.data?.detail : null
        toast.error(typeof detail === 'string' ? detail : 'Claude analysis failed.')
      }
    },
  })

  useEffect(() => { setResult(null) }, [symbol])

  const biasColor =
    result?.independent_bias?.toLowerCase().includes('bull') ? 'text-emerald-400' :
    result?.independent_bias?.toLowerCase().includes('bear') ? 'text-rose-400' :
    'text-slate-400'

  const biasIcon =
    result?.independent_bias?.toLowerCase().includes('bull') ? <TrendingUp className="h-4 w-4 text-emerald-400" /> :
    result?.independent_bias?.toLowerCase().includes('bear') ? <TrendingDown className="h-4 w-4 text-rose-400" /> :
    <Minus className="h-4 w-4 text-slate-400" />

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Bot className="h-4 w-4 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-200">Claude AI Analysis</h3>
      </div>

      {!result && !mutation.isPending && (
        <div className="flex flex-col items-center gap-3 py-4">
          <p className="text-xs text-slate-500 text-center">
            Claude forms an independent view first, then validates or challenges the ML signals.
          </p>
          <Button onClick={() => mutation.mutate()} variant="secondary">
            <Bot className="h-4 w-4" />
            Get AI Analysis
          </Button>
        </div>
      )}

      {mutation.isPending && <ProgressBar active />}

      {result && (
        <div className="space-y-4">
          {/* Action + confidence */}
          <div className="flex items-center gap-3 flex-wrap">
            <LLMActionBadge action={result.action} />
            <span className={`text-xs px-2 py-0.5 rounded border ${
              result.confidence_level === 'high'   ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
              result.confidence_level === 'medium' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
              'text-slate-400 border-slate-500/30 bg-slate-500/10'
            }`}>
              {result.confidence_level} confidence
            </span>
          </div>

          {/* Independent bias */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Independent bias:</span>
            {biasIcon}
            <span className={`text-sm font-medium ${biasColor}`}>{result.independent_bias}</span>
          </div>

          {/* Validation box */}
          <div className={`flex items-start gap-3 p-3 rounded-lg border ${
            result.validates_fusion
              ? 'border-emerald-500/30 bg-emerald-500/10'
              : 'border-amber-500/30 bg-amber-500/10'
          }`}>
            {result.validates_fusion
              ? <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              : <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
            }
            <div>
              <p className={`text-xs font-semibold ${result.validates_fusion ? 'text-emerald-300' : 'text-amber-300'}`}>
                {result.validates_fusion ? 'Confirms ML Signals ✓' : 'Challenges ML Signals ⚠'}
              </p>
              {result.divergence_reason && (
                <p className="text-xs text-slate-400 mt-1">{result.divergence_reason}</p>
              )}
            </div>
          </div>

          {/* Text sections */}
          {[
            { label: 'Market Structure', text: result.market_structure },
            { label: 'News Impact',      text: result.news_impact },
            { label: 'Entry Strategy',   text: result.entry_strategy },
          ].map(({ label, text }) => text ? (
            <div key={label}>
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className="text-xs text-slate-300 leading-relaxed">{text}</p>
            </div>
          ) : null)}

          {/* Key levels */}
          {result.key_levels && Object.keys(result.key_levels).length > 0 && (
            <div className="flex gap-3 flex-wrap">
              {Object.entries(result.key_levels).map(([k, v]) => (
                <div key={k} className="text-xs">
                  <span className="text-slate-500">{k.toUpperCase()}: </span>
                  <span className={`font-mono ${k.toLowerCase().includes('sl') ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {typeof v === 'number' ? v.toFixed(2) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result.warnings?.length > 0 && (
            <div className="space-y-1">
              {result.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-400">
                  <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Raw response */}
          {result.raw_response && <LLMRawMarkdown raw={result.raw_response} />}

          <Button
            onClick={() => mutation.mutate()}
            variant="ghost"
            size="sm"
            loading={mutation.isPending}
          >
            Re-run analysis
          </Button>
        </div>
      )}
    </div>
  )
}
