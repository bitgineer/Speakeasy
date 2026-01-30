import { j as jsxRuntimeExports, b as apiClient } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
const FORMAT_OPTIONS = [
  { value: "txt", label: "Plain Text", description: "Simple text format, one transcription per block" },
  { value: "json", label: "JSON", description: "Structured data with metadata, ideal for backup/import" },
  { value: "csv", label: "CSV", description: "Spreadsheet compatible, opens in Excel/Sheets" },
  { value: "srt", label: "SRT", description: "SubRip subtitle format for video players" },
  { value: "vtt", label: "VTT", description: "WebVTT subtitle format for web videos" }
];
const ExportDialog = ({ isOpen, onClose, singleRecordId }) => {
  const [format, setFormat] = reactExports.useState("json");
  const [includeMetadata, setIncludeMetadata] = reactExports.useState(true);
  const [startDate, setStartDate] = reactExports.useState("");
  const [endDate, setEndDate] = reactExports.useState("");
  const [isLoading, setIsLoading] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  reactExports.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);
  const handleExport = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let blob;
      if (singleRecordId) {
        blob = await apiClient.exportHistoryFiltered({
          format,
          include_metadata: includeMetadata,
          record_ids: [singleRecordId]
        });
      } else if (startDate || endDate) {
        blob = await apiClient.exportHistoryFiltered({
          format,
          include_metadata: includeMetadata,
          start_date: startDate || void 0,
          end_date: endDate || void 0
        });
      } else {
        blob = await apiClient.exportHistory(format, includeMetadata);
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `speakeasy_export_${(/* @__PURE__ */ new Date()).toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsLoading(false);
    }
  };
  if (!isOpen) return null;
  const showMetadataOption = format === "json" || format === "csv";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity",
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": "export-dialog-title",
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "w-full max-w-md transform overflow-hidden rounded-2xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] p-6 text-left align-middle shadow-xl transition-all", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "h3",
          {
            id: "export-dialog-title",
            className: "text-lg font-medium leading-6 text-[var(--color-text-primary)] mb-4 flex items-center gap-2",
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-[var(--color-accent)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" }) }),
              singleRecordId ? "Export Transcription" : "Export History"
            ]
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-sm font-medium text-[var(--color-text-secondary)] mb-2", children: "Format" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "select",
              {
                value: format,
                onChange: (e) => setFormat(e.target.value),
                className: "w-full px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]",
                children: FORMAT_OPTIONS.map((opt) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: opt.value, children: opt.label }, opt.value))
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-xs text-[var(--color-text-muted)]", children: FORMAT_OPTIONS.find((o) => o.value === format)?.description })
          ] }),
          showMetadataOption && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center gap-3 cursor-pointer", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "checkbox",
                checked: includeMetadata,
                onChange: (e) => setIncludeMetadata(e.target.checked),
                className: "w-4 h-4 text-[var(--color-accent)] bg-[var(--color-bg-tertiary)] border-[var(--color-border)] rounded focus:ring-[var(--color-accent)]"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-[var(--color-text-secondary)]", children: "Include metadata (duration, model, language)" })
          ] }),
          !singleRecordId && /* @__PURE__ */ jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "block text-sm font-medium text-[var(--color-text-secondary)] mb-2", children: "Date Range (optional)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "date",
                  value: startDate,
                  onChange: (e) => setStartDate(e.target.value),
                  className: "flex-1 px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]",
                  placeholder: "From"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "date",
                  value: endDate,
                  onChange: (e) => setEndDate(e.target.value),
                  className: "flex-1 px-3 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]",
                  placeholder: "To"
                }
              )
            ] })
          ] }) }),
          error && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg p-3", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-error)]", children: error }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-6 flex justify-end gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              className: "inline-flex justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-tertiary)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-bg-elevated)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] transition-colors",
              onClick: onClose,
              disabled: isLoading,
              children: "Cancel"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              className: "inline-flex justify-center rounded-lg border border-transparent bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-[var(--color-text-on-accent)] hover:bg-[var(--color-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
              onClick: handleExport,
              disabled: isLoading,
              children: isLoading ? /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "flex items-center gap-2", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { className: "animate-spin h-4 w-4", viewBox: "0 0 24 24", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { className: "opacity-25", cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4", fill: "none" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("path", { className: "opacity-75", fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" })
                ] }),
                "Exporting..."
              ] }) : "Export"
            }
          )
        ] })
      ] })
    }
  );
};
export {
  ExportDialog as E
};
