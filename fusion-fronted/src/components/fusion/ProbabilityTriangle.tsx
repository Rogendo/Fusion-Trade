import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props {
  probUp: number    // patchtst_prob_up
  probFlat: number  // patchtst_prob_flat
  probDown: number  // patchtst_prob_down
}

export function ProbabilityTriangle({ probUp, probFlat, probDown }: Props) {
  const up   = (probUp   * 100).toFixed(0)
  const flat = (probFlat * 100).toFixed(0)
  const down = (probDown * 100).toFixed(0)

  const winner =
    probUp > probFlat && probUp > probDown ? 'up' :
    probDown > probUp && probDown > probFlat ? 'down' :
    'flat'

  return (
    <div className="space-y-1">
      <div className="flex h-2 rounded overflow-hidden gap-px">
        <div className="bg-emerald-500 transition-all" style={{ width: `${probUp * 100}%` }} />
        <div className="bg-slate-600 transition-all" style={{ width: `${probFlat * 100}%` }} />
        <div className="bg-rose-500 transition-all" style={{ width: `${probDown * 100}%` }} />
      </div>
      <div className="flex justify-between text-[10px]">
        <span className={`flex items-center gap-0.5 ${winner === 'up' ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
          <TrendingUp className="h-2.5 w-2.5" /> {up}%
        </span>
        <span className={`flex items-center gap-0.5 ${winner === 'flat' ? 'text-slate-300 font-semibold' : 'text-slate-600'}`}>
          <Minus className="h-2.5 w-2.5" /> {flat}%
        </span>
        <span className={`flex items-center gap-0.5 ${winner === 'down' ? 'text-rose-400 font-semibold' : 'text-slate-500'}`}>
          <TrendingDown className="h-2.5 w-2.5" /> {down}%
        </span>
      </div>
    </div>
  )
}
