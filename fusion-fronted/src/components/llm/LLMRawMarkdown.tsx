import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface Props {
  raw: string
}

export function LLMRawMarkdown({ raw }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border border-terminal-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-terminal-muted transition-colors"
      >
        <span>View full Claude response</span>
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {open && (
        <div className="px-4 py-3 border-t border-terminal-border prose prose-invert prose-sm max-w-none text-slate-300">
          <ReactMarkdown>{raw}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
