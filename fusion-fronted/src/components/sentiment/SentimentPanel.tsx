import type { SentimentBlock } from '../../types/fusion'
import { SentimentMeter } from './SentimentMeter'
import { SentimentCounts } from './SentimentCounts'
import { HeadlineList } from './HeadlineList'
import { Newspaper } from 'lucide-react'

interface Props {
  sentiment: SentimentBlock | null
}

export function SentimentPanel({ sentiment }: Props) {
  if (!sentiment) {
    return (
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4">
        <div className="flex items-center gap-2 text-slate-500 text-sm">
          <Newspaper className="h-4 w-4" />
          <span>No sentiment data available</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Newspaper className="h-4 w-4 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-200">News Sentiment</h3>
        {sentiment.trading_bias && (
          <span className="ml-auto text-[10px] text-slate-500">
            Bias: <span className="text-slate-300">{sentiment.trading_bias}</span>
            {sentiment.bias_strength && ` (${sentiment.bias_strength})`}
          </span>
        )}
      </div>

      <div className="flex flex-col items-center gap-3">
        <SentimentMeter score={sentiment.overall_score} label={sentiment.overall_sentiment} />
        <SentimentCounts
          positive={sentiment.positive_count}
          negative={sentiment.negative_count}
          neutral={sentiment.neutral_count}
        />
      </div>

      <div className="border-t border-terminal-border pt-3">
        <div className="text-xs text-slate-500 mb-2">
          Recent Headlines ({sentiment.news_count} articles)
        </div>
        <HeadlineList headlines={sentiment.top_headlines} />
      </div>
    </div>
  )
}
