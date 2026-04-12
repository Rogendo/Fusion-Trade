import { useParams } from 'react-router-dom'
import { useFusion } from '../hooks/useFusion'
import { FusionScoreWidget } from '../components/fusion/FusionScoreWidget'
import { TimeframeGrid } from '../components/fusion/TimeframeGrid'
import { TargetsPanel } from '../components/fusion/TargetsPanel'
import { ReasoningBlock } from '../components/fusion/ReasoningBlock'
import { SentimentPanel } from '../components/sentiment/SentimentPanel'
import { LLMAnalysisPanel } from '../components/llm/LLMAnalysisPanel'
import { TradingViewChart } from '../components/chart/TradingViewChart'
import { TopBar } from '../components/layout/TopBar'
import { SkeletonCard } from '../components/ui/Skeleton'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { getLabel } from '../utils/symbolMeta'
import { relativeTime } from '../utils/formatPrice'
import { RefreshCw } from 'lucide-react'

export function AnalysisPage() {
  const { symbol = 'GC=F' } = useParams<{ symbol: string }>()
  const decoded = decodeURIComponent(symbol)
  const { data, isLoading, isError, error, refetch, dataUpdatedAt, isFetching } = useFusion(decoded)

  const lastUpdated = dataUpdatedAt ? relativeTime(new Date(dataUpdatedAt).toISOString()) : null

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <TopBar lastUpdated={lastUpdated} />

      <div className="flex-1 overflow-y-auto">
        {/* Chart — always visible, loads from TradingView directly */}
        <div className="px-4 pt-4">
          <TradingViewChart symbol={decoded} height={420} />
        </div>

        {/* Fusion data panels */}
        <div className="p-4 space-y-4">
          {/* Page header with live refresh indicator */}
          <div className="flex items-center justify-between">
            <h1 className="text-base font-semibold text-slate-200">
              {getLabel(decoded)} Signals
            </h1>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              {isFetching && (
                <RefreshCw className="h-3 w-3 animate-spin text-emerald-500" />
              )}
              {lastUpdated && <span>Updated {lastUpdated}</span>}
            </div>
          </div>

          {/* Error state — non-blocking, shown inline */}
          {isError && (
            <ErrorBanner
              message={(error as any)?.response?.data?.detail ?? 'Failed to load fusion signals.'}
              onRetry={() => refetch()}
            />
          )}

          {/* Loading state — only skeleton cards, no page block */}
          {isLoading && !data && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              <div className="lg:col-span-3 space-y-4">
                <SkeletonCard lines={4} />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <SkeletonCard lines={5} />
                  <SkeletonCard lines={5} />
                  <SkeletonCard lines={5} />
                  <SkeletonCard lines={5} />
                </div>
              </div>
              <div className="lg:col-span-2 space-y-4">
                <SkeletonCard lines={6} />
                <SkeletonCard lines={4} />
              </div>
            </div>
          )}

          {/* Data panels — appear as soon as data arrives */}
          {data && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              {/* Left: 3/5 */}
              <div className="lg:col-span-3 space-y-4">
                <FusionScoreWidget fusion={data} />
                <TimeframeGrid timeframes={data.timeframes} symbol={decoded} />
                <TargetsPanel targets={data.targets} symbol={decoded} />
                <ReasoningBlock reasoning={data.reasoning} logic={data.logic} />
              </div>

              {/* Right: 2/5 */}
              <div className="lg:col-span-2 space-y-4">
                <SentimentPanel sentiment={data.sentiment} />
                <LLMAnalysisPanel symbol={decoded} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
