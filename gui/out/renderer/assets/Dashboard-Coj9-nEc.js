import { j as jsxRuntimeExports, u as useHistoryStore, a as useAppStore, p as perfMonitor } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
import { u as useVirtualizer } from "./tanstack-DLTSNxug.js";
import { E as ExportDialog } from "./ExportDialog-B_ehTTyr.js";
function formatDuration(ms) {
  const seconds = Math.floor(ms / 1e3);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}
function formatDate(dateString) {
  const date = new Date(dateString);
  const now = /* @__PURE__ */ new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const recordDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffTime = today.getTime() - recordDate.getTime();
  const diffDays = Math.floor(diffTime / (1e3 * 60 * 60 * 24));
  if (diffDays === 0) {
    return date.toLocaleTimeString(void 0, {
      hour: "2-digit",
      minute: "2-digit"
    });
  } else if (diffDays === 1) {
    return "Yesterday";
  } else if (diffDays < 7 && diffDays > 0) {
    return date.toLocaleDateString(void 0, { weekday: "long" });
  } else {
    return date.toLocaleDateString(void 0, {
      month: "short",
      day: "numeric",
      year: diffDays > 365 ? "numeric" : void 0
    });
  }
}
function HistoryItem({ item, onDelete }) {
  const [copied, setCopied] = reactExports.useState(false);
  const [isDeleting, setIsDeleting] = reactExports.useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = reactExports.useState(false);
  const [showExportDialog, setShowExportDialog] = reactExports.useState(false);
  const [showOriginal, setShowOriginal] = reactExports.useState(false);
  const isAiEnhanced = item.is_ai_enhanced || item.original_text && item.original_text !== item.text;
  const displayText = showOriginal && item.original_text ? item.original_text : item.text;
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(displayText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2e3);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };
  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(item.id);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `card p-4 hover:bg-[var(--color-bg-elevated)] transition-colors group transition-opacity duration-200 ${isDeleting ? "opacity-50 pointer-events-none" : ""}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 text-sm text-[var(--color-text-muted)]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { title: new Date(item.created_at).toLocaleString(), children: formatDate(item.created_at) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-border-strong)]", children: "|" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: formatDuration(item.duration_ms) }),
        item.model_used && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-border-strong)]", children: "|" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "badge-gray", children: item.model_used })
        ] }),
        item.language && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-border-strong)]", children: "|" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "badge-blue", children: item.language.toUpperCase() })
        ] }),
        isAiEnhanced && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-border-strong)]", children: "|" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              onClick: () => setShowOriginal(!showOriginal),
              className: `inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium transition-colors ${showOriginal ? "bg-gray-500/20 text-gray-400 hover:bg-gray-500/30" : "bg-purple-500/20 text-purple-400 hover:bg-purple-500/30"}`,
              title: showOriginal ? "Click to show AI-enhanced text" : "Click to show original text",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-3 h-3", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" }) }),
                showOriginal ? "Original" : "AI Enhanced"
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: () => setShowExportDialog(true),
            className: "p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] rounded transition-colors",
            title: "Export",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" }) })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: handleCopy,
            className: "p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] rounded transition-colors",
            title: copied ? "Copied!" : "Copy to clipboard",
            children: copied ? /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-success)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" }) })
          }
        ),
        isDeleting ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-[var(--color-error)] px-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { className: "animate-spin h-4 w-4", xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { className: "opacity-25", cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("path", { className: "opacity-75", fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs font-medium", children: "Deleting..." })
        ] }) : showDeleteConfirm ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: handleDelete,
              className: "p-1.5 text-[var(--color-error)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-muted)] rounded transition-colors",
              title: "Confirm delete",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: () => setShowDeleteConfirm(false),
              className: "p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] rounded transition-colors",
              title: "Cancel",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
            }
          )
        ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: () => setShowDeleteConfirm(true),
            className: "p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-[var(--color-bg-tertiary)] rounded transition-colors",
            title: "Delete",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" }) })
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-[var(--color-text-primary)] whitespace-pre-wrap break-words leading-relaxed", children: displayText }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      ExportDialog,
      {
        isOpen: showExportDialog,
        onClose: () => setShowExportDialog(false),
        singleRecordId: item.id
      }
    )
  ] });
}
const HistoryItem$1 = reactExports.memo(HistoryItem);
function HistoryItemSkeleton({ className = "" }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `card p-4 ${className}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 w-24 bg-gray-700 rounded animate-pulse" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 w-1 bg-gray-700 rounded animate-pulse" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 w-12 bg-gray-700 rounded animate-pulse" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 w-16 bg-gray-700 rounded animate-pulse hidden sm:block" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-7 h-7 bg-gray-700 rounded animate-pulse" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-7 h-7 bg-gray-700 rounded animate-pulse" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2 mt-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 bg-gray-700 rounded animate-pulse w-full" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 bg-gray-700 rounded animate-pulse w-[85%]" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-4 bg-gray-700 rounded animate-pulse w-[60%]" })
    ] })
  ] });
}
const PAGE_SIZE_OPTIONS = [25, 50, 100];
function Pagination({
  currentPage,
  totalPages,
  total,
  limit,
  onPageChange,
  onPageSizeChange,
  isLoading = false
}) {
  if (total === 0) return null;
  const getVisiblePages = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    const end = Math.min(totalPages, start + maxVisible - 1);
    start = Math.max(1, end - maxVisible + 1);
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };
  const visiblePages = getVisiblePages();
  const startItem = (currentPage - 1) * limit + 1;
  const endItem = Math.min(currentPage * limit, total);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-3 px-4 border-t border-[var(--color-border)] bg-[var(--color-bg-secondary)]", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-sm text-[var(--color-text-muted)]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Show" }),
      onPageSizeChange && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "select",
        {
          value: limit,
          onChange: (e) => onPageSizeChange(Number(e.target.value)),
          disabled: isLoading,
          className: "px-2 py-1 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded text-[var(--color-text-secondary)] text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]",
          children: PAGE_SIZE_OPTIONS.map((size) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: size, children: size }, size))
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "per page" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm text-[var(--color-text-muted)]", children: [
      "Showing ",
      startItem,
      "-",
      endItem,
      " of ",
      total
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: () => onPageChange(1),
          disabled: currentPage === 1 || isLoading,
          className: "p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors",
          title: "First page",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M11 19l-7-7 7-7m8 14l-7-7 7-7" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: () => onPageChange(currentPage - 1),
          disabled: currentPage === 1 || isLoading,
          className: "p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors",
          title: "Previous page",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M15 19l-7-7 7-7" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1 mx-1", children: [
        visiblePages[0] > 1 && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: () => onPageChange(1),
              disabled: isLoading,
              className: "w-8 h-8 rounded text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 transition-colors",
              children: "1"
            }
          ),
          visiblePages[0] > 2 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-muted)] px-1", children: "..." })
        ] }),
        visiblePages.map((page) => /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: () => onPageChange(page),
            disabled: isLoading,
            className: `w-8 h-8 rounded text-sm font-medium transition-colors disabled:opacity-40 ${page === currentPage ? "bg-[var(--color-accent)] text-white" : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)]"}`,
            children: page
          },
          page
        )),
        visiblePages[visiblePages.length - 1] < totalPages && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          visiblePages[visiblePages.length - 1] < totalPages - 1 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-muted)] px-1", children: "..." }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: () => onPageChange(totalPages),
              disabled: isLoading,
              className: "w-8 h-8 rounded text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 transition-colors",
              children: totalPages
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: () => onPageChange(currentPage + 1),
          disabled: currentPage === totalPages || isLoading,
          className: "p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors",
          title: "Next page",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 5l7 7-7 7" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: () => onPageChange(totalPages),
          disabled: currentPage === totalPages || isLoading,
          className: "p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-tertiary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors",
          title: "Last page",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M13 5l7 7-7 7M5 5l7 7-7 7" }) })
        }
      )
    ] })
  ] });
}
const Pagination$1 = reactExports.memo(Pagination);
function Dashboard() {
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
  } = useHistoryStore();
  const { isRecording, modelLoaded, modelName } = useAppStore();
  const searchInputRef = reactExports.useRef(null);
  const listRef = reactExports.useRef(null);
  const debounceTimeoutRef = reactExports.useRef(null);
  const [isSearching, setIsSearching] = reactExports.useState(false);
  const [showExportDialog, setShowExportDialog] = reactExports.useState(false);
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => 150,
    // Estimate height including gap
    overscan: 5
  });
  reactExports.useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "e") {
        e.preventDefault();
        setShowExportDialog(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);
  reactExports.useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);
  reactExports.useEffect(() => {
    perfMonitor.markStart("history-fetch");
    fetchHistory().finally(() => {
      perfMonitor.markEnd("history-fetch");
    });
  }, [fetchHistory]);
  const handleSearchChange = reactExports.useCallback((e) => {
    const value = e.target.value;
    useHistoryStore.setState({ searchQuery: value });
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    setIsSearching(true);
    debounceTimeoutRef.current = setTimeout(async () => {
      try {
        perfMonitor.markStart("search-query");
        await search(value);
        perfMonitor.markEnd("search-query");
      } finally {
        setIsSearching(false);
      }
    }, 300);
  }, [search]);
  const handleSearchSubmit = reactExports.useCallback(async (e) => {
    e.preventDefault();
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
  }, [search, searchQuery]);
  const handleDelete = reactExports.useCallback(async (id) => {
    await deleteItem(id);
  }, [deleteItem]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-full flex flex-col", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "px-4 py-3 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border)] flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center gap-4", children: isRecording ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-[var(--color-recording)]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 rounded-full bg-[var(--color-recording)] animate-pulse" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium", children: "Recording..." })
      ] }) : modelLoaded ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-[var(--color-success)]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 rounded-full bg-[var(--color-success)]" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm", children: "Ready" }),
        modelName && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs text-[var(--color-text-muted)]", children: [
          "(",
          modelName,
          ")"
        ] })
      ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-[var(--color-warning)]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 rounded-full bg-[var(--color-warning)]" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm", children: "No model loaded" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-[var(--color-text-muted)]", children: total > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          total,
          " transcription",
          total !== 1 ? "s" : ""
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            onClick: () => setShowExportDialog(true),
            className: "flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)]",
            title: "Export history (Ctrl+E)",
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Export" })
            ]
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "px-4 py-3 border-b border-[var(--color-border)]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSearchSubmit, className: "relative", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            ref: searchInputRef,
            type: "text",
            value: searchQuery,
            onChange: handleSearchChange,
            placeholder: "Search transcriptions...",
            className: "input pl-10 pr-4"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "svg",
          {
            className: "absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]",
            fill: "none",
            stroke: "currentColor",
            viewBox: "0 0 24 24",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" })
          }
        ),
        searchQuery && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            onClick: () => {
              if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
              }
              useHistoryStore.setState({ searchQuery: "" });
              search("");
              setIsSearching(false);
            },
            className: "absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
          }
        )
      ] }),
      isSearching && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2 flex items-center gap-2 text-sm text-[var(--color-text-muted)] px-1", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Searching..." })
      ] })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mx-4 mt-4 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-error)] text-sm", children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: clearError,
          className: "text-[var(--color-error)] hover:opacity-80",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: listRef,
        className: "flex-1 overflow-auto px-4 py-4",
        children: isLoading ? (
          // Loading skeleton
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-4", children: [...Array(5)].map((_, i) => /* @__PURE__ */ jsxRuntimeExports.jsx(HistoryItemSkeleton, {}, i)) })
        ) : items.length === 0 ? (
          // Empty state
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center justify-center h-full text-center", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-16 mb-4 text-[var(--color-text-disabled)]", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" }) }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-[var(--color-text-secondary)] mb-1", children: searchQuery ? "No results found" : "No transcriptions yet" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-[var(--color-text-muted)] text-sm max-w-xs", children: searchQuery ? "Try a different search term" : "Press your hotkey to start recording. Your transcriptions will appear here." })
          ] })
        ) : (
          // History items
          /* @__PURE__ */ jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              style: {
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: "100%",
                position: "relative"
              },
              children: rowVirtualizer.getVirtualItems().map((virtualItem) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                "div",
                {
                  "data-index": virtualItem.index,
                  ref: rowVirtualizer.measureElement,
                  style: {
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${virtualItem.start}px)`,
                    paddingBottom: "0.75rem"
                    // Equivalent to space-y-3 gap
                  },
                  children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                    HistoryItem$1,
                    {
                      item: items[virtualItem.index],
                      onDelete: handleDelete
                    }
                  )
                },
                virtualItem.key
              ))
            }
          ) })
        )
      }
    ),
    !isLoading && items.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(
      Pagination$1,
      {
        currentPage,
        totalPages,
        total,
        limit,
        onPageChange: goToPage,
        onPageSizeChange: setPageSize,
        isLoading
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      ExportDialog,
      {
        isOpen: showExportDialog,
        onClose: () => setShowExportDialog(false)
      }
    )
  ] });
}
export {
  Dashboard as default
};
