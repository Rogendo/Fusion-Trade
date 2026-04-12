import type { Targets } from '../../types/fusion'
import { formatPrice } from '../../utils/formatPrice'

interface Props {
  targets: Targets
  symbol: string
}

function TargetLabel({
  label, value, symbol, color,
}: {
  label: string; value: number | null; symbol: string; color: string
}) {
  if (value == null) return null
  return (
    <div className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg border ${color}`}>
      <span className="text-[10px] text-slate-400">{label}</span>
      <span className="text-sm font-mono font-semibold text-slate-200">
        {formatPrice(value, symbol)}
      </span>
    </div>
  )
}

export function TargetsPanel({ targets, symbol }: Props) {
  const hasAny = targets.tp1 || targets.sl

  if (!hasAny) return null

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-200">Price Targets</h3>
        {targets.atr != null && (
          <span className="text-[10px] text-slate-500">ATR {formatPrice(targets.atr, symbol)}</span>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <TargetLabel label="TP1" value={targets.tp1} symbol={symbol} color="border-emerald-500/30 bg-emerald-500/5" />
        <TargetLabel label="TP2" value={targets.tp2} symbol={symbol} color="border-emerald-500/20 bg-emerald-500/5" />
        <TargetLabel label="TP3" value={targets.tp3} symbol={symbol} color="border-emerald-500/10 bg-emerald-500/5" />
        <TargetLabel label="SL"  value={targets.sl}  symbol={symbol} color="border-rose-500/30 bg-rose-500/5" />
      </div>
    </div>
  )
}
