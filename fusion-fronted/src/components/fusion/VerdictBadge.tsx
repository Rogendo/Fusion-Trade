// verdict format from API: "HIGH CONVICTION (BUY)", "MODERATE (SELL)", "DIVERGENT (HOLD)"

function verdictStyle(verdict: string): string {
  const upper = verdict.toUpperCase()
  if (upper.includes('HIGH CONVICTION')) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
  if (upper.includes('MODERATE'))        return 'bg-amber-500/20 text-amber-300 border-amber-500/40'
  return 'bg-rose-500/20 text-rose-300 border-rose-500/40'  // DIVERGENT
}

export function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded border ${verdictStyle(verdict)}`}>
      {verdict}
    </span>
  )
}
