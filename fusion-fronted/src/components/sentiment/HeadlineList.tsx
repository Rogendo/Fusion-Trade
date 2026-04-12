import type { Headline } from '../../types/fusion'
import { relativeTime } from '../../utils/formatPrice'
import { ExternalLink } from 'lucide-react'

interface Props {
  headlines: Headline[]
}

export function HeadlineList({ headlines }: Props) {
  if (!headlines.length) {
    return <p className="text-xs text-slate-600 italic">No recent news.</p>
  }

  return (
    <ul className="space-y-2 max-h-60 overflow-y-auto pr-1">
      {headlines.map((h, i) => (
        <li key={i} className="group relative">
          <a
            href={h.link}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-2 rounded-lg hover:bg-terminal-muted transition-colors"
            title={h.summary}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs text-slate-300 leading-snug line-clamp-2 flex-1">
                {h.title}
              </p>
              <ExternalLink className="h-3 w-3 text-slate-600 shrink-0 mt-0.5 group-hover:text-slate-400" />
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] text-slate-600">{h.source}</span>
              <span className="text-[10px] text-slate-700">·</span>
              <span className="text-[10px] text-slate-600">{relativeTime(h.published)}</span>
            </div>
          </a>
          {/* Tooltip on hover */}
          {h.summary && (
            <div className="absolute z-10 left-0 top-full mt-1 w-72 bg-terminal-muted border border-terminal-border rounded-lg p-3 text-xs text-slate-300 leading-relaxed shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150">
              {h.summary}
            </div>
          )}
        </li>
      ))}
    </ul>
  )
}
