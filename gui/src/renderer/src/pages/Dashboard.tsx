/**
 * Dashboard Page
 * 
 * Main page showing transcription history with search functionality.
 */

import { useEffect, useCallback, useRef, useState } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { useHistoryStore, useAppStore } from '../store'
import HistoryItem from '../components/HistoryItem'
import HistoryItemSkeleton from '../components/HistoryItemSkeleton'
import ExportDialog from '../components/ExportDialog'
import Pagination from '../components/Pagination'
import { perfMonitor } from '../utils/performance'

export default function Dashboard(): JSX.Element {
  const { 
    items, 
    total, 
    limit,
    currentPage,
    totalPages,
    searchQuery, 
    isLoading, 
    error,
    fetchHistory,
    goToPage,
    setPageSize,
    search,
    deleteItem,
    clearError
  } = useHistoryStore()
  
  const { isRecording, modelLoaded, modelName } = useAppStore()
  
  const searchInputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)

  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => 150, // Estimate height including gap
    overscan: 5,
  })
  
   useEffect(() => {
     const handleKeyDown = (e: KeyboardEvent) => {
       if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
         e.preventDefault()
         setShowExportDialog(true)
       }
     }
     window.addEventListener('keydown', handleKeyDown)
     return () => window.removeEventListener('keydown', handleKeyDown)
   }, [])
   
   // Cleanup debounce timeout on unmount
   useEffect(() => {
     return () => {
       if (debounceTimeoutRef.current) {
         clearTimeout(debounceTimeoutRef.current)
       }
     }
   }, [])
  
   // Initial fetch
   useEffect(() => {
     perfMonitor.markStart('history-fetch')
     fetchHistory().finally(() => {
       perfMonitor.markEnd('history-fetch')
     })
   }, [fetchHistory])
  
   // Search handler with debounce
   const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
     const value = e.target.value
     // Update search query immediately for UI feedback
     useHistoryStore.setState({ searchQuery: value })
     
     // Cancel pending debounce
     if (debounceTimeoutRef.current) {
       clearTimeout(debounceTimeoutRef.current)
     }
     
     // Set searching state
     setIsSearching(true)
     
      // Debounce the actual search query trigger
      debounceTimeoutRef.current = setTimeout(async () => {
        try {
          perfMonitor.markStart('search-query')
          await search(value)
          perfMonitor.markEnd('search-query')
        } finally {
          setIsSearching(false)
        }
      }, 300)
   }, [search])
   
    const handleSearchSubmit = useCallback(async (e: React.FormEvent) => {
      e.preventDefault()
      // Cancel pending debounce and execute immediately
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
      setIsSearching(true)
      try {
        perfMonitor.markStart('search-submit')
        await search(searchQuery)
        perfMonitor.markEnd('search-submit')
      } finally {
        setIsSearching(false)
      }
    }, [search, searchQuery])
  
  // Delete handler
  const handleDelete = useCallback(async (id: string) => {
    await deleteItem(id)
  }, [deleteItem])
  
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Recording status */}
          {isRecording ? (
            <div className="flex items-center gap-2 text-[var(--color-recording)]">
              <div className="w-2 h-2 rounded-full bg-[var(--color-recording)] animate-pulse" />
              <span className="text-sm font-medium">Recording...</span>
            </div>
          ) : modelLoaded ? (
            <div className="flex items-center gap-2 text-[var(--color-success)]">
              <div className="w-2 h-2 rounded-full bg-[var(--color-success)]" />
              <span className="text-sm">Ready</span>
              {modelName && (
                <span className="text-xs text-[var(--color-text-muted)]">({modelName})</span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-[var(--color-warning)]">
              <div className="w-2 h-2 rounded-full bg-[var(--color-warning)]" />
              <span className="text-sm">No model loaded</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-sm text-[var(--color-text-muted)]">
            {total > 0 && (
              <span>{total} transcription{total !== 1 ? 's' : ''}</span>
            )}
          </div>
          <button
            onClick={() => setShowExportDialog(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)]"
            title="Export history (Ctrl+E)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Export</span>
          </button>
        </div>
      </div>
      
      {/* Search bar */}
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <form onSubmit={handleSearchSubmit} className="relative">
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search transcriptions..."
            className="input pl-10 pr-4"
          />
          <svg 
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
           {searchQuery && (
             <button
               type="button"
               onClick={() => {
                 // Cancel pending debounce and clear immediately
                 if (debounceTimeoutRef.current) {
                   clearTimeout(debounceTimeoutRef.current)
                 }
                 useHistoryStore.setState({ searchQuery: '' })
                 search('')
                 setIsSearching(false)
               }}
               className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
             >
               <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
               </svg>
             </button>
           )}
        </form>
        {isSearching && (
          <div className="mt-2 flex items-center gap-2 text-sm text-[var(--color-text-muted)] px-1">
            <div className="w-3 h-3 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" />
            <span>Searching...</span>
          </div>
        )}
      </div>
      
      {/* Error message */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between">
          <span className="text-[var(--color-error)] text-sm">{error}</span>
          <button
            onClick={clearError}
            className="text-[var(--color-error)] hover:opacity-80"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      
      {/* History list */}
      <div 
        ref={listRef}
        className="flex-1 overflow-auto px-4 py-4"
      >
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <HistoryItemSkeleton key={i} />
            ))}
          </div>
        ) : items.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 mb-4 text-[var(--color-text-disabled)]">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-[var(--color-text-secondary)] mb-1">
              {searchQuery ? 'No results found' : 'No transcriptions yet'}
            </h3>
            <p className="text-[var(--color-text-muted)] text-sm max-w-xs">
              {searchQuery 
                ? 'Try a different search term'
                : 'Press your hotkey to start recording. Your transcriptions will appear here.'
              }
            </p>
          </div>
        ) : (
          // History items
          <>
            <div 
              style={{ 
                height: `${rowVirtualizer.getTotalSize()}px`, 
                width: '100%', 
                position: 'relative' 
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualItem) => (
                <div
                  key={virtualItem.key}
                  data-index={virtualItem.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualItem.start}px)`,
                    paddingBottom: '0.75rem', // Equivalent to space-y-3 gap
                  }}
                >
                  <HistoryItem 
                    item={items[virtualItem.index]} 
                    onDelete={handleDelete}
                  />
                </div>
              ))}
            </div>
          </>
        )}
      </div>
      
      {/* Pagination controls */}
      {!isLoading && items.length > 0 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          total={total}
          limit={limit}
          onPageChange={goToPage}
          onPageSizeChange={setPageSize}
          isLoading={isLoading}
        />
      )}
      
      <ExportDialog 
        isOpen={showExportDialog} 
        onClose={() => setShowExportDialog(false)} 
      />
    </div>
  )
}
