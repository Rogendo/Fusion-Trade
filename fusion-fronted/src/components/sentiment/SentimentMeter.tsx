interface Props {
  score: number   // -1.0 to +1.0
  label: string
}

export function SentimentMeter({ score, label }: Props) {
  const angle = ((score + 1) / 2) * 180
  const r = 52
  const cx = 70
  const cy = 65
  const rad = ((angle - 180) * Math.PI) / 180
  const nx = cx + r * Math.cos(rad)
  const ny = cy + r * Math.sin(rad)

  const color =
    score >= 0.3 ? '#10b981' :
    score <= -0.3 ? '#f43f5e' :
    '#f59e0b'

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path d="M 18 65 A 52 52 0 0 1 122 65" fill="none" stroke="#1a2840" strokeWidth="10" strokeLinecap="round" />
        <path d="M 18 65 A 52 52 0 0 1 70 13" fill="none" stroke="#f43f5e" strokeWidth="4" strokeLinecap="round" opacity="0.4" />
        <path d="M 70 13 A 52 52 0 0 1 122 65" fill="none" stroke="#10b981" strokeWidth="4" strokeLinecap="round" opacity="0.4" />
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="2.5" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="4" fill={color} />
        <text x={cx} y={cy + 18} textAnchor="middle" fill="white" fontSize="13" fontWeight="700">
          {score >= 0 ? '+' : ''}{score.toFixed(2)}
        </text>
      </svg>
      <span className="text-xs font-medium" style={{ color }}>{label}</span>
    </div>
  )
}
