type Action = 'BUY' | 'SELL' | 'WAIT' | 'HOLD'

const styles: Record<Action, string> = {
  BUY:  'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  SELL: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
  WAIT: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  HOLD: 'bg-slate-500/20 text-slate-300 border-slate-500/40',
}

export function LLMActionBadge({ action }: { action: Action }) {
  return (
    <span className={`text-lg font-bold px-4 py-1.5 rounded-lg border ${styles[action]}`}>
      {action}
    </span>
  )
}
