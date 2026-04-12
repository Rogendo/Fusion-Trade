const styles: Record<string, string> = {
  win:     'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  loss:    'bg-rose-500/20 text-rose-400 border-rose-500/30',
  pending: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
}

export function OutcomeBadge({ outcome, status }: { outcome: string | null; status: string }) {
  const key = outcome?.toLowerCase() ?? status?.toLowerCase() ?? 'pending'
  const cls = styles[key] ?? styles.pending
  const label = outcome ?? status ?? 'PENDING'
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${cls}`}>
      {label.toUpperCase()}
    </span>
  )
}
