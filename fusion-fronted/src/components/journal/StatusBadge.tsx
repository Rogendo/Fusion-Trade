import type { JournalStatus } from '../../types/journal'

const styles: Record<JournalStatus, string> = {
  PENDING:  'bg-amber-500/20 text-amber-400 border-amber-500/30',
  TP1_HIT:  'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  TP2_HIT:  'bg-emerald-500/30 text-emerald-300 border-emerald-500/40',
  TP3_HIT:  'bg-emerald-500/40 text-emerald-200 border-emerald-500/50',
  SL_HIT:   'bg-rose-500/20 text-rose-400 border-rose-500/30',
  EXPIRED:  'bg-slate-500/20 text-slate-500 border-slate-500/30',
  IGNORED:  'bg-slate-500/10 text-slate-600 border-slate-600/20',
}

const labels: Record<JournalStatus, string> = {
  PENDING:  'Pending',
  TP1_HIT:  'TP1 ✓',
  TP2_HIT:  'TP2 ✓',
  TP3_HIT:  'TP3 ✓',
  SL_HIT:   'SL Hit',
  EXPIRED:  'Expired',
  IGNORED:  'Ignored',
}

export function StatusBadge({ status }: { status: JournalStatus }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium whitespace-nowrap ${styles[status]}`}>
      {labels[status]}
    </span>
  )
}
