import type { JournalEntry } from '../../types/journal'
import { JournalRow } from './JournalRow'

interface Props {
  entries: JournalEntry[]
}

export function JournalTable({ entries }: Props) {
  if (!entries.length) {
    return (
      <div className="text-center py-12 text-slate-500 text-sm bg-terminal-surface border border-terminal-border rounded-xl">
        No journal entries yet. Predictions will appear here after the daily run.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-terminal-border">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-terminal-border bg-terminal-muted/50">
            {['Symbol', 'TF', 'Signal', 'Models', 'Fusion', 'Entry', 'Exit', 'Pips', 'Status', 'Time'].map(h => (
              <th key={h} className="px-4 py-3 text-[10px] text-slate-500 uppercase tracking-wider font-medium">
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
