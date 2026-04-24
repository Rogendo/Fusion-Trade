import type { JournalOutcome } from '../../types/journal'

const styles: Record<string, string> = {
  WIN:     'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  LOSS:    'bg-rose-500/20 text-rose-400 border-rose-500/30',
  NEUTRAL: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
}

export function OutcomeBadge({ outcome }: { outcome: JournalOutcome }) {
  if (!outcome) return null
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-semibold ${styles[outcome] ?? styles.NEUTRAL}`}>
      {outcome}
    </span>
  )
}
