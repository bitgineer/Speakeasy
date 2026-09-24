# Phase 6 report (uncommitted working tree on HEAD 5241f3f; branch feat/ui-overhaul)

## Files changed
- `gui/src/renderer/src/components/Overlay/IdlePill.tsx` rebuilt: solid `--surface-panel` pill, accent glyph, hover/focus label reveal; title, mode label, and hover-scale motion unchanged.
- `gui/src/renderer/src/components/Overlay/RecordingPill.tsx` rebuilt: danger dot with pulse ring, lock, mode badge, mono timer, divider, stop/cancel; time math and handlers unchanged, buttons gained aria-labels.
- `gui/src/renderer/src/components/Overlay/TranscribingLine.tsx` rebuilt: panel pill with accent spinner; "Processing..." unchanged.
- `gui/src/renderer/src/components/Overlay/OverlayContainer.tsx` transition moved to duration/ease tokens; mouse pass-through toggling unchanged.
- `gui/src/renderer/src/components/RecordingIndicator.tsx` loading pill and live caption tokenized; `overlay-root` class added; every state/visibility/resize effect untouched.
- `gui/src/renderer/src/components/ExportDialog.tsx` rebuilt on the `ui/dialog` primitive: format, metadata, date range, confirm/cancel flows unchanged; Escape/outside-click/X-close and focus trapping are additive.
- `gui/src/renderer/src/components/ModelDownloadDialog.tsx` rebuilt on the same primitive: status heading, progress track/fill, error block, cancel/retry/close unchanged.
- `gui/src/renderer/src/components/Toast.tsx` rebuilt: `data-tone` styling, lucide icons, close button; 300ms exit and provider lifecycle unchanged.
- `gui/src/renderer/src/components/LoadingSpinner.tsx` `min-h-[200px]` moved to `.loading-panel`; token spinner with `role="status"`.
- `gui/src/renderer/src/styles/globals.css` new overlay/dialog/toast vocabulary on semantic tokens; `body:has(.overlay-root)` makes the transparent overlay window actually transparent.
- `gui/src/renderer/src/styles/tokens.css` legacy `--color-*` alias block deleted (48 names).
- `gui/scripts/check-tokens.mjs` ratchets pinned: `LEGACY_BASELINE` 40 -> 0, `ARBITRARY_BASELINE` 5 -> 0.
- `gui/scripts/capture-ui.mjs` adds an export-dialog capture and an overlay-idle capture from the second CDP target; scratch settings keep the indicator visible; theme/screenshot steps factored into helpers.
- `gui/src/main/tray.ts` "Open Dashboard" -> "Dashboard" to match the sidebar label; icon states, tooltips, and menu actions unchanged.
- `gui/vitest.config.ts` adds the `@` alias already declared in `tsconfig.web.json`.
- `gui/src/renderer/src/test/phase6-surfaces.test.tsx` new: export cancel/confirm/single-record, download error/retry/cancel, overlay stop/cancel wiring, toast tones and exit timing (10 tests).
- `docs/design/ui-captures/phase6/` this report + dashboard before pair (dialog-backdrop context only).

## Gates (each exit 0 unless noted)
- `npm run lint` -> `Warning: React version not specified in eslint-plugin-react settings.` (pre-existing)
- `npm run typecheck` -> main and renderer clean
- `npm test` -> `Test Files 7 passed (7)`, `Tests 51 passed (51)`
- `npm run check:tokens` -> `arbitrary or raw-color values in tsx: 0 (baseline 0)`, `legacy --color-* usages: 0`, `check:tokens OK`, `semantic names per theme: 38 dark / 38 light`
- `npm run build` -> `✓ built in 4.72s`
- `npm run capture:ui -- --out C:\Users\Jack\AppData\Local\Temp\opencode\ui-captures\phase6 --theme dark,light` -> exit 1: `capture:ui failed: port 8765 is in use; close the running SpeakEasy app or stop its backend first`

## Ratchets
legacy 40 -> 0 (both remaining consumers migrated, alias block deleted, baseline pinned at 0). arbitrary 5 -> 0 (RecordingPill 3 + IdlePill 1 rebuilt, LoadingSpinner 1 moved into `.loading-panel`; baseline pinned at 0).

## Captures
After: blocked (0 files). The user's app holds port 8765 (python pid 47008) and was not stopped, per the brief. Both capture extensions are implemented and `node --check`-clean but unexecuted; the next run with the port free emits `12-export-dialog-{dark,light}.png` and `13-overlay-idle-{dark,light}.png` next to the 11 routes.
Before: `baseline-1461218` holds only the 11 route screens; the overlay, dialogs, and toasts were never captured before the overhaul, so this phase has no true before. The dashboard pair is copied as the dialog-backdrop context (light is byte-identical: 1461218 had no light theme).
Toast capture: not shipped. The only triggers are hotkey-registration failure (OS-level conflict, environment-dependent) and the AI-processing warning (requires a real recording); neither is deterministic over CDP, so it is reported instead of shipped flaky.

## Deviations
- Overlay transparency fix: `body` painted `--surface-canvas`, so the frameless "transparent" window rendered an opaque slab around the pill; `body:has(.overlay-root)` clears it. Pill surfaces are solid `--surface-panel` with border and `--shadow-panel` in both themes.
- Dialogs now ride the Phase 2 Radix primitive; the manual title ids were dropped so Radix's `aria-labelledby` wiring stays intact (verified in the mounted DOM).
- Timer drops 18px -> `--text-heading` (15px) and the mode badge 10px -> `--text-label` (11px) to stay on the token scale and Phase 2's 11px minimum.
- Recording/locked/processing overlay states and the tray icon were not visually re-captured (no deterministic CDP trigger without a real recording); recording-pill stop/cancel wiring is covered by the new test instead.
- Jev review (focused submission, 3 rounds): baseline correctness 7.5 / testQuality 5.9 / documentation 7.5; after the test file and why-comment, testQuality 7.4, documentation 8.2, no regressions; round 3 held in the 7.0-8.5 band, so the loop stopped. Remaining findings are generic low-severity with no located lever; the capture gap is the port block.
