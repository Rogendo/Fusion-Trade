import { useState } from 'react'
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

// TradingView widgetembed does NOT accept percent-encoded symbols (%3A, %21).
// Build the URL manually so COMEX:GC1! stays as-is.
function buildSrc(tvSymbol: string, interval: string): string {
  const base = 'https://www.tradingview.com/widgetembed/'
  const params = [
    `symbol=${tvSymbol}`,
    `interval=${interval}`,
    `timezone=Etc%2FUTC`,
    `theme=dark`,
    `style=1`,
    `locale=en`,
    `backgroundColor=%230d1526`,
    `gridColor=rgba(26%2C40%2C64%2C0.5)`,
    `hide_top_toolbar=false`,
    `hide_legend=false`,
    `hide_volume=false`,
    `allow_symbol_change=false`,
    `save_image=false`,
    `withdateranges=true`,
  ].join('&')
  return `${base}?${params}`
}

export function TradingViewChart({ symbol, height = 420 }: Props) {
  const [activeInterval, setActiveInterval] = useState('60')
  const tvSymbol = getTVSymbol(symbol)
  const src = buildSrc(tvSymbol, activeInterval)

  return (
    <div
      className="bg-terminal-surface border border-terminal-border rounded-xl overflow-hidden"
      style={{ height: `${height + 36}px` }}
    >
      {/* Timeframe selector */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-terminal-border bg-terminal-bg/50">
        <span className="text-[10px] text-slate-600 mr-2 uppercase tracking-wider">TF</span>
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
        <span className="ml-auto text-[10px] text-slate-600">{tvSymbol}</span>
      </div>

      {/* Iframe — key forces full reload when symbol or interval changes */}
      <iframe
        key={`${tvSymbol}-${activeInterval}`}
        src={src}
        style={{ width: '100%', height: `${height}px`, border: 'none', display: 'block' }}
        allowTransparency
        title={`${symbol} chart`}
      />
    </div>
  )
}
