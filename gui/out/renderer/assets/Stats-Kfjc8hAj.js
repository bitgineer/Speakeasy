import { u as useHistoryStore, j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
function StatCard({ title, value, subtitle, icon, color = "accent" }) {
  const colorClasses = {
    accent: "text-[var(--color-accent)]",
    success: "text-[var(--color-success)]",
    warning: "text-[var(--color-warning)]",
    info: "text-[var(--color-info)]"
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "card p-5", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] font-medium", children: title }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: `text-3xl font-bold mt-2 ${colorClasses[color]}`, children: value }),
      subtitle && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-1", children: subtitle })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `p-3 rounded-lg bg-[var(--color-bg-tertiary)] ${colorClasses[color]}`, children: icon })
  ] }) });
}
function formatDuration(ms) {
  if (ms === 0) return "0s";
  const seconds = Math.floor(ms / 1e3);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) {
    return `${days}d ${hours % 24}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}
function formatDate(dateString) {
  if (!dateString) return "Never";
  const date = new Date(dateString);
  return date.toLocaleDateString(void 0, {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}
function Stats() {
  const { stats, items, fetchStats, fetchHistory, isLoading } = useHistoryStore();
  const [refreshing, setRefreshing] = reactExports.useState(false);
  reactExports.useEffect(() => {
    fetchStats();
    fetchHistory();
  }, [fetchStats, fetchHistory]);
  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchStats(), fetchHistory()]);
    setRefreshing(false);
  };
  const extendedStats = reactExports.useMemo(() => {
    if (!items.length) {
      return {
        totalWords: 0,
        avgWordsPerTranscription: 0,
        avgDuration: 0,
        longestTranscription: null,
        shortestTranscription: null
      };
    }
    const totalWords = items.reduce((acc, item) => {
      return acc + item.text.split(/\s+/).filter(Boolean).length;
    }, 0);
    const avgWordsPerTranscription = Math.round(totalWords / items.length);
    const totalDuration = items.reduce((acc, item) => acc + item.duration_ms, 0);
    const avgDuration = Math.round(totalDuration / items.length);
    const sortedByLength = [...items].sort((a, b) => b.text.length - a.text.length);
    const longestTranscription = sortedByLength[0] || null;
    const shortestTranscription = sortedByLength[sortedByLength.length - 1] || null;
    return {
      totalWords,
      avgWordsPerTranscription,
      avgDuration,
      longestTranscription,
      shortestTranscription
    };
  }, [items]);
  if (isLoading && !stats) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-4xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Statistics" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Overview of your transcription activity" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          onClick: handleRefresh,
          disabled: refreshing,
          className: "flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)] disabled:opacity-50",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "svg",
              {
                className: `w-4 h-4 ${refreshing ? "animate-spin" : ""}`,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" })
              }
            ),
            refreshing ? "Refreshing..." : "Refresh"
          ]
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Total Transcriptions",
          value: stats?.total_count ?? 0,
          subtitle: "All time",
          color: "accent",
          icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Total Recording Time",
          value: formatDuration(stats?.total_duration_ms ?? 0),
          subtitle: "Combined duration",
          color: "success",
          icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Words Transcribed",
          value: extendedStats.totalWords.toLocaleString(),
          subtitle: `~${extendedStats.avgWordsPerTranscription} per transcription`,
          color: "info",
          icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" }) })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        StatCard,
        {
          title: "Avg. Duration",
          value: formatDuration(extendedStats.avgDuration),
          subtitle: "Per transcription",
          color: "warning",
          icon: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M13 10V3L4 14h7v7l9-11h-7z" }) })
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-6 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-5", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Recent Activity" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2 border-b border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-[var(--color-text-secondary)]", children: "Today" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg font-semibold text-[var(--color-accent)]", children: stats?.today_count ?? 0 })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2 border-b border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-[var(--color-text-secondary)]", children: "This Week" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg font-semibold text-[var(--color-accent)]", children: stats?.this_week_count ?? 0 })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-[var(--color-text-secondary)]", children: "This Month" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg font-semibold text-[var(--color-accent)]", children: stats?.this_month_count ?? 0 })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-5", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Timeline" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 rounded-full bg-[var(--color-success-muted)] flex items-center justify-center flex-shrink-0", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-success)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" }) }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm font-medium text-[var(--color-text-secondary)]", children: "First Transcription" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)]", children: formatDate(stats?.first_transcription ?? null) })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 rounded-full bg-[var(--color-info-muted)] flex items-center justify-center flex-shrink-0", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-info)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm font-medium text-[var(--color-text-secondary)]", children: "Latest Transcription" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)]", children: formatDate(stats?.last_transcription ?? null) })
            ] })
          ] })
        ] })
      ] })
    ] }),
    (extendedStats.longestTranscription || extendedStats.shortestTranscription) && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-5", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Records" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-4", children: [
        extendedStats.longestTranscription && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-[var(--color-bg-tertiary)] rounded-lg p-4 border border-[var(--color-border)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-success)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 10l7-7m0 0l7 7m-7-7v18" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-[var(--color-text-secondary)]", children: "Longest Transcription" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-[var(--color-success)]", children: [
            extendedStats.longestTranscription.text.split(/\s+/).filter(Boolean).length,
            " words"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2", children: [
            '"',
            extendedStats.longestTranscription.text.slice(0, 100),
            '..."'
          ] })
        ] }),
        extendedStats.shortestTranscription && extendedStats.shortestTranscription !== extendedStats.longestTranscription && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-[var(--color-bg-tertiary)] rounded-lg p-4 border border-[var(--color-border)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-warning)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 14l-7 7m0 0l-7-7m7 7V3" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-[var(--color-text-secondary)]", children: "Shortest Transcription" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-[var(--color-warning)]", children: [
            extendedStats.shortestTranscription.text.split(/\s+/).filter(Boolean).length,
            " words"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2", children: [
            '"',
            extendedStats.shortestTranscription.text,
            '"'
          ] })
        ] })
      ] })
    ] }),
    (!stats || stats.total_count === 0) && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "card p-8 text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-16 mx-auto mb-4 text-[var(--color-text-disabled)]", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" }) }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-[var(--color-text-secondary)] mb-1", children: "No data yet" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-[var(--color-text-muted)] text-sm", children: "Start transcribing to see your statistics here" })
    ] })
  ] });
}
export {
  Stats as default
};
