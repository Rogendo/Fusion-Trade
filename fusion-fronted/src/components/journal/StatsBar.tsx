import type { JournalStats } from '../../types/journal'
import { TrendingUp, TrendingDown, Clock, BarChart2, ArrowUpDown, AlertTriangle } from 'lucide-react'

interface Props {
  stats: JournalStats
}

interface StatCardProps {
  label: string
  value: string
  sub?: string
  icon: React.ReactNode
  color?: string
}

function StatCard({ label, value, sub, icon, color = 'text-slate-200' }: StatCardProps) {
  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-slate-500 uppercase tracking-wide">{label}</span>
        <span className="text-slate-600">{icon}</span>
      </div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[11px] text-slate-500">{sub}</p>}
    </div>
  )
}

export function StatsBar({ stats }: Props) {
  const pipColor = stats.total_pips >= 0 ? 'text-emerald-400' : 'text-rose-400'
  const pipsSign = stats.total_pips >= 0 ? '+' : ''

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <StatCard
        label="Win Rate"
        value={`${stats.win_rate.toFixed(1)}%`}
        sub={`${stats.wins}W / ${stats.losses}L`}
        icon={<TrendingUp className="h-4 w-4" />}
        color={stats.win_rate >= 50 ? 'text-emerald-400' : 'text-rose-400'}
      />
      <StatCard
        label="Total Pips"
        value={`${pipsSign}${stats.total_pips.toFixed(1)}`}
        sub={`${stats.total_trades} closed trades`}
        icon={<ArrowUpDown className="h-4 w-4" />}
        color={pipColor}
      />
      <StatCard
        label="Profit Factor"
        value={stats.profit_factor >= 999 ? '∞' : stats.profit_factor.toFixed(2)}
        sub="gross profit / gross loss"
        icon={<BarChart2 className="h-4 w-4" />}
        color={stats.profit_factor >= 1.5 ? 'text-emerald-400' : stats.profit_factor >= 1 ? 'text-amber-400' : 'text-rose-400'}
      />
      <StatCard
        label="Max Drawdown"
        value={`-${stats.max_drawdown.toFixed(1)} pips`}
        sub="peak-to-trough"
        icon={<TrendingDown className="h-4 w-4" />}
        color="text-rose-400"
      />
      <StatCard
        label="Pending"
        value={String(stats.pending)}
        sub="awaiting verification"
        icon={<Clock className="h-4 w-4" />}
        color="text-amber-400"
      />
      <StatCard
        label="Total Trades"
        value={String(stats.total_trades + stats.pending)}
        sub={`${stats.total_trades} closed`}
        icon={<AlertTriangle className="h-4 w-4" />}
      />
    </div>
  )
}
