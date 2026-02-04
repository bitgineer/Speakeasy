/**
 * Pagination Component
 * 
 * Provides page navigation controls for paginated lists.
 */

import { memo } from 'react'

interface PaginationProps {
  currentPage: number
  totalPages: number
  total: number
  limit: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (size: number) => void
  isLoading?: boolean
}

const PAGE_SIZE_OPTIONS = [25, 50, 100]

function Pagination({
  currentPage,
  totalPages,
  total,
  limit,
  onPageChange,
  onPageSizeChange,
  isLoading = false
}: PaginationProps): JSX.Element | null {
  if (total === 0) return null
  
  // Calculate visible page range (show max 5 page buttons)
  const getVisiblePages = (): number[] => {
    const pages: number[] = []
    const maxVisible = 5
    
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
    const end = Math.min(totalPages, start + maxVisible - 1)
    
    // Adjust start if we're near the end
    start = Math.max(1, end - maxVisible + 1)
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    
    return pages
  }
  
  const visiblePages = getVisiblePages()
  const startItem = (currentPage - 1) * limit + 1
  const endItem = Math.min(currentPage * limit, total)
  
  return (
    <div className="flex items-center justify-between py-3 px-4 border-t border-[var(--color-border)] bg-[var(--color-bg-secondary)]">
      {/* Page size selector */}
      <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
        <span>Show</span>
        {onPageSizeChange && (
          <select
            value={limit}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            disabled={isLoading}
            className="px-2 py-1 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded text-[var(--color-text-secondary)] text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
          >
            {PAGE_SIZE_OPTIONS.map(size => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        )}
        <span>per page</span>
      </div>
      
      {/* Item range display */}
      <div className="text-sm text-[var(--color-text-muted)]">
        Showing {startItem}-{endItem} of {total}
      </div>
      
      {/* Page navigation */}
      <div className="flex items-center gap-1">
        {/* First page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1 || isLoading}
          className="p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="First page"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
        
        {/* Previous page */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || isLoading}
          className="p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="Previous page"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        
        {/* Page numbers */}
        <div className="flex items-center gap-1 mx-1">
          {visiblePages[0] > 1 && (
            <>
              <button
                onClick={() => onPageChange(1)}
                disabled={isLoading}
                className="w-8 h-8 rounded text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 transition-colors"
              >
                1
              </button>
              {visiblePages[0] > 2 && (
                <span className="text-[var(--color-text-muted)] px-1">...</span>
              )}
            </>
          )}
          
          {visiblePages.map(page => (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              disabled={isLoading}
              className={`w-8 h-8 rounded text-sm font-medium transition-colors disabled:opacity-40 ${
                page === currentPage
                  ? 'bg-[var(--color-accent)] text-white'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]'
              }`}
            >
              {page}
            </button>
          ))}
          
          {visiblePages[visiblePages.length - 1] < totalPages && (
            <>
              {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
                <span className="text-[var(--color-text-muted)] px-1">...</span>
              )}
              <button
                onClick={() => onPageChange(totalPages)}
                disabled={isLoading}
                className="w-8 h-8 rounded text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 transition-colors"
              >
                {totalPages}
              </button>
            </>
          )}
        </div>
        
        {/* Next page */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages || isLoading}
          className="p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="Next page"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        
        {/* Last page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages || isLoading}
          className="p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="Last page"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default memo(Pagination)
