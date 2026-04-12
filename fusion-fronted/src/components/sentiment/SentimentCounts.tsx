interface Props {
  positive: number
  negative: number
  neutral: number
}

export function SentimentCounts({ positive, negative, neutral }: Props) {
  return (
    <div className="flex gap-2 flex-wrap justify-center">
      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
        {positive} Bullish
      </span>
      <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
        {negative} Bearish
      </span>
      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30">
        {neutral} Neutral
      </span>
    </div>
  )
}
