import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPreview, triggerNewsletter } from '../api/newsletter'
import { SkeletonCard } from '../components/ui/Skeleton'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Button } from '../components/ui/Button'
import { Mail, Send, RefreshCw, Bot } from 'lucide-react'
import toast from 'react-hot-toast'

const DEFAULT_SYMBOLS = ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD']

export function NewsletterPage() {
  const [includeLlm, setIncludeLlm] = useState(true)
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['newsletter-preview', includeLlm],
    queryFn: () => getPreview({ symbols: DEFAULT_SYMBOLS, include_llm: includeLlm }),
    staleTime: 5 * 60_000,
    retry: false,   // don't retry — request already takes ~20s, 3 retries = 1min of spinning
  })

  const sendMutation = useMutation({
    mutationFn: () => triggerNewsletter({ symbols: DEFAULT_SYMBOLS, include_llm: includeLlm }),
    onSuccess: () => toast.success('Newsletter triggered successfully!'),
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join(', ')
        : typeof detail === 'string' ? detail : 'Failed to trigger newsletter.'
      toast.error(msg)
    },
  })

  const handleSend = () => {
    if (confirm(`Send newsletter to all subscribers now?\nClaude AI insights: ${includeLlm ? 'included' : 'excluded'}`)) {
      sendMutation.mutate()
    }
  }

  const handleRefreshPreview = () => {
    queryClient.invalidateQueries({ queryKey: ['newsletter-preview'] })
    refetch()
  }

  return (
    <div className="flex flex-col flex-1 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-slate-400" />
          <h1 className="text-base font-semibold text-slate-200">Newsletter</h1>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* LLM toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <div
              className={`relative w-9 h-5 rounded-full transition-colors ${includeLlm ? 'bg-emerald-600' : 'bg-terminal-muted'}`}
              onClick={() => setIncludeLlm(v => !v)}
            >
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${includeLlm ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </div>
            <span className="flex items-center gap-1 text-xs text-slate-400">
              <Bot className="h-3.5 w-3.5" />
              Claude insights
            </span>
          </label>

          <Button onClick={handleRefreshPreview} variant="ghost" size="sm">
            <RefreshCw className="h-4 w-4" />
            Refresh preview
          </Button>

          <Button onClick={handleSend} loading={sendMutation.isPending} variant="primary">
            <Send className="h-4 w-4" />
            Send Newsletter
          </Button>
        </div>
      </div>

      {/* Status bar */}
      <div className={`flex items-start gap-2 text-xs p-3 rounded-lg border ${
        includeLlm
          ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
          : 'text-slate-500 border-terminal-border bg-terminal-surface'
      }`}>
        <span className={`w-2 h-2 rounded-full mt-0.5 shrink-0 ${includeLlm ? 'bg-amber-500' : 'bg-slate-600'}`} />
        {includeLlm
          ? 'Claude AI insights enabled — preview will take 2–3 minutes per symbol. Be patient after clicking "Refresh preview".'
          : 'ML signals only — fast preview. Enable Claude insights above for deeper analysis (adds ~2–3 min per symbol).'
        }
      </div>

      {isLoading && <SkeletonCard lines={10} />}
      {isError && (
        <ErrorBanner
          message={`Failed to load preview. ${(error as any)?.response?.data?.detail ?? (error as any)?.message ?? ''}`}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <div className="bg-terminal-surface border border-terminal-border rounded-xl overflow-hidden flex-1">
          <div className="px-4 py-3 border-b border-terminal-border flex items-center justify-between">
            <p className="text-xs text-slate-400">
              Preview — {includeLlm ? 'with Claude AI insights' : 'ML signals only'}
            </p>
          </div>
          <iframe
            srcDoc={data.preview_html}
            className="w-full"
            style={{ height: 'calc(100vh - 220px)', border: 'none' }}
            sandbox="allow-same-origin"
            title="Newsletter Preview"
          />
        </div>
      )}
    </div>
  )
}
