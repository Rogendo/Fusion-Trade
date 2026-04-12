import type { FusionResponse } from '../../types/fusion'
import { VerdictBadge } from './VerdictBadge'

interface Props {
  fusion: FusionResponse
}

function scoreColor(score: number): string {
  if (score >= 60) return '#10b981'  // emerald
  if (score >= 30) return '#f59e0b'  // amber
  return '#f43f5e'                   // rose
}

export function FusionScoreWidget({ fusion }: Props) {
  const { master_fusion_score, verdict, timeframes } = fusion
  const score = master_fusion_score

  // Convert dict to array for rendering
  const tfEntries = Object.entries(timeframes)
  const agreedCount = tfEntries.filter(([, tf]) => tf.agreement >= 0.8).length

  const r = 54
  const circumference = 2 * Math.PI * r
  const arcLen = (3 / 4) * circumference
  const offset = arcLen - (score / 100) * arcLen
  const color = scoreColor(score)
  const isPulsing = score >= 80

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-start gap-6">
        {/* Arc gauge */}
        <div className="relative flex-shrink-0">
          <svg width="140" height="110" viewBox="0 0 140 110">
            {/* Track */}
            <circle
              cx="70" cy="75" r={r}
              fill="none"
              stroke="#1a2840"
              strokeWidth="10"
              strokeDasharray={`${arcLen} ${circumference}`}
              strokeDashoffset="0"
              strokeLinecap="round"
              transform="rotate(135 70 75)"
            />
            {/* Fill */}
            <circle
              cx="70" cy="75" r={r}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeDasharray={`${arcLen} ${circumference}`}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(135 70 75)"
              className={isPulsing ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]' : ''}
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
            <text x="70" y="72" textAnchor="middle" fill="white" fontSize="28" fontWeight="700">
              {Math.round(score)}
            </text>
            <text x="70" y="89" textAnchor="middle" fill="#64748b" fontSize="11">
              FUSION
            </text>
          </svg>
        </div>

        {/* Right info */}
        <div className="flex flex-col gap-3 pt-1">
          <VerdictBadge verdict={verdict} />
          <div className="flex flex-col gap-1.5">
            <div className="text-xs text-slate-400">Timeframe Agreement</div>
            <div className="flex gap-2 flex-wrap">
              {tfEntries.map(([interval, tf]) => (
                <div
                  key={interval}
                  className={`text-xs px-2 py-0.5 rounded border ${
                    tf.agreement >= 0.8
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : 'bg-terminal-muted text-slate-500 border-terminal-border'
                  }`}
                >
                  {interval}
                </div>
              ))}
            </div>
            <div className="text-xs text-slate-400">
              {agreedCount}/{tfEntries.length} timeframes agree
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
