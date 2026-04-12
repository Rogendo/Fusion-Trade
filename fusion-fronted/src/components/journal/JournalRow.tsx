import type { JournalEntry } from '../../types/journal'
import { OutcomeBadge } from './OutcomeBadge'
import { SignalChip } from '../ui/SignalChip'
import { getLabel } from '../../utils/symbolMeta'
import { relativeTime } from '../../utils/formatPrice'

interface Props {
  entry: JournalEntry
}

export function JournalRow({ entry }: Props) {
  const pipColor =
    (entry.pips ?? 0) > 0 ? 'text-emerald-400' :
    (entry.pips ?? 0) < 0 ? 'text-rose-400' :
    'text-slate-400'

  return (
    <tr className="border-b border-terminal-border hover:bg-terminal-muted/50 transition-colors">
      <td className="px-4 py-3 text-xs font-medium text-slate-200">{getLabel(entry.symbol)}</td>
      <td className="px-4 py-3 text-xs text-slate-400">{entry.interval}</td>
      <td className="px-4 py-3">
        <SignalChip signal={entry.signal as any} />
      </td>
      <td className="px-4 py-3 text-xs text-slate-500">
        <div className="flex gap-1">
          {entry.lstm_signal && <SignalChip signal={entry.lstm_signal as any} />}
          {entry.patchtst_signal && <SignalChip signal={entry.patchtst_signal as any} />}
        </div>
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">
        {entry.fusion_score != null ? entry.fusion_score.toFixed(1) : '—'}
      </td>
      <td className="px-4 py-3 text-xs font-mono text-slate-300">
        {entry.entry_price?.toFixed(4) ?? '—'}
      </td>
      <td className="px-4 py-3 text-xs font-mono text-slate-300">
        {entry.exit_price?.toFixed(4) ?? '—'}
      </td>
      <td className={`px-4 py-3 text-xs font-mono font-medium ${pipColor}`}>
        {entry.pips != null ? (entry.pips >= 0 ? '+' : '') + entry.pips.toFixed(1) : '—'}
      </td>
      <td className="px-4 py-3">
        <OutcomeBadge outcome={entry.outcome} status={entry.status} />
      </td>
      <td className="px-4 py-3 text-xs text-slate-600">{relativeTime(entry.created_at)}</td>
    </tr>
  )
}
