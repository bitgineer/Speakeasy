/**
 * Dashboard Page
 *
 * Main page showing transcription history with search functionality.
 */

import { useEffect, useCallback, useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Download, X } from "lucide-react";
import { useHistoryStore, useAppStore } from "../store";
import HistoryItem from "../components/HistoryItem";
import HistoryItemSkeleton from "../components/HistoryItemSkeleton";
import ExportDialog from "../components/ExportDialog";
import Pagination from "../components/Pagination";
import ModelLoadingBanner from "../components/ModelLoadingBanner";
import ModeChips from "../components/ModeChips";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { perfMonitor } from "../utils/performance";

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
    clearError,
  } = useHistoryStore();

  const { modelLoading, modelName } = useAppStore();

  const searchInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);

  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => 128, // Estimate height including gap
    overscan: 5,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "e") {
        e.preventDefault();
        setShowExportDialog(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Cleanup debounce timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Initial fetch
  useEffect(() => {
    perfMonitor.markStart("history-fetch");
    fetchHistory().finally(() => {
      perfMonitor.markEnd("history-fetch");
    });
  }, [fetchHistory]);

  // Search handler with debounce
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      // Update search query immediately for UI feedback
      useHistoryStore.setState({ searchQuery: value });

      // Cancel pending debounce
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }

      // Set searching state
      setIsSearching(true);

      // Debounce the actual search query trigger
      debounceTimeoutRef.current = setTimeout(async () => {
        try {
          perfMonitor.markStart("search-query");
          await search(value);
          perfMonitor.markEnd("search-query");
        } finally {
          setIsSearching(false);
        }
      }, 300);
    },
    [search],
  );

  const handleSearchSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      // Cancel pending debounce and execute immediately
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      setIsSearching(true);
      try {
        perfMonitor.markStart("search-submit");
        await search(searchQuery);
        perfMonitor.markEnd("search-submit");
      } finally {
        setIsSearching(false);
      }
    },
    [search, searchQuery],
  );

  const handleSearchClear = useCallback(() => {
    // Cancel pending debounce and clear immediately
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    useHistoryStore.setState({ searchQuery: "" });
    void search("");
    setIsSearching(false);
  }, [search]);

  // Delete handler
  const handleDelete = useCallback(
    async (id: string) => {
      await deleteItem(id);
    },
    [deleteItem],
  );

  return (
    <div className="workspace workspace-dashboard">
      <header className="page-head">
        <div>
          <p className="eyebrow">Capture / review</p>
          <h1>Transcription history</h1>
          <p className="page-subtitle">Your recent voice work, ready to search and reuse.</p>
        </div>
        <div className="page-actions">
          {total > 0 && (
            <span className="pill">
              {total} transcription{total !== 1 ? "s" : ""}
            </span>
          )}
          <Button
            variant="secondary"
            onClick={() => setShowExportDialog(true)}
            title="Export history (Ctrl+E)"
          >
            <Download size={14} aria-hidden="true" />
            Export history
          </Button>
        </div>
      </header>

      <div className="toolbar">
        <ModeChips />
        <span className="muted">Sorted newest first</span>
      </div>

      <form className="search-row" role="search" onSubmit={handleSearchSubmit}>
        <Input
          ref={searchInputRef}
          type="search"
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search transcriptions"
          aria-label="Search transcriptions"
        />
        {searchQuery && (
          <Button type="button" variant="ghost" onClick={handleSearchClear} title="Clear search">
            Clear
          </Button>
        )}
        <Button type="submit" variant="secondary">
          Search
        </Button>
      </form>

      {isSearching && <p className="search-status">Searching...</p>}

      {/* Model Loading Banner */}
      {modelLoading && (
        <div className="mb-3">
          <ModelLoadingBanner modelName={modelName} />
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button type="button" onClick={clearError} title="Dismiss error" aria-label="Dismiss error">
            <X size={14} aria-hidden="true" />
          </button>
        </div>
      )}

      <section aria-labelledby="history-title">
        <div className="section-bar">
          <h2 id="history-title">Recent records</h2>
          <span>{items.length > 0 ? `Showing ${items.length} of ${total}` : ""}</span>
        </div>

        <div ref={listRef} className="record-list">
          {isLoading ? (
            // Loading skeleton
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <HistoryItemSkeleton key={i} />
              ))}
            </div>
          ) : items.length === 0 ? (
            // Empty state
            <div className="empty-state">
              <h3>{searchQuery ? "No results found" : "No transcriptions yet"}</h3>
              <p>
                {searchQuery
                  ? "No transcriptions match your search. Try a different word."
                  : "Press your hotkey to start recording. Transcriptions land here, ready to copy and export."}
              </p>
            </div>
          ) : (
            // History items
            <div
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: "100%",
                position: "relative",
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualItem) => (
                <div
                  key={virtualItem.key}
                  data-index={virtualItem.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${virtualItem.start}px)`,
                    paddingBottom: "var(--space-3)",
                  }}
                >
                  <HistoryItem
                    item={items[virtualItem.index]}
                    onDelete={handleDelete}
                    index={virtualItem.index}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

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
  );
}
