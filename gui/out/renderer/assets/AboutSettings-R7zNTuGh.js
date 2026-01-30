import { j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
function AboutSettings() {
  const [version, setVersion] = reactExports.useState("...");
  reactExports.useEffect(() => {
    window.api?.getVersion().then((v) => setVersion(v)).catch(() => setVersion("Unknown"));
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-2xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "About" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Application information" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4 mb-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-16 rounded-2xl bg-[var(--color-accent)] flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-10 h-10 text-[var(--color-text-on-accent)]", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" }) }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-bold text-[var(--color-text-primary)]", children: "SpeakEasy" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)]", children: "Open-source voice transcription" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-4 text-sm", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-muted)]", children: "Version" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-[var(--color-text-primary)] font-medium", children: version })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-muted)]", children: "License" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-[var(--color-text-primary)] font-medium", children: "MIT" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Technology" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2 border-b border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-secondary)]", children: "Desktop Framework" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Electron" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2 border-b border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-secondary)]", children: "Frontend" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "React + TypeScript" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2 border-b border-[var(--color-border)]", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-secondary)]", children: "Backend" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "FastAPI (Python)" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between py-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-secondary)]", children: "ASR Engine" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-[var(--color-text-primary)]", children: "Whisper / faster-whisper" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Key Features" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: "space-y-2 text-sm text-[var(--color-text-secondary)]", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "100% local processing - your data never leaves your device" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Global hotkey support for quick voice-to-text" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Multiple Whisper model sizes for accuracy vs speed tradeoffs" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "GPU acceleration (CUDA) for faster transcription" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Batch transcription for audio files" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-5 h-5 text-[var(--color-success)] shrink-0 mt-0.5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Customizable themes and appearance" })
          ] })
        ] })
      ] })
    ] })
  ] });
}
export {
  AboutSettings as default
};
