import { j as jsxRuntimeExports, c as useSettingsStore } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
import { u as useKeyboardShortcuts, S as SaveStatusIndicator } from "./useKeyboardShortcuts-8hu33O7_.js";
const keyDisplayNames = {
  " ": "Space",
  "ArrowUp": "Up",
  "ArrowDown": "Down",
  "ArrowLeft": "Left",
  "ArrowRight": "Right",
  "Escape": "Esc",
  "Delete": "Del",
  "Backspace": "Backspace",
  "Enter": "Enter",
  "Tab": "Tab",
  "Home": "Home",
  "End": "End",
  "PageUp": "PgUp",
  "PageDown": "PgDn",
  "Insert": "Ins",
  "Pause": "Pause",
  "ScrollLock": "ScrollLock",
  "PrintScreen": "PrtSc",
  "ContextMenu": "Menu"
};
function formatKeyForDisplay(key) {
  if (keyDisplayNames[key]) {
    return keyDisplayNames[key];
  }
  if (key.startsWith("F") && !isNaN(parseInt(key.slice(1)))) {
    return key;
  }
  if (key.length === 1) {
    return key.toUpperCase();
  }
  return key;
}
function formatHotkeyForDisplay(hotkey) {
  if (!hotkey) return "";
  const parts = hotkey.split("+");
  return parts.map((part) => {
    const trimmed = part.trim();
    if (trimmed === "CommandOrControl") return "Ctrl";
    if (trimmed === "Command") return "Cmd";
    if (trimmed === "Control") return "Ctrl";
    if (trimmed === "Alt") return "Alt";
    if (trimmed === "Shift") return "Shift";
    if (trimmed === "Super") return "Win";
    return formatKeyForDisplay(trimmed);
  }).join(" + ");
}
function HotkeyInput({
  value,
  onChange,
  disabled = false
}) {
  const [isCapturing, setIsCapturing] = reactExports.useState(false);
  const [capturedKeys, setCapturedKeys] = reactExports.useState(/* @__PURE__ */ new Set());
  const inputRef = reactExports.useRef(null);
  const handleKeyDown = reactExports.useCallback((e) => {
    if (!isCapturing) return;
    e.preventDefault();
    e.stopPropagation();
    const key = e.key;
    const newKeys = new Set(capturedKeys);
    if (e.ctrlKey) newKeys.add("Control");
    if (e.altKey) newKeys.add("Alt");
    if (e.shiftKey) newKeys.add("Shift");
    if (e.metaKey) newKeys.add("Super");
    if (!["Control", "Alt", "Shift", "Meta"].includes(key)) {
      newKeys.add(key);
    }
    setCapturedKeys(newKeys);
  }, [isCapturing, capturedKeys]);
  const handleKeyUp = reactExports.useCallback((e) => {
    if (!isCapturing) return;
    e.preventDefault();
    e.stopPropagation();
    const modifiers = ["Control", "Alt", "Shift", "Super"];
    const hasMainKey = Array.from(capturedKeys).some((k) => !modifiers.includes(k));
    if (hasMainKey) {
      const parts = [];
      if (capturedKeys.has("Control")) parts.push("Control");
      if (capturedKeys.has("Alt")) parts.push("Alt");
      if (capturedKeys.has("Shift")) parts.push("Shift");
      if (capturedKeys.has("Super")) parts.push("Super");
      capturedKeys.forEach((key) => {
        if (!modifiers.includes(key)) {
          parts.push(key);
        }
      });
      const hotkeyString = parts.join("+");
      onChange(hotkeyString);
    }
    setIsCapturing(false);
    setCapturedKeys(/* @__PURE__ */ new Set());
    inputRef.current?.blur();
  }, [isCapturing, capturedKeys, onChange]);
  reactExports.useEffect(() => {
    if (isCapturing) {
      window.addEventListener("keydown", handleKeyDown, true);
      window.addEventListener("keyup", handleKeyUp, true);
      return () => {
        window.removeEventListener("keydown", handleKeyDown, true);
        window.removeEventListener("keyup", handleKeyUp, true);
      };
    }
  }, [isCapturing, handleKeyDown, handleKeyUp]);
  const startCapturing = () => {
    if (disabled) return;
    setIsCapturing(true);
    setCapturedKeys(/* @__PURE__ */ new Set());
  };
  const clearHotkey = () => {
    onChange("");
    setIsCapturing(false);
    setCapturedKeys(/* @__PURE__ */ new Set());
  };
  const displayValue = isCapturing ? capturedKeys.size > 0 ? formatHotkeyForDisplay(Array.from(capturedKeys).join("+")) : "Press keys..." : value ? formatHotkeyForDisplay(value) : "Click to set hotkey";
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Recording Hotkey" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          ref: inputRef,
          type: "text",
          value: displayValue,
          onFocus: startCapturing,
          onBlur: () => {
            if (!capturedKeys.size) {
              setIsCapturing(false);
            }
          },
          readOnly: true,
          disabled,
          placeholder: "Click to set hotkey",
          className: `input pr-20 cursor-pointer ${isCapturing ? "ring-2 ring-blue-500" : ""}`
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1", children: [
        value && !isCapturing && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            onClick: clearHotkey,
            disabled,
            className: "p-1 text-gray-500 hover:text-gray-300 disabled:opacity-50",
            title: "Clear hotkey",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
          }
        ),
        isCapturing && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-blue-400 animate-pulse", children: "Recording..." })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-xs text-gray-500", children: "Click the input and press your desired key combination (e.g., F8, Ctrl+Shift+R)" })
  ] });
}
function HotkeySettings() {
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
    hotkey: "",
    hotkey_mode: "toggle"
  });
  const [saveStatus, setSaveStatus] = reactExports.useState("idle");
  const originalSettings = reactExports.useRef(localSettings);
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
  }, [fetchSettings]);
  reactExports.useEffect(() => {
    if (settings) {
      const newSettings = {
        hotkey: settings.hotkey,
        hotkey_mode: settings.hotkey_mode || "toggle"
      };
      setLocalSettings(newSettings);
      originalSettings.current = newSettings;
    }
  }, [settings]);
  const handleSave = async () => {
    setSaveStatus("saving");
    const success = await updateSettings({
      hotkey: localSettings.hotkey,
      hotkey_mode: localSettings.hotkey_mode
    });
    if (success) {
      setSaveStatus("saved");
      originalSettings.current = localSettings;
      if (localSettings.hotkey && window.api) {
        await window.api.registerHotkey(localSettings.hotkey, localSettings.hotkey_mode);
      } else if (!localSettings.hotkey && window.api) {
        await window.api.unregisterHotkey();
      }
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
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Hotkey Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Configure keyboard shortcuts for recording" })
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
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Recording Hotkey" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          HotkeyInput,
          {
            value: localSettings.hotkey,
            onChange: (hotkey) => setLocalSettings((prev) => ({ ...prev, hotkey })),
            disabled: isSaving
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-3 text-xs text-[var(--color-text-muted)]", children: "Press any key combination to set it as your recording hotkey. The hotkey works globally even when the app is in the background." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Hotkey Mode" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-start gap-3 cursor-pointer p-3 rounded-lg border border-[var(--color-border)] flex-1 hover:bg-[var(--color-bg-tertiary)] transition-colors", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "radio",
                name: "hotkey_mode",
                value: "toggle",
                checked: localSettings.hotkey_mode === "toggle",
                onChange: () => setLocalSettings((prev) => ({ ...prev, hotkey_mode: "toggle" })),
                disabled: isSaving,
                className: "w-4 h-4 mt-1 text-[var(--color-accent)] bg-[var(--color-bg-secondary)] border-[var(--color-border)]"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)] font-medium", children: "Toggle" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-1", children: "Press to start, press again to stop" })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-start gap-3 cursor-pointer p-3 rounded-lg border border-[var(--color-border)] flex-1 hover:bg-[var(--color-bg-tertiary)] transition-colors", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "radio",
                name: "hotkey_mode",
                value: "push-to-talk",
                checked: localSettings.hotkey_mode === "push-to-talk",
                onChange: () => setLocalSettings((prev) => ({ ...prev, hotkey_mode: "push-to-talk" })),
                disabled: isSaving,
                className: "w-4 h-4 mt-1 text-[var(--color-accent)] bg-[var(--color-bg-secondary)] border-[var(--color-border)]"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)] font-medium", children: "Push-to-talk" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-1", children: "Hold to record, release to stop" })
            ] })
          ] })
        ] })
      ] })
    ] })
  ] });
}
export {
  HotkeySettings as default
};
