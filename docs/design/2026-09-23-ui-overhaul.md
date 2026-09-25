# UI overhaul

Status: direction decided (A, Refined dark), Phase 2 starting. Branch `feat/ui-overhaul`, stacked on `feat/ai-processing-modes` at `27f37e0`. The AI processing feature is code-complete and gate-verified there. Its PR is deferred until this overhaul lands.

## Problem

The owner wants the entire interface redone: every page, every field, every selector. No designs exist. The standard to build and judge against is the `better-*` skill family (`better-interface`, `better-accessibility`, `better-layout`, `better-writing`, `better-typography`, `better-colors`, `better-ui`), with `variant` for direction exploration, `break` for state stress, and `interface-review` for change reviews.

The current UI is a half-built system. `styles/tokens.css` defines spacing, type, shadow, radius, and motion tokens. `styles/themes.css` defines nine dark color themes. Components style themselves almost entirely through 554 direct `var(--...)` references; the Tailwind token utilities are nearly unused (13 named token classes). The config maps `primary`/`success`/`warning`/`error`/`info` scales to variables that do not exist in the stylesheets, and 14 usages of those classes in the ui primitives render with no color at all. Twenty-seven raw hex values are mostly theme-preview swatches in Appearance settings, which is data rather than drift. No light theme exists. There is no rendered baseline, no repository-scope audit, and no automated interface gate. The repo has no interface guidelines beyond `CONTRIBUTING.md`, which does not cover design.

## Inventory (44 tsx files)

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

## Known starting findings (verified)

- Semantic scale classes are broken. `gui/tailwind.config.js` maps `primary`, `success`, `warning`, `error`, and `info` to `--color-*-N00` variables that no stylesheet defines. `ui/badge.tsx` variants, `ui/input.tsx` error state, and `ui/label.tsx` use them, so those states render with no color. 14 usages.
- Direct `var(--...)` references dominate (554) while token utilities are nearly unused (13). Theme changes today depend on every component spelling the same variable names by hand.
- The nine community themes are dark-only. No light theme exists.
- The 27 raw hex values are theme swatches in Appearance settings, intentional data rather than drift.

## Definition of done (falsifiable)

1. A committed capture script produces baseline and after images for every surface and state; both runs exist as artifacts. The tray menu is captured manually, since a native menu cannot be screenshotted through CDP.
2. A repository-scope `better-interface` review at the end reports no HIGH findings and no unresolved MEDIUM findings; accepted exceptions are listed with reasons.
3. Every escalation trigger in `better-interface` is clear. Named controls, visible focus, keyboard reachability, reduced-motion support, 320px and 200% zoom containment, AA contrast, no color-only meaning, confirmations for destructive actions, truncation escape hatches, recoverable errors.
4. One token layer is the only source of visual values. A committed check reconciles three layers: component usage, the Tailwind config mapping, and the CSS variable definitions. It fails on raw hex, one-off px, dangling `var()` references, token classes the config never generates, and scale mappings with no defined variable.
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

## Decision (2026-09-23)

Direction A, Refined dark, chosen from renders. At the app's real window size (900x670) A shows three history records and most of the provider form; B shows two records and a sliver of the form. The app runs in short sessions and its settings pages carry a lot of fields, so density wins. Renders are committed under `docs/design/ui-prototypes/`.

Adopted from B: the two-tier semantic token discipline, the measured-contrast table as a working method, and the warm light palette as the Light theme in the same semantic names. A's control calibration moves up slightly during Phase 2, with a minimum text size of 11px and controls raised from 32px where the layout allows.

Theme story, settled: Light, Dark, and System plus two accent presets (A's violet, B's ink blue). The nine community themes are preserved unwired in `community-themes.css` and return later as skins over the semantic layer. A stored community theme maps to Dark until then.

Baseline note: the pre-change state is committed at `1461218`. The Phase 0 capture harness is built in Phase 2, and the baseline images are captured from a worktree at that commit, so no before state is lost.

## Phases

- **Phase 0. Harness and audit.** Build the capture script using the project-local `verify-speakeasy` skill (Electron over CDP plus the backend), which already exists at `.opencode/skills/verify-speakeasy`. Add an e2e scaffold only if a browser suite earns its place. Capture every surface and state. Run the repository-scope `better-interface` review and file the ranked findings as the work list. Gate: captures exist, audit list reviewed.
- **Phase 1. Direction.** `variant` builds the shell plus Dashboard plus Processing settings in the shortlisted directions against real data. Side-by-side captures. Owner picks. Gate: signed-off direction.
- **Phase 2. Tokens and primitives.** Rebuild `tokens.css` and `themes.css` to the chosen direction. Rebuild `ui/*` and add select, combobox, and field primitives. Land the token check. Gate: primitives pass `break` and the accessibility checks, token check green.
- **Phase 3. Shell and first pages.** Sidebar, page frame, settings layout pattern, Dashboard including its History section.
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
