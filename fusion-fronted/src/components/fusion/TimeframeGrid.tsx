import type { TimeframeSignal } from '../../types/fusion'
import { TimeframeCard } from './TimeframeCard'

interface Props {
  timeframes: Record<string, TimeframeSignal>
  symbol: string
}

const TF_ORDER = ['15m', '30m', '1h', '4h']

export function TimeframeGrid({ timeframes, symbol }: Props) {
  // Sort timeframes in canonical order
  const entries = TF_ORDER
    .filter(tf => tf in timeframes)
    .map(tf => [tf, timeframes[tf]] as [string, TimeframeSignal])

  // Add any extra timeframes not in order list
  Object.keys(timeframes).forEach(tf => {
    if (!TF_ORDER.includes(tf)) entries.push([tf, timeframes[tf]])
  })

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {entries.map(([interval, tf]) => (
        <TimeframeCard key={interval} interval={interval} tf={tf} symbol={symbol} />
      ))}
    </div>
  )
}
