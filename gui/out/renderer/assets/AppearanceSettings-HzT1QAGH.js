import { c as useSettingsStore, j as jsxRuntimeExports } from "./index-Cay8ThtR.js";
import { r as reactExports } from "./vendor-CCKbG8cq.js";
import { u as useKeyboardShortcuts, S as SaveStatusIndicator } from "./useKeyboardShortcuts-8hu33O7_.js";
const themes = [
  {
    id: "default",
    name: "Default",
    description: "Clean dark theme with indigo accent",
    colors: { bg: "#0a0a0a", accent: "#6366f1", text: "#fafafa" }
  },
  {
    id: "tokyo-night",
    name: "Tokyo Night",
    description: "Storm variant of the popular Tokyo Night theme",
    colors: { bg: "#1a1b26", accent: "#7aa2f7", text: "#c0caf5" }
  },
  {
    id: "catppuccin",
    name: "Catppuccin Mocha",
    description: "Soothing pastel theme with warm colors",
    colors: { bg: "#1e1e2e", accent: "#89b4fa", text: "#cdd6f4" }
  },
  {
    id: "gruvbox",
    name: "Gruvbox Dark",
    description: "Retro groove colors with warm tones",
    colors: { bg: "#282828", accent: "#83a598", text: "#ebdbb2" }
  },
  {
    id: "everforest",
    name: "Everforest",
    description: "Green forest-inspired comfortable colors",
    colors: { bg: "#2b3339", accent: "#a7c080", text: "#d3c6aa" }
  },
  {
    id: "nord",
    name: "Nord",
    description: "Arctic, north-bluish color palette",
    colors: { bg: "#2e3440", accent: "#88c0d0", text: "#eceff4" }
  },
  {
    id: "kanagawa",
    name: "Kanagawa Wave",
    description: "Inspired by the great wave off Kanagawa",
    colors: { bg: "#1f1f28", accent: "#7e9cd8", text: "#dcd7ba" }
  },
  {
    id: "ayu",
    name: "Ayu Dark",
    description: "Simple, bright colors with warm accent",
    colors: { bg: "#0b0e14", accent: "#e6b450", text: "#bfbdb6" }
  },
  {
    id: "one-dark",
    name: "One Dark",
    description: "Atom One Dark theme colors",
    colors: { bg: "#282c34", accent: "#61afef", text: "#abb2bf" }
  }
];
function AppearanceSettings() {
  const {
    settings,
    isLoading,
    isSaving,
    error,
    fetchSettings,
    updateSettings,
    clearError
  } = useSettingsStore();
  const [selectedTheme, setSelectedTheme] = reactExports.useState(null);
  const [saveStatus, setSaveStatus] = reactExports.useState("idle");
  const originalTheme = reactExports.useRef(null);
  useKeyboardShortcuts({
    onSave: () => handleSave(),
    enabled: saveStatus === "unsaved"
  });
  reactExports.useEffect(() => {
    if (selectedTheme === null) return;
    const isDirty = selectedTheme !== originalTheme.current;
    if (isDirty && saveStatus !== "saving") {
      setSaveStatus("unsaved");
    } else if (!isDirty && saveStatus === "unsaved") {
      setSaveStatus("idle");
    }
  }, [selectedTheme, saveStatus]);
  reactExports.useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);
  reactExports.useEffect(() => {
    if (settings?.theme) {
      setSelectedTheme(settings.theme);
      originalTheme.current = settings.theme;
    }
  }, [settings]);
  reactExports.useEffect(() => {
    if (selectedTheme) {
      document.documentElement.setAttribute("data-theme", selectedTheme);
    }
  }, [selectedTheme]);
  const handleSave = async () => {
    if (!selectedTheme) return;
    setSaveStatus("saving");
    const success = await updateSettings({
      theme: selectedTheme
    });
    if (success) {
      setSaveStatus("saved");
      originalTheme.current = selectedTheme;
    } else {
      setSaveStatus("unsaved");
    }
  };
  const handleThemeChange = (themeId) => {
    setSelectedTheme(themeId);
    document.documentElement.setAttribute("data-theme", themeId);
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center h-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-[var(--color-border)] border-t-[var(--color-accent)] rounded-full animate-spin" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-6 max-w-2xl", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-[var(--color-text-primary)]", children: "Appearance" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mt-1", children: "Customize the look and feel of the application" })
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
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-6", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: "card p-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-base font-medium mb-4 text-[var(--color-text-primary)]", children: "Theme" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-[var(--color-text-muted)] mb-4", children: "Choose a color theme for the application. Changes are previewed immediately." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid grid-cols-1 gap-3", children: themes.map((theme) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "label",
        {
          className: `
                  flex items-center gap-4 p-3 rounded-lg border cursor-pointer
                  transition-all duration-150 ease-out
                  ${selectedTheme === theme.id ? "border-[var(--color-accent)] bg-[var(--color-accent-muted)]" : "border-[var(--color-border)] hover:bg-[var(--color-bg-tertiary)]"}
                `,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "radio",
                name: "theme",
                value: theme.id,
                checked: selectedTheme === theme.id,
                onChange: () => handleThemeChange(theme.id),
                disabled: isSaving || selectedTheme === null,
                className: "sr-only"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "div",
              {
                className: "w-12 h-12 rounded-lg flex items-center justify-center shrink-0 border border-white/10",
                style: { backgroundColor: theme.colors.bg },
                children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    className: "w-4 h-4 rounded-full",
                    style: { backgroundColor: theme.colors.accent }
                  }
                )
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 min-w-0", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-[var(--color-text-primary)]", children: theme.name }),
                selectedTheme === theme.id && /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-4 h-4 text-[var(--color-accent)]", fill: "currentColor", viewBox: "0 0 20 20", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { fillRule: "evenodd", d: "M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z", clipRule: "evenodd" }) })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-[var(--color-text-muted)] mt-0.5 truncate", children: theme.description })
            ] })
          ]
        },
        theme.id
      )) })
    ] }) })
  ] });
}
export {
  AppearanceSettings as default
};
