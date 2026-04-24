import type { JournalEntry } from '../../types/journal'
import { StatusBadge } from './StatusBadge'
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

  const formatPx = (v: number | null) => v != null ? v.toFixed(5) : '—'

  return (
    <tr className="border-b border-terminal-border hover:bg-terminal-muted/40 transition-colors text-xs">
      <td className="px-3 py-3 font-medium text-slate-200 whitespace-nowrap">{getLabel(entry.symbol)}</td>
      <td className="px-3 py-3 text-slate-400">{entry.interval}</td>
      <td className="px-3 py-3">
        <SignalChip signal={entry.signal as any} />
      </td>
      <td className="px-3 py-3 text-slate-400">
        {entry.confidence != null ? `${(entry.confidence * 100).toFixed(0)}%` : '—'}
      </td>
      <td className="px-3 py-3 font-mono text-slate-300">{formatPx(entry.entry_price)}</td>
      <td className="px-3 py-3 font-mono text-slate-400">
        {entry.take_profit_1 != null ? formatPx(entry.take_profit_1) : '—'}
      </td>
      <td className="px-3 py-3 font-mono text-slate-400">
        {entry.stop_loss != null ? formatPx(entry.stop_loss) : '—'}
      </td>
      <td className="px-3 py-3 font-mono text-slate-400">
        {entry.exit_price != null ? formatPx(entry.exit_price) : '—'}
      </td>
      <td className={`px-3 py-3 font-mono font-semibold ${pipColor}`}>
        {entry.pips != null
          ? `${entry.pips >= 0 ? '+' : ''}${entry.pips.toFixed(1)}`
          : '—'}
      </td>
      <td className="px-3 py-3">
        <StatusBadge status={entry.status} />
      </td>
      <td className="px-3 py-3">
        <OutcomeBadge outcome={entry.outcome} />
      </td>
      <td className="px-3 py-3 text-slate-600 whitespace-nowrap">{relativeTime(entry.created_at)}</td>
    </tr>
  )
}
