/**
 * Pagination Component
 *
 * Provides page navigation controls for paginated lists.
 */

import { memo } from 'react'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '../lib/utils'
import { Button } from './ui/button'

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
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-edge-subtle bg-surface-panel px-4 py-3">
      {/* Page size selector */}
      <label className="flex items-center gap-2 text-small text-content-muted">
        <span>Show</span>
        {onPageSizeChange && (
          <select
            value={limit}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            disabled={isLoading}
            className="select w-auto"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        )}
        <span>per page</span>
      </label>

      {/* Item range display */}
      <div className="text-small text-content-muted">
        Showing {startItem}-{endItem} of {total}
      </div>

      {/* Page navigation */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          className="px-1.5"
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1 || isLoading}
          title="First page"
        >
          <ChevronsLeft size={14} aria-hidden="true" />
          <span className="sr-only">First page</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="px-1.5"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || isLoading}
          title="Previous page"
        >
          <ChevronLeft size={14} aria-hidden="true" />
          <span className="sr-only">Previous page</span>
        </Button>

        <div className="mx-1 flex items-center gap-1">
          {visiblePages[0] > 1 && (
            <>
              <PageButton page={1} currentPage={currentPage} isLoading={isLoading} onPageChange={onPageChange} />
              {visiblePages[0] > 2 && <span className="px-1 text-content-muted">...</span>}
            </>
          )}

          {visiblePages.map((page) => (
            <PageButton
              key={page}
              page={page}
              currentPage={currentPage}
              isLoading={isLoading}
              onPageChange={onPageChange}
            />
          ))}

          {visiblePages[visiblePages.length - 1] < totalPages && (
            <>
              {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
                <span className="px-1 text-content-muted">...</span>
              )}
              <PageButton
                page={totalPages}
                currentPage={currentPage}
                isLoading={isLoading}
                onPageChange={onPageChange}
              />
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="px-1.5"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages || isLoading}
          title="Next page"
        >
          <ChevronRight size={14} aria-hidden="true" />
          <span className="sr-only">Next page</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="px-1.5"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages || isLoading}
          title="Last page"
        >
          <ChevronsRight size={14} aria-hidden="true" />
          <span className="sr-only">Last page</span>
        </Button>
      </div>
    </div>
  )
}

function PageButton({
  page,
  currentPage,
  isLoading,
  onPageChange
}: {
  page: number
  currentPage: number
  isLoading: boolean
  onPageChange: (page: number) => void
}): JSX.Element {
  const current = page === currentPage
  return (
    <button
      type="button"
      onClick={() => onPageChange(page)}
      disabled={isLoading}
      aria-current={current ? 'page' : undefined}
      className={cn(
        'min-h-8 min-w-8 rounded-control px-2 text-small font-medium transition-colors disabled:opacity-45',
        current
          ? 'bg-accent-solid text-accent-on-solid'
          : 'text-content-muted hover:bg-surface-raised hover:text-content-primary'
      )}
    >
      {page}
    </button>
  )
}

export default memo(Pagination)
