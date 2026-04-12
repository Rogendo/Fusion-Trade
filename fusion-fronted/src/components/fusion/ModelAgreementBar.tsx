interface Props {
  agreement: number   // 0.0–1.0
}

export function ModelAgreementBar({ agreement }: Props) {
  const pct = agreement * 100
  const agreed = agreement >= 0.8
  const color = agreed ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-rose-500'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-terminal-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-xs font-medium ${agreed ? 'text-emerald-400' : 'text-slate-400'}`}>
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}
