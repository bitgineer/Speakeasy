# Phase 5 report (committed c03eb9a; branch feat/ui-overhaul)
## Files changed
- `gui/src/renderer/src/pages/settings/ModelSettings.tsx` rebuilt: page head, selection and compute panels, downloaded-models rows, reload warning; save/load/sync/delete/clear flows and GPU gating unchanged.
- `gui/src/renderer/src/pages/settings/BehaviorSettings.tsx` rebuilt: switch rows, conditional filler-words field and live-transcription controls; draft/save payload unchanged.
- `gui/src/renderer/src/pages/settings/HotkeySettings.tsx` rebuilt: binding rows with capture field, trigger/mode selects, remove; dirty/duplicate/invalid logic and registration toast unchanged.
- `gui/src/renderer/src/pages/settings/AudioSettings.tsx` rebuilt: device panel, tips list; fetch/set-device flow unchanged.
- `gui/src/renderer/src/pages/settings/AppearanceSettings.tsx` rebuilt: theme and accent option cards (Phase 2 selectors kept); preview/save/store-accent logic unchanged.
- `gui/src/renderer/src/pages/settings/DataSettings.tsx` rebuilt: import (merge checkbox, JSON file button, status), export dialog trigger, privacy note; import flow unchanged.
- `gui/src/renderer/src/pages/settings/ProcessingSettings.tsx` rebuilt to A's two-column grid: providers, tone profiles, focused-app row, default tone, command prompt; every handler and API call unchanged.
- `gui/src/renderer/src/pages/settings/AboutSettings.tsx` rebuilt: app facts, technology table, feature list; version fetch unchanged.
- `gui/src/renderer/src/components/SaveStatusIndicator.tsx` tokenized; visibility timing, aria-live, and onSave-only Save button unchanged.
- `gui/src/renderer/src/components/DeviceSelector.tsx` tokenized; disabled logic and device details unchanged.
- `gui/src/renderer/src/components/HotkeyInput.tsx` tokenized; capture logic unchanged; capture field and clear button gained aria-labels.
- `gui/src/renderer/src/components/ModelSelector.tsx` tokenized selects and metadata pills; option text and store reads unchanged.
- `gui/src/renderer/src/styles/globals.css` new tokenized settings vocabulary (fields, switch, subpanel, tone, option cards, table, banners, save state) in A's direction; both themes via semantic names only.
- `gui/scripts/check-tokens.mjs` baselines lowered: legacy 283 -> 40, arbitrary 17 -> 5.
- `docs/design/ui-captures/phase5/` 16 before PNGs + this report. `ExportDialog.tsx` and `ModelDownloadDialog.tsx` untouched (dialogs are Phase 6).

## Gates (each exit 0 unless noted)
- `npm run lint` -> `Warning: React version not specified in eslint-plugin-react settings.` (pre-existing)
- `npm run typecheck` -> main and renderer clean
- `npm test` -> `Test Files 6 passed (6)`, `Tests 41 passed (41)`
- `npm run check:tokens` -> `arbitrary or raw-color values in tsx: 5 (baseline 5)`, `legacy --color-* usages: 40`, `check:tokens OK`
- `npm run capture:ui -- --out %TEMP%\opencode\ui-captures\phase5 --theme dark,light` -> exit 1: `capture:ui failed: port 8765 is in use; close the running SpeakEasy app or stop its backend first`
- Extra evidence (not a requested gate): `npm run build` -> `✓ built in 4.32s`, every new class present in the emitted CSS.

## Ratchets
legacy 283 -> 40 (baseline 283 -> 40; 243 migrated, floor ExportDialog 36 + RecordingIndicator 4); arbitrary 17 -> 5 (baseline 17 -> 5; 12 migrated, floor LoadingSpinner 1 + RecordingPill 4).

## Captures
After: blocked (0 files). The user's app holds port 8765 and was not stopped, per the brief. Close the app and rerun the command to produce the 8 settings after pairs; Batch and Stats after pairs (the Phase 4 gap) are deferred to the same rerun.
Before (16) copied from `%TEMP%\opencode\ui-captures\baseline-1461218`: `settings-{model,behavior,hotkey,audio,appearance,data,processing,about}-before-1461218-{dark,light}.png`. Every dark/light pair is byte-identical because no light theme existed at `1461218`; the `-light` copies are kept so the after set pairs name-for-name.

## Deviations
- Processing uses A's own responsive breakpoint: the provider/tone grid collapses at <=950px, so the 900px window stacks it; side-by-side appears on wider windows.
- A's Processing "readiness" banner omitted: no existing state backs provider reachability, and inventing status exceeds behavior preservation.
- Behavior's nested "Always show Ready status" row renders conditionally instead of max-height-hidden; this also drops a focusable hidden input, and the save payload is unchanged.
- Copy lightly normalized to sentence case in heads and buttons; the full `better-writing` pass is Phase 7.
- Jev review baseline (focused submission): correctness 8.1, readability 8.6, consistency 8.5, compatibility 8.7; only weak metric was testQuality 5.3 (low, pre-existing repo-wide gap with no in-scope lever). Fix after review: accessible names on the hotkey capture field and clear button.
