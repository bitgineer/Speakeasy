interface HistoryItemSkeletonProps {
  className?: string
}

export default function HistoryItemSkeleton({ className = '' }: HistoryItemSkeletonProps): JSX.Element {
  return (
    <div className={`card record ${className}`}>
      {/* Header with metadata skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Date/Time placeholder */}
          <div className="h-4 w-24 animate-pulse rounded-control bg-surface-hover" />

          {/* Duration placeholder */}
          <div className="h-4 w-12 animate-pulse rounded-control bg-surface-hover" />

          {/* Optional badge placeholder */}
          <div className="hidden h-4 w-16 animate-pulse rounded-control bg-surface-hover sm:block" />
        </div>

        {/* Actions skeleton */}
        <div className="flex items-center gap-1">
          {/* Copy button placeholder */}
          <div className="h-7 w-7 animate-pulse rounded-control bg-surface-hover" />
          {/* Delete button placeholder */}
          <div className="h-7 w-7 animate-pulse rounded-control bg-surface-hover" />
        </div>
      </div>

      {/* Text content skeleton */}
      <div className="mt-3 space-y-2">
        <div className="h-4 w-full animate-pulse rounded-control bg-surface-hover" />
        <div className="h-4 w-4/5 animate-pulse rounded-control bg-surface-hover" />
      </div>
    </div>
  )
}
