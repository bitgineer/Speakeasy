import React from 'react'

interface HistoryItemSkeletonProps {
  className?: string
}

export default function HistoryItemSkeleton({ className = '' }: HistoryItemSkeletonProps): JSX.Element {
  return (
    <div className={`card p-4 ${className}`}>
      {/* Header with metadata skeleton */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          {/* Date/Time placeholder */}
          <div className="h-4 w-24 bg-gray-700 rounded animate-pulse" />
          
          {/* Separator placeholder */}
          <div className="h-4 w-1 bg-gray-700 rounded animate-pulse" />
          
          {/* Duration placeholder */}
          <div className="h-4 w-12 bg-gray-700 rounded animate-pulse" />
          
          {/* Optional badge placeholder */}
          <div className="h-4 w-16 bg-gray-700 rounded animate-pulse hidden sm:block" />
        </div>
        
        {/* Actions skeleton */}
        <div className="flex items-center gap-1">
          {/* Copy button placeholder */}
          <div className="w-7 h-7 bg-gray-700 rounded animate-pulse" />
          {/* Delete button placeholder */}
          <div className="w-7 h-7 bg-gray-700 rounded animate-pulse" />
        </div>
      </div>
      
      {/* Text content skeleton */}
      <div className="space-y-2 mt-3">
        <div className="h-4 bg-gray-700 rounded animate-pulse w-full" />
        <div className="h-4 bg-gray-700 rounded animate-pulse w-[85%]" />
        <div className="h-4 bg-gray-700 rounded animate-pulse w-[60%]" />
      </div>
    </div>
  )
}
