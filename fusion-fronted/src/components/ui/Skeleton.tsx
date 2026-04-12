interface Props {
  className?: string
}

export function Skeleton({ className = '' }: Props) {
  return (
    <div
      className={`animate-pulse bg-terminal-muted rounded ${className}`}
    />
  )
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-terminal-surface border border-terminal-border rounded-xl p-4 space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === 0 ? 'w-1/3' : 'w-full'}`} />
      ))}
    </div>
  )
}
