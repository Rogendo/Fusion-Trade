import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useJournal } from '../hooks/useJournal'
import { triggerVerification } from '../api/journal'
import { StatsBar } from '../components/journal/StatsBar'
import { JournalTable } from '../components/journal/JournalTable'
import { SkeletonCard } from '../components/ui/Skeleton'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Button } from '../components/ui/Button'
import { BookOpen, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

type StatusFilter = '' | 'PENDING' | 'TP1_HIT' | 'TP2_HIT' | 'SL_HIT' | 'EXPIRED'

const STATUS_TABS: { label: string; value: StatusFilter }[] = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'TP Hit', value: 'TP1_HIT' },
  { label: 'SL Hit', value: 'SL_HIT' },
  { label: 'Expired', value: 'EXPIRED' },
]

export function JournalPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')
  const queryClient = useQueryClient()

  const { data, isLoading, isError, refetch } = useJournal(
    page,
    undefined,
    statusFilter || undefined,
  )

  const verifyMutation = useMutation({
    mutationFn: triggerVerification,
    onSuccess: (data) => {
      const count = data?.result?.verified ?? '?'
      toast.success(`Verification complete — checked ${count} pending entries.`)
      queryClient.invalidateQueries({ queryKey: ['journal'] })
    },
    onError: () => toast.error('Failed to run verification.'),
  })

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1

  const handleTabChange = (val: StatusFilter) => {
    setStatusFilter(val)
    setPage(1)
  }

  return (
    <div className="flex flex-col flex-1 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-slate-400" />
          <h1 className="text-base font-semibold text-slate-200">Trading Journal</h1>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => verifyMutation.mutate()}
          loading={verifyMutation.isPending}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Verify Pending Now
        </Button>
      </div>

      {/* Explanation banner */}
      <div className="text-xs text-slate-500 bg-terminal-surface border border-terminal-border rounded-lg px-4 py-3 space-y-1">
        <p className="font-medium text-slate-400">How verification works</p>
        <p>Predictions start as <span className="text-amber-400">Pending</span>. Every 15 minutes, the verification worker fetches live prices and checks if TP1 or SL was hit candle-by-candle since the signal was generated. Entries older than 7 days without a hit are marked <span className="text-slate-500">Expired</span>. Click "Verify Pending Now" to run it immediately.</p>
      </div>

      {isLoading && <SkeletonCard lines={6} />}
      {isError && <ErrorBanner message="Failed to load journal." onRetry={() => refetch()} />}

      {data && (
        <>
          {/* Stats */}
          <StatsBar stats={data.stats} />

          {/* Status filter tabs */}
          <div className="flex gap-1 flex-wrap">
            {STATUS_TABS.map(tab => (
              <button
                key={tab.value}
                onClick={() => handleTabChange(tab.value)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  statusFilter === tab.value
                    ? 'bg-terminal-muted text-slate-200 border border-terminal-border'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-terminal-muted/50'
                }`}
              >
                {tab.label}
                {tab.value === '' && (
                  <span className="ml-1.5 text-slate-600">{data.total}</span>
                )}
                {tab.value === 'PENDING' && (
                  <span className="ml-1.5 text-amber-500">{data.stats.pending}</span>
                )}
              </button>
            ))}
          </div>

          {/* Table */}
          <JournalTable entries={data.entries} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-xs text-slate-400">
                Page {page} of {totalPages} &nbsp;·&nbsp; {data.total} entries
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
