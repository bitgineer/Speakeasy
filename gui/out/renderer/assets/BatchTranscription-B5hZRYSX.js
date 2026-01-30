import { w as wsClient, b as apiClient, j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
function BatchTranscription() {
  const [selectedFiles, setSelectedFiles] = reactExports.useState([]);
  const [job, setJob] = reactExports.useState(null);
  const [isDragging, setIsDragging] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  const [isLoading, setIsLoading] = reactExports.useState(false);
  reactExports.useEffect(() => {
    const handleMessage = (event) => {
      if (event.type === "batch_progress") {
        const progressEvent = event;
        if (job && job.id === progressEvent.job_id) {
          setJob((prev) => prev ? {
            ...prev,
            status: progressEvent.status,
            current_file_index: progressEvent.current_index,
            completed_count: progressEvent.completed,
            failed_count: progressEvent.failed
            // We might need to refresh the full job to get updated file statuses
            // but for the progress bar, the event data is enough
          } : null);
          if (progressEvent.file_status) {
            apiClient.getBatchJob(progressEvent.job_id).then(setJob).catch(console.error);
          }
        }
      }
    };
    const unsubscribe = wsClient.on("message", handleMessage);
    return () => {
      unsubscribe();
    };
  }, [job]);
  const handleDragOver = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const handleDragLeave = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  const handleDrop = reactExports.useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter(
        (file) => file.type.startsWith("audio/") || file.type.startsWith("video/") || // Fallback for some formats that might not have mime type detected correctly
        /\.(mp3|wav|m4a|ogg|flac|mp4|mkv|mov|webm)$/i.test(file.name)
      );
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  }, []);
  const handleFileSelect = reactExports.useCallback((e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
    e.target.value = "";
  }, []);
  const removeFile = reactExports.useCallback((index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);
  const clearAll = reactExports.useCallback(() => {
    setSelectedFiles([]);
    setJob(null);
    setError(null);
  }, []);
  const startBatch = reactExports.useCallback(async () => {
    if (selectedFiles.length === 0) return;
    setIsLoading(true);
    setError(null);
    try {
      const filePaths = selectedFiles.map((f) => f.path);
      const response = await apiClient.createBatchJob({
        file_paths: filePaths
      });
      const newJob = await apiClient.getBatchJob(response.job_id);
      setJob(newJob);
      setSelectedFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start batch job");
    } finally {
      setIsLoading(false);
    }
  }, [selectedFiles]);
  const retryFailed = reactExports.useCallback(async () => {
    if (!job) return;
    setIsLoading(true);
    try {
      const response = await apiClient.retryBatchJob(job.id);
      setJob(response.job);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry job");
    } finally {
      setIsLoading(false);
    }
  }, [job]);
  const formatSize = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-full flex flex-col bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] p-6 overflow-auto", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6 flex justify-between items-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-2xl font-bold", children: "Batch Transcription" }),
      job && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: clearAll,
          className: "text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors",
          children: "Start New Batch"
        }
      )
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mb-6 p-4 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg text-[var(--color-error)]", children: error }),
    !job ? (
      // File Selection State
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex flex-col gap-6", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            className: `
              border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
              ${isDragging ? "border-[var(--color-accent)] bg-[var(--color-accent-muted)]" : "border-[var(--color-border)] hover:border-[var(--color-border-strong)] bg-[var(--color-bg-tertiary)]"}
            `,
            onDragOver: handleDragOver,
            onDragLeave: handleDragLeave,
            onDrop: handleDrop,
            onClick: () => document.getElementById("file-input")?.click(),
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "file",
                  id: "file-input",
                  multiple: true,
                  className: "hidden",
                  onChange: handleFileSelect,
                  accept: "audio/*,video/*"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center gap-3", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-12 h-12 text-[var(--color-text-muted)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 1.5, d: "M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-lg font-medium text-[var(--color-text-secondary)]", children: "Drop audio files here or click to browse" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)]", children: "Supports MP3, WAV, M4A, MP4, MKV, and more" })
              ] })
            ]
          }
        ),
        selectedFiles.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex flex-col bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden border border-[var(--color-border)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4 border-b border-[var(--color-border)] flex justify-between items-center bg-[var(--color-bg-tertiary)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "font-medium text-[var(--color-text-secondary)]", children: [
              selectedFiles.length,
              " files selected"
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: () => setSelectedFiles([]),
                className: "text-sm text-[var(--color-error)] hover:text-[var(--color-error-hover)]",
                children: "Clear All"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 overflow-auto p-2 space-y-2", children: selectedFiles.map((file, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between p-3 bg-[var(--color-bg-tertiary)] rounded-lg group", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 overflow-hidden", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 rounded bg-[var(--color-bg-elevated)] flex items-center justify-center flex-shrink-0", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-text-muted)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" }) }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm font-medium text-[var(--color-text-secondary)] truncate", children: file.name }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)]", children: formatSize(file.size) })
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: (e) => {
                  e.stopPropagation();
                  removeFile(index);
                },
                className: "p-1 text-[var(--color-text-muted)] hover:text-[var(--color-error)] opacity-0 group-hover:opacity-100 transition-opacity",
                children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
              }
            )
          ] }, `${file.name}-${index}`)) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-tertiary)]", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: startBatch,
              disabled: isLoading,
              className: "w-full py-3 px-4 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed text-[var(--color-text-on-accent)] font-medium rounded-lg transition-colors flex items-center justify-center gap-2",
              children: isLoading ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" }),
                "Starting..."
              ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M21 12a9 9 0 11-18 0 9 9 0 0118 0z" })
                ] }),
                "Start Batch Transcription"
              ] })
            }
          ) })
        ] })
      ] })
    ) : (
      // Job Progress/Results State
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex flex-col gap-6", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-[var(--color-bg-secondary)] rounded-xl p-6 border border-[var(--color-border)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-end mb-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-lg font-semibold text-[var(--color-text-primary)] mb-1", children: job.status === "completed" ? "Batch Complete" : job.status === "failed" ? "Batch Failed" : "Processing Batch..." }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)]", children: job.status === "processing" ? `Processing file ${job.current_file_index + 1} of ${job.total_files}` : `Processed ${job.completed_count} of ${job.total_files} files` })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-right", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-2xl font-bold text-[var(--color-accent)]", children: [
              Math.round(job.completed_count / job.total_files * 100),
              "%"
            ] }) })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-2 bg-[var(--color-bg-tertiary)] rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: `h-full transition-all duration-500 ${job.status === "failed" ? "bg-[var(--color-error)]" : job.status === "completed" ? "bg-[var(--color-success)]" : "bg-[var(--color-accent)]"}`,
              style: { width: `${job.completed_count / job.total_files * 100}%` }
            }
          ) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-2xl font-bold text-[var(--color-success)]", children: job.completed_count }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-[var(--color-text-muted)] uppercase tracking-wider", children: "Completed" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-2xl font-bold text-[var(--color-error)]", children: job.failed_count }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-[var(--color-text-muted)] uppercase tracking-wider", children: "Failed" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-2xl font-bold text-[var(--color-text-muted)]", children: job.skipped_count }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-[var(--color-text-muted)] uppercase tracking-wider", children: "Skipped" })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 bg-[var(--color-bg-secondary)] rounded-xl overflow-hidden border border-[var(--color-border)] flex flex-col", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-4 border-b border-[var(--color-border)] font-medium text-[var(--color-text-secondary)]", children: "Files" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 overflow-auto p-2 space-y-2", children: job.files.map((file) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: `
                    flex items-center justify-between p-3 rounded-lg border
                    ${file.status === "processing" ? "bg-[var(--color-info-muted)] border-[var(--color-info)]" : file.status === "completed" ? "bg-[var(--color-success-muted)] border-[var(--color-success)]" : file.status === "failed" ? "bg-[var(--color-error-muted)] border-[var(--color-error)]" : "bg-[var(--color-bg-tertiary)] border-transparent"}
                  `,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 min-w-0", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `
                      w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                      ${file.status === "completed" ? "text-[var(--color-success)]" : file.status === "failed" ? "text-[var(--color-error)]" : file.status === "processing" ? "text-[var(--color-info)]" : "text-[var(--color-text-muted)]"}
                    `, children: file.status === "completed" ? /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }) : file.status === "failed" ? /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) : file.status === "processing" ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 bg-current rounded-full" }) }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm font-medium text-[var(--color-text-secondary)] truncate", children: file.filename }),
                    file.error && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-error)] truncate", children: file.error })
                  ] })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs font-medium px-2 py-1 rounded bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)] capitalize", children: file.status })
              ]
            },
            file.id
          )) }),
          job.failed_count > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-4 border-t border-[var(--color-border)] bg-[var(--color-bg-tertiary)]", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: retryFailed,
              disabled: isLoading,
              className: "w-full py-2 px-4 bg-[var(--color-bg-elevated)] hover:bg-[var(--color-bg-secondary)] text-[var(--color-text-primary)] font-medium rounded-lg transition-colors flex items-center justify-center gap-2",
              children: isLoading ? "Retrying..." : "Retry Failed Files"
            }
          ) })
        ] })
      ] })
    )
  ] });
}
export {
  BatchTranscription as default
};
