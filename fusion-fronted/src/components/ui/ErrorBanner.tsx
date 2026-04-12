import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  message?: string
  onRetry?: () => void
}

export function ErrorBanner({ message = 'Something went wrong.', onRetry }: Props) {
  return (
    <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-rose-400">
      <AlertTriangle className="h-5 w-5 shrink-0" />
      <span className="text-sm flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-xs hover:text-rose-300 transition-colors"
        >
          <RefreshCw className="h-3 w-3" /> Retry
        </button>
      )}
    </div>
  )
}
