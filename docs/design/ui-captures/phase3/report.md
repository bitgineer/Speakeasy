# Phase 3 report (committed d4b8248; branch feat/ui-overhaul)

## Files changed
- `gui/scripts/capture-ui.mjs` (new) isolated 900x670 route harness; `gui/scripts/fixtures/capture-history.json` (new) 4-record seed incl. AI-processed and long text; `gui/package.json` adds `capture:ui`.
- `gui/src/renderer/src/utils/navigation.ts` (new) one nav table for sidebar and breadcrumb. It first landed under `lib/`, which the root ignore rule swallows, so it moved.
- `gui/src/renderer/src/components/Sidebar.tsx` compact 34px rows, uppercase Settings label, lucide glyphs, aria-current, connection footer.
- `gui/src/renderer/src/App.tsx` shell grid, topbar (breadcrumb + status), skip link.
- `gui/src/renderer/src/pages/Dashboard.tsx` page head, counts, Export, mode segmented row, search row, pinned pagination.
- `gui/src/renderer/src/components/HistoryItem.tsx` record card, Processed/Original, Copy/Export/Delete, 2-line clamp with Show full text.
- `gui/src/renderer/src/components/ModeChips.tsx`, `Pagination.tsx`, `HistoryItemSkeleton.tsx` rebuilt on semantic tokens, behavior unchanged.
- `gui/src/renderer/src/styles/globals.css` A's frame/record/segmented/pill classes tokenized; `#root { height: 100% }`.
- `gui/scripts/check-tokens.mjs` both baselines lowered.

## Gates (each exit 0)
- `npm run lint` -> `Warning: React version not specified in eslint-plugin-react settings.` (pre-existing)
- `npm run typecheck` -> main and renderer clean
- `npm test` -> `Test Files 6 passed (6)`, `Tests 41 passed (41)`
- `npm run check:tokens` -> `arbitrary or raw-color values in tsx: 17 (baseline 17)`, `legacy --color-* usages: 407`
- `npm run capture:ui -- --out %TEMP%\opencode\ui-captures\phase3-final --theme dark,light` -> 22 captures, all 900x670

## Ratchets
legacy 527 -> 407 (baseline 554 -> 407); arbitrary 19 -> 17 (baseline 19 -> 17).

## Baseline
Succeeded. Worktree `%TEMP%\opencode\speakeasy-baseline-1461218` with junctions `gui\node_modules` and `backend\.venv`; 22 PNGs under `%TEMP%\opencode\ui-captures\baseline-1461218`.
Baseline light files are byte-identical to dark (no light theme existed at 1461218).

## Captures
- after (22): `01-dashboard`, `02-batch`, `03-stats`, `04-settings-model`, `05-settings-behavior`, `06-settings-hotkey`, `07-settings-audio`, `08-settings-appearance`, `09-settings-data`, `10-settings-processing`, `11-settings-about`, each `-dark.png` and `-light.png`.
- baseline (22): same names under `baseline-1461218\` (only `01-dashboard-*` copied).
- committed: `dashboard-before-1461218-{dark,light}.png`, `dashboard-after-phase3-{dark,light}.png`.

## Deviations
- Electron ignores USERPROFILE for `app.getPath('home')`, so a GUI cannot read an isolated settings file. The harness runs the isolated backend on the real settings port with a preflight, as verify-speakeasy does.
- Stopped an orphaned SpeakEasy backend pair (pids 30244/35448, dead parent, no GUI) holding 8765; no data touched, the app restarts it on next launch.
- `--theme` forces `data-theme`/`data-accent` so captures are deterministic.
- `ExportDialog.tsx` untouched (dialog pass is Phase 6; its legacy aliases remain).
- A's mode/tone record pills omitted: `TranscriptionRecord` carries no mode or tone field.
- Live pass via verify-speakeasy: search, clear, copy, Original/Processed, delete with confirm, next/first page, mode chip write (`active_mode=write`), export dialog open/cancel.
- The live-pass delete hit the isolated scratch store (`.verify/runs/20260923-190207/home/.speakeasy/speakeasy.db`, 64 to 63 rows). The real store was not modified; its mtime predates the run and it holds 1329 rows.
- Route markers were hardened after review: a route now needs its marker plus at least 15 words of `main` text, so a blank page cannot pass.
