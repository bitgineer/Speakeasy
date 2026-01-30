import { j as jsxRuntimeExports, c as useSettingsStore } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
function DeviceSelector({
  devices,
  selectedDevice,
  onChange,
  disabled = false,
  isConnecting = false,
  error = null
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "label", children: "Audio Input Device" }),
      isConnecting && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center text-xs text-[var(--color-info)] animate-pulse", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { className: "animate-spin -ml-1 mr-2 h-3 w-3 text-[var(--color-info)]", xmlns: "http://www.w3.org/2000/svg", fill: "none", viewBox: "0 0 24 24", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { className: "opacity-25", cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("path", { className: "opacity-75", fill: "currentColor", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })
        ] }),
        "Connecting..."
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "select",
      {
        value: selectedDevice || "",
        onChange: (e) => onChange(e.target.value),
        disabled: disabled || devices.length === 0 || isConnecting,
        className: `select ${isConnecting ? "opacity-50 pointer-events-none" : ""}`,
        children: devices.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "No devices found" }) : devices.map((device) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: device.name, children: [
          device.name,
          device.is_default ? " (Default)" : ""
        ] }, device.id))
      }
    ),
    error && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-1 text-xs text-[var(--color-error)] flex items-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "mr-1", children: "x" }),
      " ",
      error
    ] }),
    selectedDevice && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-1 text-xs text-[var(--color-text-muted)]", children: [
      devices.find((d) => d.name === selectedDevice)?.channels || 0,
      " channel(s),",
      " ",
      (devices.find((d) => d.name === selectedDevice)?.sample_rate || 0) / 1e3,
      "kHz"
    ] })
  ] });
}
const DeviceSelector$1 = reactExports.memo(DeviceSelector);
function AudioSettings() {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    availableDevices,
    fetchSettings,
    fetchDevices,
    setDevice,
    clearError
  } = useSettingsStore();
  reactExports.useEffect(() => {
    fetchSettings();
    fetchDevices();
  }, [fetchSettings, fetchDevices]);
  const handleDeviceChange = async (deviceName) => {
    await setDevice(deviceName);
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-2xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Audio Settings" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Configure audio input device" })
    ] }),
    error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6 p-3 bg-[var(--color-error-muted)] border border-[var(--color-error)] rounded-lg flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-error)] text-sm", children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: clearError, className: "text-[var(--color-error)] hover:opacity-80", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Input Device" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          DeviceSelector$1,
          {
            devices: availableDevices,
            selectedDevice: settings?.device_name || null,
            onChange: handleDeviceChange,
            disabled: isSaving
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-3 text-xs text-[var(--color-text-muted)]", children: "Select the microphone or audio input device to use for transcription. Changes take effect immediately." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Tips for Best Results" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: "space-y-2 text-sm text-[var(--color-text-secondary)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Use a dedicated microphone for best audio quality" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Keep the microphone close to reduce background noise" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Speak clearly and at a moderate pace" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Minimize background noise when recording" })
          ] })
        ] })
      ] })
    ] })
  ] });
}
export {
  AudioSettings as default
};
