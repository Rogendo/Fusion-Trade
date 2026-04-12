import { useNavigate, useParams } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { TRAINED_SYMBOLS, getLabel } from '../../utils/symbolMeta'

interface Props {
  lastUpdated?: string | null
}

export function TopBar({ lastUpdated }: Props) {
  const { symbol } = useParams<{ symbol: string }>()
  const navigate = useNavigate()
  const activeSymbol = symbol ? decodeURIComponent(symbol) : ''

  return (
    <div className="flex items-center gap-1 px-4 py-2 border-b border-terminal-border bg-terminal-surface overflow-x-auto">
      <div className="flex gap-1 flex-1 min-w-0">
        {TRAINED_SYMBOLS.map(sym => (
          <button
            key={sym}
            onClick={() => navigate(`/analysis/${encodeURIComponent(sym)}`)}
            className={`px-2.5 py-1 text-xs rounded-lg transition-colors whitespace-nowrap flex-shrink-0 ${
              activeSymbol === sym
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:bg-terminal-muted hover:text-slate-200'
            }`}
          >
            {getLabel(sym)}
          </button>
        ))}
      </div>
      {lastUpdated && (
        <div className="flex items-center gap-1.5 text-[10px] text-slate-600 shrink-0 pl-2">
          <RefreshCw className="h-3 w-3" />
          <span className="hidden sm:inline">{lastUpdated}</span>
        </div>
      )}
    </div>
  )
}
