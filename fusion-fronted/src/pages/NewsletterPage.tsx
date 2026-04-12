import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { getPreview, triggerNewsletter } from '../api/newsletter'
import { Button } from '../components/ui/Button'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Mail, Send, RefreshCw, Zap } from 'lucide-react'
import toast from 'react-hot-toast'

const DEFAULT_SYMBOLS = ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD']

export function NewsletterPage() {
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)

  const previewMutation = useMutation({
    mutationFn: () => getPreview({ symbols: DEFAULT_SYMBOLS, include_llm: false, period: 'daily' }),
    onSuccess: (data) => {
      setPreviewHtml(data.preview_html)
      setPreviewError(null)
    },
    onError: (err: any) => {
      setPreviewError(err?.response?.data?.detail ?? 'Preview generation failed.')
    },
  })

  const triggerMutation = useMutation({
    mutationFn: triggerNewsletter,
    onSuccess: () => toast.success('Newsletter triggered successfully!'),
    onError: () => toast.error('Failed to trigger newsletter.'),
  })

  const handleSend = () => {
    if (confirm('Send newsletter to all subscribers now?')) {
      triggerMutation.mutate()
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
    <div className="p-6 space-y-4 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-slate-400" />
          <h1 className="text-base font-semibold text-slate-200">Newsletter</h1>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => previewMutation.mutate()}
            loading={previewMutation.isPending}
            variant="secondary"
          >
            <RefreshCw className="h-4 w-4" />
            {previewHtml ? 'Regenerate Preview' : 'Generate Preview'}
          </Button>
          <Button
            onClick={() => triggerMutation.mutate()}
            loading={triggerMutation.isPending}
            variant="primary"
          >
            <Zap className="h-4 w-4" />
            Quick Trigger
          </Button>
          <Button onClick={handleSend} variant="secondary">
            <Send className="h-4 w-4" />
            Send to Subscribers
          </Button>
        </div>
      </div>

      {previewError && <ErrorBanner message={previewError} onRetry={() => previewMutation.mutate()} />}

      {!previewHtml && !previewMutation.isPending && (
        <div className="flex flex-col items-center justify-center flex-1 gap-4 py-20 text-center">
          <Mail className="h-12 w-12 text-terminal-muted" />
          <div>
            <p className="text-slate-300 font-medium">No preview loaded</p>
            <p className="text-slate-500 text-sm mt-1">
              Click "Generate Preview" to build the newsletter.<br />
              This may take 1–2 minutes while models run.
            </p>
          </div>
          <Button onClick={() => previewMutation.mutate()} loading={previewMutation.isPending}>
            Generate Preview
          </Button>
        </div>
      )}

      {previewMutation.isPending && (
        <div className="flex flex-col items-center justify-center flex-1 gap-3 py-20">
          <div className="animate-spin h-8 w-8 border-2 border-emerald-500 border-t-transparent rounded-full" />
          <p className="text-slate-400 text-sm animate-pulse">Generating newsletter… this takes 1–2 minutes</p>
        </div>
      )}

      {previewHtml && (
        <div className="bg-terminal-surface border border-terminal-border rounded-xl overflow-hidden flex-1">
          <div className="px-4 py-3 border-b border-terminal-border flex items-center justify-between">
            <p className="text-xs text-slate-400">Newsletter preview — HTML rendered below</p>
            <span className="text-[10px] text-emerald-400">Ready to send</span>
          </div>
          <iframe
            srcDoc={previewHtml}
            className="w-full"
            style={{ height: 'calc(100vh - 220px)', border: 'none' }}
            sandbox="allow-same-origin"
            title="Newsletter Preview"
          />
        </div>
      )}
    </div>
    </div>
  )
}
