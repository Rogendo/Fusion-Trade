import type { TimeframeSignal } from '../../types/fusion'
import { ModelAgreementBar } from './ModelAgreementBar'
import { ProbabilityTriangle } from './ProbabilityTriangle'
import { SignalChip } from '../ui/SignalChip'
import { ConfidenceBar } from '../ui/ConfidenceBar'
import { formatPrice } from '../../utils/formatPrice'

interface Props {
  interval: string
  tf: TimeframeSignal
  symbol: string
}

export function TimeframeCard({ interval, tf, symbol }: Props) {
  const priceDelta = tf.predicted_price - tf.current_price
  const pricePct = tf.current_price ? (priceDelta / tf.current_price) * 100 : 0
  const priceUp = priceDelta >= 0

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-200">{interval.toUpperCase()}</span>
        {tf.agreement >= 0.8 && (
          <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
            AGREE
          </span>
        )}
      </div>

      {/* Agreement bar */}
      <ModelAgreementBar agreement={tf.agreement} />

      {/* LSTM row */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-500 w-14">LSTM</span>
          <SignalChip signal={tf.lstm} />
        </div>
        <ConfidenceBar value={tf.lstm_confidence} />
        {tf.lstm_direction_accuracy != null && (
          <div className="text-[10px] text-slate-600">
            Hist. acc: {tf.lstm_direction_accuracy.toFixed(1)}%
          </div>
        )}
      </div>

      {/* PatchTST row */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-500 w-14">PatchTST</span>
          <SignalChip signal={tf.patchtst} />
        </div>
        <ConfidenceBar value={tf.patchtst_confidence} />
      </div>

      {/* Probability bar */}
      <ProbabilityTriangle
        probUp={tf.patchtst_prob_up}
        probFlat={tf.patchtst_prob_flat}
        probDown={tf.patchtst_prob_down}
      />

      {/* Price prediction */}
      <div className="flex items-center justify-between text-xs pt-1 border-t border-terminal-border">
        <span className="text-slate-500 font-mono">{formatPrice(tf.current_price, symbol)}</span>
        <span className="text-slate-400">→</span>
        <span className="text-slate-200 font-mono">{formatPrice(tf.predicted_price, symbol)}</span>
        <span className={priceUp ? 'text-emerald-400' : 'text-rose-400'}>
          {priceUp ? '+' : ''}{pricePct.toFixed(2)}%
        </span>
      </div>
    </div>
  )
}
