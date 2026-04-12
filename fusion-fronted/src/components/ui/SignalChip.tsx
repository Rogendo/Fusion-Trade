type Signal = 'BUY' | 'SELL' | 'HOLD' | 'WAIT' | null

const styles: Record<string, string> = {
  BUY:  'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  SELL: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  HOLD: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  WAIT: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
}

interface Props {
  signal: Signal
  size?: 'sm' | 'md'
}

export function SignalChip({ signal, size = 'sm' }: Props) {
  if (!signal) return <span className="text-slate-600 text-xs">—</span>
  const cls = styles[signal] ?? styles.HOLD
  const pad = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
  return (
    <span className={`inline-block font-semibold rounded border ${cls} ${pad}`}>
      {signal}
    </span>
  )
}
