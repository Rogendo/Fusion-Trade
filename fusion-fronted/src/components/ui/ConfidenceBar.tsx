interface Props {
  value: number  // 0.0–1.0
  className?: string
}

export function ConfidenceBar({ value, className = '' }: Props) {
  const pct = Math.min(100, Math.max(0, value * 100))
  const color =
    pct >= 70 ? 'bg-emerald-500' :
    pct >= 50 ? 'bg-amber-500' :
    'bg-rose-500'

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-1.5 bg-terminal-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct.toFixed(0)}%</span>
    </div>
  )
}
