import { c as useSettingsStore, j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
import { u as useKeyboardShortcuts, S as SaveStatusIndicator } from "./useKeyboardShortcuts-8hu33O7_.js";
function BehaviorSettings() {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    clearError
  } = useSettingsStore();
  const [localSettings, setLocalSettings] = reactExports.useState({
    auto_paste: true,
    show_recording_indicator: true,
    always_show_indicator: true,
    enable_text_cleanup: false,
    custom_filler_words: "",
    enable_grammar_correction: false,
    grammar_model: "vennify/t5-base-grammar-correction",
    grammar_device: "auto"
  });
  const [saveStatus, setSaveStatus] = reactExports.useState("idle");
  const originalSettings = reactExports.useRef(localSettings);
  const [grammarModels, setGrammarModels] = reactExports.useState({});
  const [modelStatus, setModelStatus] = reactExports.useState({
    status: "not_downloaded",
    progress: 0,
    error: null,
    active_model: null
  });
  const [isLoadingGrammarInfo, setIsLoadingGrammarInfo] = reactExports.useState(false);
  const [isUnloadingModel, setIsUnloadingModel] = reactExports.useState(false);
  const [isStartingDownload, setIsStartingDownload] = reactExports.useState(false);
  const fetchGrammarModels = reactExports.useCallback(async () => {
    if (modelStatus.status !== "downloading" && modelStatus.status !== "loading") {
      setIsLoadingGrammarInfo(true);
    }
    try {
      const response = await fetch("http://127.0.0.1:8765/api/grammar/models");
      if (response.ok) {
        const data = await response.json();
        setGrammarModels(data.models);
        setModelStatus(data.status);
      }
    } catch (err) {
      console.error("Failed to fetch grammar models:", err);
    } finally {
      setIsLoadingGrammarInfo(false);
    }
  }, [modelStatus.status]);
  reactExports.useEffect(() => {
    let pollInterval = null;
    if (modelStatus.status === "downloading" || modelStatus.status === "loading") {
      pollInterval = setInterval(fetchGrammarModels, 1e3);
    }
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [modelStatus.status, fetchGrammarModels]);
  const handleUnloadModel = async () => {
    setIsUnloadingModel(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/grammar/unload", {
        method: "POST"
      });
      if (response.ok) {
        await fetchGrammarModels();
      }
    } catch (err) {
      console.error("Failed to unload grammar model:", err);
    } finally {
      setIsUnloadingModel(false);
    }
  };
  const handleDownloadModel = async () => {
    setIsStartingDownload(true);
    try {
      const response = await fetch("http://127.0.0.1:8765/api/grammar/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: localSettings.grammar_model })
      });
      if (response.ok) {
        await fetchGrammarModels();
      }
    } catch (err) {
      console.error("Failed to start download:", err);
    } finally {
      setIsStartingDownload(false);
    }
  };
  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === "unsaved"
  });
  reactExports.useEffect(() => {
    const isDirty = JSON.stringify(localSettings) !== JSON.stringify(originalSettings.current);
    if (isDirty && saveStatus !== "saving") {
      setSaveStatus("unsaved");
    } else if (!isDirty && saveStatus === "unsaved") {
      setSaveStatus("idle");
    }
  }, [localSettings, saveStatus]);
  reactExports.useEffect(() => {
    fetchSettings();
    fetchGrammarModels();
  }, []);
  reactExports.useEffect(() => {
    if (settings) {
      const newSettings = {
        auto_paste: settings.auto_paste,
        show_recording_indicator: settings.show_recording_indicator,
        always_show_indicator: settings.always_show_indicator ?? true,
        enable_text_cleanup: settings.enable_text_cleanup ?? false,
        custom_filler_words: settings.custom_filler_words?.join(", ") ?? "",
        enable_grammar_correction: settings.enable_grammar_correction ?? false,
        grammar_model: settings.grammar_model ?? "vennify/t5-base-grammar-correction",
        grammar_device: settings.grammar_device ?? "auto"
      };
      if (saveStatus === "idle" || saveStatus === "saved") {
        setLocalSettings(newSettings);
        originalSettings.current = newSettings;
      }
    }
  }, [settings, saveStatus]);
  const handleSave = async () => {
    setSaveStatus("saving");
    const success = await updateSettings({
      auto_paste: localSettings.auto_paste,
      show_recording_indicator: localSettings.show_recording_indicator,
      always_show_indicator: localSettings.always_show_indicator,
      enable_text_cleanup: localSettings.enable_text_cleanup,
      custom_filler_words: localSettings.custom_filler_words ? localSettings.custom_filler_words.split(",").map((s) => s.trim()).filter(Boolean) : null,
      enable_grammar_correction: localSettings.enable_grammar_correction,
      grammar_model: localSettings.grammar_model,
      grammar_device: localSettings.grammar_device
    });
    if (success) {
      setSaveStatus("saved");
      originalSettings.current = localSettings;
    } else {
      setSaveStatus("unsaved");
    }
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-2xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Configure app behavior and text processing" })
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
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Recording Behavior" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center justify-between cursor-pointer", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Auto-paste after transcription" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5", children: "Automatically paste transcribed text to the active window" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: localSettings.auto_paste,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, auto_paste: e.target.checked })),
                  disabled: isSaving,
                  className: "sr-only peer"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center justify-between cursor-pointer", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Show recording indicator" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5", children: "Display a visual indicator in the center of the screen while recording" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: localSettings.show_recording_indicator,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, show_recording_indicator: e.target.checked })),
                  disabled: isSaving,
                  className: "sr-only peer"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" })
            ] })
          ] }),
          localSettings.show_recording_indicator && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center justify-between cursor-pointer ml-6 pl-4 border-l-2 border-[var(--color-border)] animate-in fade-in slide-in-from-top-2 duration-200", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: 'Always show "Ready" status' }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5", children: "Keep the indicator visible on screen when idle" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: localSettings.always_show_indicator,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, always_show_indicator: e.target.checked })),
                  disabled: isSaving,
                  className: "sr-only peer"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" })
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Text Cleanup" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center justify-between cursor-pointer", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Remove filler words" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5", children: 'Automatically remove common filler words like "um", "uh", "like", etc.' })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: localSettings.enable_text_cleanup,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, enable_text_cleanup: e.target.checked })),
                  disabled: isSaving,
                  className: "sr-only peer"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" })
            ] })
          ] }),
          localSettings.enable_text_cleanup && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "animate-in fade-in slide-in-from-top-2 duration-200", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Additional filler words (comma-separated)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "text",
                value: localSettings.custom_filler_words,
                onChange: (e) => setLocalSettings((prev) => ({ ...prev, custom_filler_words: e.target.value })),
                disabled: isSaving,
                placeholder: "e.g., basically, literally, actually",
                className: "input w-full"
              }
            )
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Grammar Correction" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center justify-between cursor-pointer", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Enable AI grammar correction" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5", children: "Use a local AI model to fix grammar and improve fluency" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  checked: localSettings.enable_grammar_correction,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, enable_grammar_correction: e.target.checked })),
                  disabled: isSaving,
                  className: "sr-only peer"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-11 h-6 bg-[var(--color-bg-tertiary)] peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-[var(--color-accent)] rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--color-accent)]" })
            ] })
          ] }),
          localSettings.enable_grammar_correction && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "animate-in fade-in slide-in-from-top-2 duration-200 space-y-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Grammar Model" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "select",
                {
                  value: localSettings.grammar_model,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, grammar_model: e.target.value })),
                  disabled: isSaving,
                  className: "input w-full",
                  children: Object.entries(grammarModels).length > 0 ? Object.entries(grammarModels).map(([id, model]) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: id, children: [
                    model.name,
                    " (",
                    model.size_mb,
                    "MB)",
                    model.downloaded ? " ✓" : ""
                  ] }, id)) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "vennify/t5-base-grammar-correction", children: "T5 Base Grammar Correction (890MB, recommended)" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "pszemraj/flan-t5-large-grammar-synthesis", children: "Flan T5 Large Grammar Synthesis (3GB)" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "grammarly/coedit-xl", children: "Grammarly CoEdit XL (3GB)" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "prithivida/grammar_error_correcter_v1", children: "Grammar Error Correcter V1 (220MB, may have issues)" })
                  ] })
                }
              )
            ] }),
            grammarModels[localSettings.grammar_model] && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-3 bg-[var(--color-bg-secondary)] rounded-lg", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-2", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-[var(--color-text-primary)]", children: grammarModels[localSettings.grammar_model].name }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                  grammarModels[localSettings.grammar_model].downloaded ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full", children: "Downloaded" }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded-full", children: "Will download on first use" }),
                  modelStatus.active_model === localSettings.grammar_model && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full", children: "Loaded" })
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)]", children: grammarModels[localSettings.grammar_model].description }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4 mt-2 text-xs text-[var(--color-text-muted)]", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                  "Size: ",
                  grammarModels[localSettings.grammar_model].size_mb,
                  "MB"
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                  "VRAM: ~",
                  grammarModels[localSettings.grammar_model].vram_gb,
                  "GB"
                ] })
              ] }),
              modelStatus.active_model === localSettings.grammar_model && modelStatus.status === "loaded" && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  onClick: handleUnloadModel,
                  disabled: isUnloadingModel,
                  className: "mt-3 px-3 py-1.5 text-xs bg-[var(--color-bg-tertiary)] hover:bg-[var(--color-border)] text-[var(--color-text-secondary)] rounded transition-colors",
                  children: isUnloadingModel ? "Unloading..." : `Unload Model (Free VRAM)`
                }
              ),
              !grammarModels[localSettings.grammar_model].downloaded && modelStatus.status !== "downloading" && modelStatus.status !== "loading" && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "button",
                {
                  onClick: handleDownloadModel,
                  disabled: isStartingDownload,
                  className: "mt-3 px-3 py-1.5 text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded transition-colors",
                  children: isStartingDownload ? "Starting..." : `Download Model Now`
                }
              ),
              (modelStatus.status === "downloading" || modelStatus.status === "loading") && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 space-y-1", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between text-xs text-[var(--color-text-secondary)]", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: modelStatus.status === "downloading" ? "Downloading..." : "Loading..." }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                    Math.round(modelStatus.progress * 100),
                    "%"
                  ] })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-full bg-[var(--color-bg-tertiary)] rounded-full h-1.5 overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    className: "bg-[var(--color-accent)] h-1.5 rounded-full transition-all duration-300",
                    style: { width: `${modelStatus.progress * 100}%` }
                  }
                ) })
              ] }),
              modelStatus.status === "error" && modelStatus.error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 p-2 bg-red-500/10 text-red-500 text-xs rounded border border-red-500/20", children: [
                "Error: ",
                modelStatus.error
              ] })
            ] }),
            isLoadingGrammarInfo && !Object.keys(grammarModels).length && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-sm text-[var(--color-text-muted)]", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-4 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }),
              "Loading model info..."
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Device" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "select",
                {
                  value: localSettings.grammar_device,
                  onChange: (e) => setLocalSettings((prev) => ({ ...prev, grammar_device: e.target.value })),
                  disabled: isSaving,
                  className: "input w-full",
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "auto", children: "Auto (GPU if available, otherwise CPU)" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "cuda", children: "GPU (CUDA)" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "cpu", children: "CPU" })
                  ]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-1.5", children: "GPU is faster but requires a compatible graphics card with sufficient VRAM." })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-xs text-blue-400", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Note:" }),
              " The model will download automatically on first use. This may take a moment depending on your internet speed. The model runs locally on your device for privacy."
            ] }) })
          ] })
        ] })
      ] })
    ] })
  ] });
}
export {
  BehaviorSettings as default
};
