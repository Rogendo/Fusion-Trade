import type { JournalStats } from '../../types/journal'

interface Props {
  stats: JournalStats
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-3 flex flex-col gap-1">
      <span className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</span>
      <span className="text-lg font-bold text-slate-200">{value}</span>
      {sub && <span className="text-[10px] text-slate-600">{sub}</span>}
    </div>
  )
}

export function StatsBar({ stats }: Props) {
  const pips = stats.total_pips ?? 0
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
      <StatCard label="Total" value={String(stats.total_trades)} />
      <StatCard label="Win Rate" value={`${(stats.win_rate ?? 0).toFixed(1)}%`} />
      <StatCard label="Wins" value={String(stats.wins)} />
      <StatCard label="Losses" value={String(stats.losses)} />
      <StatCard label="Pending" value={String(stats.pending)} />
      <StatCard label="Total Pips" value={pips >= 0 ? `+${pips.toFixed(1)}` : pips.toFixed(1)} />
      <StatCard label="Profit Factor" value={(stats.profit_factor ?? 0).toFixed(2)} />
      <StatCard label="Max Drawdown" value={`${(stats.max_drawdown ?? 0).toFixed(1)}`} />
    </div>
  )
}
