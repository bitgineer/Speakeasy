import { c as useSettingsStore, j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1e3);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}
function AudioWaveform() {
  const bars = [0.4, 0.7, 1, 0.6, 0.8, 0.5, 0.9, 0.6, 1, 0.7];
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center gap-[3px] h-6 mx-3", children: bars.map((height, i) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: "w-[3px] rounded-full bg-red-500/90 shadow-[0_0_8px_rgba(239,68,68,0.5)]",
      style: {
        animation: `waveform 0.8s ease-in-out infinite`,
        animationDelay: `${i * 0.08}s`,
        height: `${height * 100}%`
      }
    },
    i
  )) });
}
function RecordingIndicator() {
  const [duration, setDuration] = reactExports.useState(0);
  const [status, setStatus] = reactExports.useState("idle");
  const [isLocked, setIsLocked] = reactExports.useState(false);
  const startTimeRef = reactExports.useRef(0);
  const contentRef = reactExports.useRef(null);
  const { settings, fetchSettings } = useSettingsStore();
  const updateWindowSize = reactExports.useCallback(() => {
    if (contentRef.current) {
      const rect = contentRef.current.getBoundingClientRect();
      const width = Math.ceil(rect.width);
      const height = Math.ceil(rect.height);
      window.api?.resizeIndicator?.(width, height);
    }
  }, []);
  reactExports.useLayoutEffect(() => {
    updateWindowSize();
  }, [status, isLocked, updateWindowSize]);
  reactExports.useEffect(() => {
    if (status === "recording" && duration % 5e3 < 100) {
      updateWindowSize();
    }
  }, [duration, status, updateWindowSize]);
  reactExports.useEffect(() => {
    const originalHtmlBg = document.documentElement.style.background;
    const originalBodyBg = document.body.style.background;
    const originalBodyOverflow = document.body.style.overflow;
    document.documentElement.style.setProperty("background", "transparent", "important");
    document.body.style.setProperty("background", "transparent", "important");
    document.body.style.setProperty("overflow", "hidden", "important");
    fetchSettings();
    const interval = setInterval(() => fetchSettings(), 2e3);
    return () => {
      document.documentElement.style.background = originalHtmlBg;
      document.body.style.background = originalBodyBg;
      document.body.style.overflow = originalBodyOverflow;
      clearInterval(interval);
    };
  }, [fetchSettings]);
  reactExports.useEffect(() => {
    if (!settings) return;
    const showFeature = settings.show_recording_indicator ?? true;
    const alwaysShow = settings.always_show_indicator ?? true;
    if (!showFeature) {
      window.api?.hideIndicator?.();
      return;
    }
    if (status === "idle") {
      if (alwaysShow) {
        window.api?.showIndicator?.();
      } else {
        window.api?.hideIndicator?.();
      }
    } else {
      window.api?.showIndicator?.();
    }
  }, [status, settings]);
  reactExports.useEffect(() => {
    if (status !== "recording") {
      return;
    }
    startTimeRef.current = Date.now();
    setDuration(0);
    const interval = setInterval(() => {
      setDuration(Date.now() - startTimeRef.current);
    }, 100);
    return () => clearInterval(interval);
  }, [status]);
  reactExports.useEffect(() => {
    window.api?.getRecordingStatus?.().then((isActive) => {
      if (isActive) {
        setStatus("recording");
        setIsLocked(false);
      }
    });
    const unsubStart = window.api?.onRecordingStart(() => {
      setStatus("recording");
      setIsLocked(false);
      setDuration(0);
    });
    const unsubLocked = window.api?.onRecordingLocked?.(() => {
      setIsLocked(true);
    });
    const unsubComplete = window.api?.onRecordingComplete(() => {
      setStatus("idle");
      setIsLocked(false);
    });
    const unsubError = window.api?.onRecordingError(() => {
      setStatus("idle");
      setIsLocked(false);
    });
    return () => {
      unsubStart?.();
      unsubLocked?.();
      unsubComplete?.();
      unsubError?.();
    };
  }, []);
  if (status === "idle") {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center w-full h-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        ref: contentRef,
        className: "\n            flex items-center h-9 px-4 rounded-full\n            bg-[#0a0a0a]/60 backdrop-blur-sm\n            border border-zinc-800/30\n            shadow-lg hover:bg-[#0a0a0a]/80 hover:border-zinc-700/50 transition-all\n            cursor-default select-none\n          ",
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 rounded-full bg-zinc-500 mr-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs font-medium text-zinc-400", children: "Ready" })
        ]
      }
    ) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center w-full h-full overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: contentRef,
        className: `
          flex items-center h-12 px-1 pl-2 rounded-full
          bg-[#0a0a0a]/90 backdrop-blur-md
          border ${isLocked ? "border-yellow-500/50" : "border-zinc-800/50"}
          shadow-lg shadow-black/40
          transition-all duration-300
        `,
        children: status === "recording" ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative flex items-center justify-center w-8 h-8 ml-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `absolute w-full h-full rounded-full ${isLocked ? "bg-yellow-500/20" : "bg-red-500/20"} animate-ping opacity-75` }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `w-2.5 h-2.5 rounded-full ${isLocked ? "bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.8)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]"}` })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(AudioWaveform, {}),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center justify-center min-w-[60px] mx-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `text-sm font-mono font-bold ${isLocked ? "text-amber-400" : "text-zinc-100"} tracking-wide`, children: formatTime(duration) }),
            isLocked && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[9px] font-bold text-amber-500 uppercase leading-none mt-0.5 animate-pulse", children: "LOCKED" })
          ] }),
          isLocked && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center text-amber-500 mr-2 animate-in fade-in slide-in-from-left-2 duration-300", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-3.5 h-3.5 mr-1", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[10px] font-medium whitespace-nowrap opacity-80", children: "Press hotkey to stop" })
          ] }),
          !isLocked && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-px h-5 bg-zinc-800 mx-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: () => window.api?.cancelRecording?.(),
              className: "\n                flex items-center justify-center w-7 h-7 rounded-full\n                text-zinc-500 hover:text-white hover:bg-zinc-800\n                transition-all mr-1\n              ",
              title: "Cancel Recording",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) })
            }
          )
        ] }) : (
          /* Transcribing State */
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 px-3", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-4 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-zinc-200", children: "Transcribing..." })
          ] })
        )
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx("style", { children: `
        @keyframes waveform {
          0%, 100% { height: 30%; opacity: 0.6; }
          50% { height: 100%; opacity: 1; }
        }
      ` })
  ] });
}
export {
  RecordingIndicator as default
};
