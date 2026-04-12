import { useEffect, useRef, useState } from 'react'
import { getTVSymbol } from '../../utils/symbolMeta'

interface Props {
  symbol: string
  height?: number
}

const TIMEFRAMES = [
  { label: '15m', value: '15' },
  { label: '30m', value: '30' },
  { label: '1H',  value: '60' },
  { label: '4H',  value: '240' },
  { label: '1D',  value: 'D' },
]

export function TradingViewChart({ symbol, height = 420 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [activeInterval, setActiveInterval] = useState('60')  // default 1H
  const tvSymbol = getTVSymbol(symbol)

  useEffect(() => {
    if (!containerRef.current) return

    containerRef.current.innerHTML = ''

    const script = document.createElement('script')
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js'
    script.type = 'text/javascript'
    script.async = true
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: activeInterval,
      timezone: 'Etc/UTC',
      theme: 'dark',
      style: '1',
      locale: 'en',
      backgroundColor: '#0d1526',
      gridColor: 'rgba(26, 40, 64, 0.6)',
      hide_top_toolbar: false,
      hide_legend: false,
      hide_volume: false,
      allow_symbol_change: false,
      save_image: false,
      calendar: false,
      support_host: 'https://www.tradingview.com',
    })

    containerRef.current.appendChild(script)

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [tvSymbol, activeInterval])

  return (
    <div
      className="bg-terminal-surface border border-terminal-border rounded-xl overflow-hidden"
      style={{ height: `${height + 36}px` }}
    >
      {/* Timeframe selector bar */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-terminal-border bg-terminal-bg/50">
        <span className="text-[10px] text-slate-600 mr-2 uppercase tracking-wider">Timeframe</span>
        {TIMEFRAMES.map(tf => (
          <button
            key={tf.value}
            onClick={() => setActiveInterval(tf.value)}
            className={`px-2.5 py-1 text-xs rounded transition-colors ${
              activeInterval === tf.value
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-terminal-muted'
            }`}
          >
            {tf.label}
          </button>
        ))}
        <span className="ml-auto text-[10px] text-slate-600">TradingView</span>
      </div>

      {/* Chart */}
      <div ref={containerRef} style={{ height: `${height}px`, width: '100%' }} />
    </div>
  )
}
