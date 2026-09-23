# UI overhaul

Status: framed, not started. Branch `feat/ui-overhaul`, stacked on `feat/ai-processing-modes` at `27f37e0`. The AI processing feature is code-complete and gate-verified there. Its PR is deferred until this overhaul lands.

## Problem

The owner wants the entire interface redone: every page, every field, every selector. No designs exist. The standard to build and judge against is the `better-*` skill family (`better-interface`, `better-accessibility`, `better-layout`, `better-writing`, `better-typography`, `better-colors`, `better-ui`), with `variant` for direction exploration, `break` for state stress, and `interface-review` for change reviews.

The current UI is a half-built system. `styles/tokens.css` defines spacing, type, shadow, radius, and motion tokens. `styles/themes.css` defines nine dark color themes. Components mix three dialects: 554 direct `var(--...)` usages, 27 raw hex values, and 242 Tailwind token classes. No light theme exists. There is no rendered baseline, no repository-scope audit, and no automated interface gate. The repo has no interface guidelines beyond `CONTRIBUTING.md`, which does not cover design.

## Inventory (43 tsx files)

| Group | Surfaces |
|---|---|
| Pages | Dashboard, Batch, Stats |
| Settings pages | About, Appearance, Audio, Behavior, Data, Hotkey, Model, Processing |
| Overlay | OverlayContainer, IdlePill, RecordingPill, TranscribingLine, RecordingIndicator |
| Shell | App, Sidebar, Toast, ToastProvider, ErrorBoundary |
| Feature components | HistoryItem, HistoryItemSkeleton, ExportDialog, HotkeyInput, DeviceSelector, ModelSelector, ModelDownloadDialog, ModelLoadingBanner, ModeChips, Pagination, ConfidenceText, LoadingSpinner, SaveStatusIndicator |
| Primitives | ui/button, ui/input, ui/label, ui/dialog, ui/card, ui/badge, ui/icon |
| Tokens | styles/tokens.css, styles/themes.css, styles/globals.css |

States to capture and re-verify for every interactive surface: default, hover, focus, active, disabled, loading, empty, error, long text, narrow width, and 200% zoom.

## Definition of done (falsifiable)

1. A committed capture script produces baseline and after images for every surface and state; both runs exist as artifacts.
2. A repository-scope `better-interface` review at the end reports no HIGH findings and no unresolved MEDIUM findings; accepted exceptions are listed with reasons.
3. Every escalation trigger in `better-interface` is clear. Named controls, visible focus, keyboard reachability, reduced-motion support, 320px and 200% zoom containment, AA contrast, no color-only meaning, confirmations for destructive actions, truncation escape hatches, recoverable errors.
4. One token layer is the only source of visual values. A committed check fails on raw hex, one-off px, and unmapped var usage in components.
5. Every interactive component renders its empty, loading, error, disabled, and long-text states, proven by `break`.
6. Copy passes `better-writing` across every surface.
7. The app runs every flow with the existing test suites green, driven live via `verify-speakeasy`.

## Rigor

High. The token layer and primitives are a one-way door that reaches every page. Visual work needs before and after evidence, not opinion.

## Direction options

The direction is a product call. Each option is prototyped on the same two screens (Dashboard and the Processing settings page) before commitment.

- **A. Refined dark.** Keep the current near-black and violet identity. Rebuild it properly: coherent tokens, real hierarchy, consistent spacing, restrained color, unified states. Fastest path, zero identity risk.
- **B. Calm light-first.** Light becomes the default surface with a first-class dark mode. Editorial spacing and typography, soft surfaces, quiet chrome. Biggest visual change, most work in the token layer, two modes to maintain.
- **C. Ambient minimal.** Fewer chrome elements, generous space, one accent, larger type, the overlay and the transcript as the heroes. Closest to the marketing voice, hardest to execute well across dense settings screens.

Recommendation: prototype A and B, choose one, then reduce the theme story to Light, Dark, and System plus two or three accent presets. The nine community themes can return later as color skins over the semantic layer.

## Phases

- **Phase 0. Harness and audit.** Build the capture script (Electron over CDP via `verify-speakeasy`, or a Playwright Electron scaffold under `gui/e2e`, which currently does not exist). Capture every surface and state. Run the repository-scope `better-interface` review and file the ranked findings as the work list. Gate: captures exist, audit list reviewed.
- **Phase 1. Direction.** `variant` builds the shell plus Dashboard plus Processing settings in the shortlisted directions against real data. Side-by-side captures. Owner picks. Gate: signed-off direction.
- **Phase 2. Tokens and primitives.** Rebuild `tokens.css` and `themes.css` to the chosen direction. Rebuild `ui/*` and add select, combobox, and field primitives. Land the token check. Gate: primitives pass `break` and the accessibility checks, token check green.
- **Phase 3. Shell and first pages.** Sidebar, page frame, settings layout pattern, Dashboard, History.
- **Phase 4. Batch and Stats.**
- **Phase 5. Settings pages,** including Processing and the mode chips.
- **Phase 6. Overlay, tray menu, dialogs, toasts.**
- **Phase 7. Copy and certification.** `better-writing` pass, `break` across components, per-page `interface-review` sweep.
- **Phase 8. Whole-app verification and PR.** Drive every flow, compare against baseline, open the PR.

## Open questions

- Light mode in scope now or dark-only for this pass?
- Density. Comfortable or compact? The settings pages carry many fields.
- Theme story. Keep nine community themes, or ship Light, Dark, System plus a few accents?
- Is the overlay treated as a first-class surface (idle, recording, processing, error) in every phase?
- Windows is the only tested platform here. macOS and Linux need a visual pass before release.
