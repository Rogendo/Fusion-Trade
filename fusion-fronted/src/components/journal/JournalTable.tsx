import type { JournalEntry } from '../../types/journal'
import { JournalRow } from './JournalRow'

interface Props {
  entries: JournalEntry[]
}

const COLS = [
  'Symbol', 'TF', 'Signal', 'Conf',
  'Entry', 'TP1', 'SL', 'Exit',
  'Pips', 'Status', 'Outcome', 'Time'
]

export function JournalTable({ entries }: Props) {
  if (!entries.length) {
    return (
      <div className="text-center py-16 text-slate-500 text-sm bg-terminal-surface border border-terminal-border rounded-xl">
        <p className="mb-1">No journal entries yet.</p>
        <p className="text-xs text-slate-600">Signals are logged automatically each time the prediction worker runs.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-terminal-border">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-terminal-border bg-terminal-muted/50">
            {COLS.map(h => (
              <th key={h} className="px-3 py-3 text-[10px] text-slate-500 uppercase tracking-wider font-medium whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {entries.map(e => <JournalRow key={e.id} entry={e} />)}
        </tbody>
      </table>
    </div>
  )
}
