import { d as useDownloadStore, j as jsxRuntimeExports, c as useSettingsStore, a as useAppStore } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
import { u as useKeyboardShortcuts, S as SaveStatusIndicator } from "./useKeyboardShortcuts-8hu33O7_.js";
function ModelSelector({
  availableModels,
  selectedType,
  selectedName,
  onTypeChange,
  onNameChange,
  disabled = false,
  isLoadingModels = false,
  isLoadingModel = false
}) {
  const { cachedModels, isDownloading } = useDownloadStore();
  const isModelDownloaded = (name) => {
    return cachedModels.some((m) => m.model_name === name);
  };
  const getModelSize = (name) => {
    return cachedModels.find((m) => m.model_name === name)?.size_human;
  };
  const currentModelInfo = reactExports.useMemo(() => {
    return availableModels[selectedType] || null;
  }, [availableModels, selectedType]);
  const modelVariants = reactExports.useMemo(() => {
    if (!currentModelInfo) return [];
    return Object.keys(currentModelInfo.models);
  }, [currentModelInfo]);
  const isComponentDisabled = disabled || isLoadingModels || isLoadingModel || isDownloading;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4 relative", children: [
    isLoadingModels && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 z-10 bg-gray-900/50 backdrop-blur-[1px] flex items-center justify-center rounded-lg", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center gap-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-white", children: "Loading models..." })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: isLoadingModels ? "opacity-50 pointer-events-none" : "", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "model-type-select", className: "label", children: "Model Type" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "select",
        {
          id: "model-type-select",
          value: selectedType,
          onChange: (e) => {
            onTypeChange(e.target.value);
            const newModelInfo = availableModels[e.target.value];
            if (newModelInfo) {
              const firstModel = Object.keys(newModelInfo.models)[0];
              if (firstModel) {
                onNameChange(firstModel);
              }
            }
          },
          disabled: isComponentDisabled,
          className: `select ${isComponentDisabled ? "cursor-not-allowed opacity-70" : ""}`,
          children: Object.entries(availableModels).map(([type, info]) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: type, children: [
            type,
            " - ",
            info.description
          ] }, type))
        }
      ),
      currentModelInfo && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-1 text-xs text-gray-500", children: [
        "Languages: ",
        currentModelInfo.languages.slice(0, 5).join(", "),
        currentModelInfo.languages.length > 5 && ` +${currentModelInfo.languages.length - 5} more`
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: isLoadingModels ? "opacity-50 pointer-events-none" : "", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "model-variant-select", className: "label", children: "Model Variant" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "select",
        {
          id: "model-variant-select",
          value: selectedName,
          onChange: (e) => onNameChange(e.target.value),
          disabled: isComponentDisabled || modelVariants.length === 0,
          className: `select ${isComponentDisabled ? "cursor-not-allowed opacity-70" : ""}`,
          children: modelVariants.map((name) => {
            const modelDetails = currentModelInfo?.models[name];
            const isDownloaded = isModelDownloaded(name);
            return /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: name, children: [
              isDownloaded ? "✓ " : "⬇ ",
              name,
              modelDetails && ` (${modelDetails.speed}, ${modelDetails.vram_gb}GB VRAM)`
            ] }, name);
          })
        }
      ),
      isLoadingModel && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2 flex items-center gap-2 text-blue-400 animate-pulse", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs font-medium", children: "Loading model..." })
      ] }),
      !isLoadingModel && currentModelInfo && selectedName && currentModelInfo.models[selectedName] && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2 flex flex-wrap items-center gap-2 text-xs", children: [
        isModelDownloaded(selectedName) ? /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "badge-green flex items-center gap-1", children: [
          "✓ Downloaded",
          getModelSize(selectedName) && ` (${getModelSize(selectedName)})`
        ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "badge-gray flex items-center gap-1", children: "⬇ Not downloaded - click to download" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "badge-blue", children: [
          "Speed: ",
          currentModelInfo.models[selectedName].speed
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "badge-green", children: [
          "Accuracy: ",
          currentModelInfo.models[selectedName].accuracy
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "badge-yellow", children: [
          "VRAM: ",
          currentModelInfo.models[selectedName].vram_gb,
          "GB"
        ] })
      ] })
    ] })
  ] });
}
const ModelSelector$1 = reactExports.memo(ModelSelector);
const formatBytes = (bytes, decimals = 2) => {
  if (!+bytes) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};
const formatTime = (seconds) => {
  if (seconds === null || !isFinite(seconds)) return "Calculating...";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
};
const ModelDownloadDialog = ({
  isOpen,
  onClose,
  onRetry
}) => {
  const {
    isDownloading,
    downloadProgress,
    downloadedBytes,
    totalBytes,
    modelName,
    status,
    errorMessage,
    bytesPerSecond,
    estimatedRemainingSeconds,
    cancelDownload
  } = useDownloadStore();
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
  if (!isOpen) return null;
  const isCompleted = status === "completed";
  const isError = status === "error";
  const isCancelled = status === "cancelled";
  const handleCancel = async () => {
    await cancelDownload();
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: "fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity",
      role: "dialog",
      "aria-modal": "true",
      "aria-labelledby": "download-dialog-title",
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "w-full max-w-md transform overflow-hidden rounded-2xl bg-gray-800 border border-gray-700 p-6 text-left align-middle shadow-xl transition-all", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "h3",
          {
            id: "download-dialog-title",
            className: "text-lg font-medium leading-6 text-white mb-4 flex items-center gap-2",
            children: isCompleted ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-green-500", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
              "Download Complete"
            ] }) : isError ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-red-500", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }) }),
              "Download Failed"
            ] }) : isCancelled ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-yellow-500", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" }) }),
              "Download Cancelled"
            ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-6 h-6 text-blue-500 animate-pulse", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" }) }),
              "Downloading Model"
            ] })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-gray-300 mb-4", children: modelName ? `Model: ${modelName}` : "Preparing download..." }),
          isError && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "bg-red-900/20 border border-red-900/50 rounded-lg p-3 mb-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-red-400", children: errorMessage || "An unknown error occurred during download." }) }),
          !isCompleted && !isError && !isCancelled && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between text-xs text-gray-400", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                formatBytes(downloadedBytes),
                " / ",
                formatBytes(totalBytes)
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                Math.round(downloadProgress),
                "%"
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-2 w-full bg-gray-700 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                className: "h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300 ease-out",
                style: { width: `${downloadProgress}%` }
              }
            ) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between text-xs text-gray-500 mt-1", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                formatBytes(bytesPerSecond),
                "/s"
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "ETA: ",
                formatTime(estimatedRemainingSeconds)
              ] })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-6 flex justify-end gap-3", children: isDownloading ? /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            className: "inline-flex justify-center rounded-lg border border-transparent bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 transition-colors",
            onClick: handleCancel,
            children: "Cancel Download"
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          (isError || isCancelled) && onRetry && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              className: "inline-flex justify-center rounded-lg border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors",
              onClick: onRetry,
              children: "Retry"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              className: "inline-flex justify-center rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-sm font-medium text-white hover:bg-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2 transition-colors",
              onClick: onClose,
              children: isCompleted ? "Done" : "Close"
            }
          )
        ] }) })
      ] })
    }
  );
};
function ModelSettings() {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    availableModels,
    needsModelReload,
    fetchSettings,
    fetchModels,
    updateSettings,
    loadModel,
    clearError
  } = useSettingsStore();
  const { gpuAvailable, gpuName, gpuVramGb } = useAppStore();
  const {
    isDownloading,
    cachedModels,
    cacheDir,
    totalCacheSizeHuman,
    fetchCacheInfo,
    clearCache,
    isClearingCache
  } = useDownloadStore();
  const [showDownloadDialog, setShowDownloadDialog] = reactExports.useState(false);
  const [isSyncing, setIsSyncing] = reactExports.useState(false);
  const [lastSyncTime, setLastSyncTime] = reactExports.useState(null);
  const [localSettings, setLocalSettings] = reactExports.useState({
    model_type: "",
    model_name: "",
    device: "cpu",
    compute_type: "float16",
    language: "auto"
  });
  const [saveStatus, setSaveStatus] = reactExports.useState("idle");
  const [originalSettings, setOriginalSettings] = reactExports.useState(localSettings);
  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === "unsaved"
  });
  reactExports.useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings);
    if (isDirty && saveStatus !== "saving") {
      setSaveStatus("unsaved");
    } else if (!isDirty && saveStatus === "unsaved") {
      setSaveStatus("idle");
    }
  }, [localSettings, saveStatus, originalSettings]);
  reactExports.useEffect(() => {
    fetchSettings();
    fetchModels();
  }, [fetchSettings, fetchModels]);
  reactExports.useEffect(() => {
    if (isDownloading) {
      setShowDownloadDialog(true);
    }
  }, [isDownloading]);
  reactExports.useEffect(() => {
    if (settings) {
      const newSettings = {
        model_type: settings.model_type,
        model_name: settings.model_name,
        device: settings.device,
        compute_type: settings.compute_type,
        language: settings.language
      };
      setLocalSettings(newSettings);
      setOriginalSettings(newSettings);
    }
  }, [settings]);
  const handleSyncModels = reactExports.useCallback(async () => {
    setIsSyncing(true);
    try {
      await fetchCacheInfo();
      setLastSyncTime(/* @__PURE__ */ new Date());
    } finally {
      setIsSyncing(false);
    }
  }, [fetchCacheInfo]);
  const handleSave = async () => {
    setSaveStatus("saving");
    const success = await updateSettings({
      model_type: localSettings.model_type,
      model_name: localSettings.model_name,
      device: localSettings.device,
      compute_type: localSettings.compute_type,
      language: localSettings.language
    });
    if (success) {
      setSaveStatus("saved");
      setOriginalSettings(localSettings);
    } else {
      setSaveStatus("unsaved");
    }
  };
  const handleLoadModel = async () => {
    await loadModel(localSettings.model_type, localSettings.model_name);
  };
  const handleTypeChange = reactExports.useCallback((type) => {
    setLocalSettings((prev) => ({ ...prev, model_type: type }));
  }, []);
  const handleNameChange = reactExports.useCallback((name) => {
    setLocalSettings((prev) => ({ ...prev, model_name: name }));
  }, []);
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-2xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Model Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Configure transcription model and performance" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(SaveStatusIndicator, { status: saveStatus }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: handleSave,
            disabled: isSaving || saveStatus === "idle" || saveStatus === "saved",
            className: "btn-primary",
            children: isSaving ? "Saving..." : "Save Changes"
          }
        )
      ] })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-error)] text-sm", children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: clearError, className: "text-[var(--color-error)] hover:opacity-80", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) })
    ] }),
    needsModelReload && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6 p-3 bg-[var(--color-warning-muted)] border border-[var(--color-warning)] rounded-lg flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-warning)] text-sm", children: 'Model settings changed. Click "Load Model" to apply.' }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: handleLoadModel,
          disabled: isSaving || isDownloading,
          className: "btn-sm bg-[var(--color-warning)] text-[var(--color-bg-primary)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
          children: isDownloading ? "Downloading..." : "Load Model"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Model Selection" }),
        availableModels.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-8 text-[var(--color-text-muted)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-6 h-6 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin mx-auto mb-3" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "Loading available models..." })
        ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx(
          ModelSelector$1,
          {
            availableModels,
            selectedType: localSettings.model_type,
            selectedName: localSettings.model_name,
            onTypeChange: handleTypeChange,
            onNameChange: handleNameChange,
            disabled: isSaving
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Compute Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Compute Device" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              value: localSettings.device,
              onChange: (e) => setLocalSettings((prev) => ({ ...prev, device: e.target.value })),
              disabled: isSaving,
              className: "select",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "cpu", children: "CPU" }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: "cuda", disabled: !gpuAvailable, children: [
                  "GPU (CUDA)",
                  gpuAvailable ? ` - ${gpuName}` : " - Not available"
                ] })
              ]
            }
          ),
          gpuAvailable && gpuVramGb && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-1 text-xs text-[var(--color-text-muted)]", children: [
            "GPU has ",
            gpuVramGb.toFixed(1),
            "GB VRAM available"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Compute Precision" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              value: localSettings.compute_type,
              onChange: (e) => setLocalSettings((prev) => ({ ...prev, compute_type: e.target.value })),
              disabled: isSaving,
              className: "select",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "float32", children: "Float32 (Most accurate, slowest)" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "float16", children: "Float16 (Balanced)" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "int8", children: "Int8 (Fastest, less accurate)" })
              ]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Language" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              value: localSettings.language,
              onChange: (e) => setLocalSettings((prev) => ({ ...prev, language: e.target.value })),
              disabled: isSaving,
              className: "select",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "auto", children: "Auto-detect" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "en", children: "English" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "es", children: "Spanish" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "fr", children: "French" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "de", children: "German" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "it", children: "Italian" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "pt", children: "Portuguese" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "nl", children: "Dutch" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "ja", children: "Japanese" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "ko", children: "Korean" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "zh", children: "Chinese" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "ru", children: "Russian" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "ar", children: "Arabic" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "hi", children: "Hindi" })
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium text-[var(--color-text-primary)]", children: "Downloaded Models" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
            lastSyncTime && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs text-[var(--color-text-muted)]", children: [
              "Last synced: ",
              lastSyncTime.toLocaleTimeString()
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "button",
              {
                onClick: handleSyncModels,
                disabled: isSyncing,
                className: "flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)] rounded-lg transition-colors border border-[var(--color-border)] disabled:opacity-50 disabled:cursor-not-allowed",
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "svg",
                    {
                      className: `w-4 h-4 ${isSyncing ? "animate-spin" : ""}`,
                      fill: "none",
                      stroke: "currentColor",
                      viewBox: "0 0 24 24",
                      children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" })
                    }
                  ),
                  isSyncing ? "Syncing..." : "Refresh"
                ]
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between text-sm text-[var(--color-text-muted)] bg-[var(--color-bg-tertiary)] p-3 rounded-lg border border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-secondary)] font-medium", children: "Local Cache Storage" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-[var(--color-text-muted)] mt-1 font-mono break-all", children: cacheDir || "Loading..." })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-semibold text-[var(--color-text-primary)]", children: totalCacheSizeHuman || "0 B" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-[var(--color-text-muted)]", children: "Total Usage" })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "bg-[var(--color-bg-tertiary)] rounded-lg border border-[var(--color-border)] overflow-hidden", children: cachedModels.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-4 text-center text-[var(--color-text-muted)] text-sm", children: "No models downloaded yet." }) : /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "divide-y divide-[var(--color-border)]", children: cachedModels.map((model) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "p-3 flex items-center justify-between hover:bg-[var(--color-bg-elevated)] transition-colors", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium text-[var(--color-text-secondary)]", children: model.model_name }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-[var(--color-text-muted)]", children: [
                model.size_human,
                " • ",
                model.source
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: () => {
                  if (confirm(`Are you sure you want to delete ${model.model_name}?`)) {
                    clearCache(model.model_name);
                  }
                },
                disabled: isClearingCache,
                className: "p-2 text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-muted)] rounded-lg transition-colors",
                title: "Delete model",
                children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" }) })
              }
            )
          ] }, model.model_name)) }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between pt-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)]", children: "Models are cached locally to enable offline use and faster loading." }),
            cachedModels.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: () => {
                  if (confirm("Are you sure you want to delete ALL downloaded models? This cannot be undone.")) {
                    clearCache();
                  }
                },
                disabled: isClearingCache,
                className: "text-xs text-[var(--color-error)] hover:opacity-80 disabled:opacity-50",
                children: isClearingCache ? "Clearing..." : "Clear All Cache"
              }
            )
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      ModelDownloadDialog,
      {
        isOpen: showDownloadDialog,
        onClose: () => setShowDownloadDialog(false)
      }
    )
  ] });
}
export {
  ModelSettings as default
};
