import { useState } from 'react'
import { useJournal } from '../hooks/useJournal'
import { StatsBar } from '../components/journal/StatsBar'
import { JournalTable } from '../components/journal/JournalTable'
import { SkeletonCard } from '../components/ui/Skeleton'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { Button } from '../components/ui/Button'
import { BookOpen, ChevronLeft, ChevronRight } from 'lucide-react'

export function JournalPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError, refetch } = useJournal(page)

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1

  return (
    <div className="flex-1 overflow-y-auto">
    <div className="p-6 space-y-4 max-w-7xl mx-auto">
      <div className="flex items-center gap-2">
        <BookOpen className="h-5 w-5 text-slate-400" />
        <h1 className="text-base font-semibold text-slate-200">Trading Journal</h1>
      </div>

      {isLoading && <SkeletonCard lines={6} />}

      {isError && (
        <ErrorBanner message="Failed to load journal." onRetry={() => refetch()} />
      )}

      {data && (
        <>
          <StatsBar stats={data.stats} />
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
                Page {page} of {totalPages}
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
    </div>
  )
}
