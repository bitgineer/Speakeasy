import { j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
const SaveStatusIndicator = ({
  status,
  className = ""
}) => {
  const [isVisible, setIsVisible] = reactExports.useState(true);
  reactExports.useEffect(() => {
    let timeoutId;
    if (status === "saved") {
      setIsVisible(true);
      timeoutId = setTimeout(() => {
        setIsVisible(false);
      }, 3e3);
    } else if (status === "idle") {
      setIsVisible(false);
    } else {
      setIsVisible(true);
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [status]);
  if (status === "idle" && !isVisible) return null;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `inline-flex items-center gap-2 text-sm font-medium transition-opacity duration-500 ${isVisible ? "opacity-100" : "opacity-0"} ${className}`,
      "aria-live": "polite",
      children: [
        status === "unsaved" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "relative flex h-2 w-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "relative inline-flex rounded-full h-2 w-2 bg-yellow-500" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-gray-400", children: "Unsaved changes" })
        ] }),
        status === "saving" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "svg",
            {
              className: "animate-spin h-4 w-4 text-blue-500",
              xmlns: "http://www.w3.org/2000/svg",
              fill: "none",
              viewBox: "0 0 24 24",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "circle",
                  {
                    className: "opacity-25",
                    cx: "12",
                    cy: "12",
                    r: "10",
                    stroke: "currentColor",
                    strokeWidth: "4"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "path",
                  {
                    className: "opacity-75",
                    fill: "currentColor",
                    d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  }
                )
              ]
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-gray-400", children: "Saving..." })
        ] }),
        status === "saved" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              className: "h-4 w-4 text-green-500",
              fill: "none",
              strokeLinecap: "round",
              strokeLinejoin: "round",
              strokeWidth: "2",
              viewBox: "0 0 24 24",
              stroke: "currentColor",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { d: "M5 13l4 4L19 7" })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-gray-400", children: "Saved" })
        ] })
      ]
    }
  );
};
function useKeyboardShortcuts(config) {
  const { onSave, onEscape, onToggleRecording, enabled = true } = config;
  reactExports.useEffect(() => {
    if (!enabled) return;
    const handleKeyDown = (event) => {
      const target = event.target;
      const isInputElement = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement;
      if ((event.metaKey || event.ctrlKey) && event.key === "s") {
        event.preventDefault();
        onSave?.();
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        onEscape?.();
        return;
      }
      if (event.key === " " && !isInputElement) {
        event.preventDefault();
        onToggleRecording?.();
        return;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled, onSave, onEscape, onToggleRecording]);
}
export {
  SaveStatusIndicator as S,
  useKeyboardShortcuts as u
};
