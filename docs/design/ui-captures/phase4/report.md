# Phase 4 report (committed 1ecc6b8; branch feat/ui-overhaul)

## Files changed
- `gui/src/renderer/src/pages/BatchTranscription.tsx` rebuilt on semantic tokens: page head, dropzone, queue panel, progress panel, file list. All handlers, WebSocket wiring, and API calls unchanged.
- `gui/src/renderer/src/pages/Stats.tsx` rebuilt on semantic tokens: stat cards, recent activity, timeline, records, empty state. Derived figures unchanged.
- `gui/src/renderer/src/styles/globals.css` new tokenized Batch/Stats blocks (dropzone, queue, progress, file list, stat cards, panels) in A's direction, both themes via the semantic layer.
- `gui/scripts/check-tokens.mjs` legacy ratchet lowered 407 -> 283.
- `.gitignore` was already modified before this task began; left untouched.

## Gates (each exit 0)
- `npm run lint` -> `Warning: React version not specified in eslint-plugin-react settings.` (pre-existing)
- `npm run typecheck` -> main and renderer clean
- `npm test` -> `Test Files 6 passed (6)`, `Tests 41 passed (41)`
- `npm run check:tokens` -> `arbitrary or raw-color values in tsx: 17 (baseline 17)`, `legacy --color-* usages: 283`
- `npm run capture:ui -- --out %TEMP%\opencode\ui-captures\phase4 --theme dark,light` -> exit 1: `capture:ui failed: port 8765 is in use; close the running SpeakEasy app or stop its backend first`

## Ratchets
legacy 407 -> 283 (baseline 407 -> 283). arbitrary unchanged 17 -> 17 (both pages already had zero).

## Captures
After: blocked (0 files). Before (4) copied from `%TEMP%\opencode\ui-captures\baseline-1461218`:
`batch-before-1461218-{dark,light}.png`, `stats-before-1461218-{dark,light}.png`. The dark and light before pairs are byte-identical because no light theme existed at `1461218`; the `-light` copies are kept so the after set pairs name-for-name.

Blocker: a live SpeakEasy app is running, launched from `start.bat` (cmd 35680 <- explorer.exe). Its GUI (PID 47700, user data `%APPDATA%\speakeasy`) holds the Electron single-instance lock, and its backend (PIDs 3192/47008) holds port 8765. The harness preflights the port and refuses; verify-speakeasy documents the same lock and says to close the app. I did not stop it, per the no-backend constraint. Close the app, then rerun the command to produce `batch-after-phase4-*` and `stats-after-phase4-*`.

## Deviations
- Cancel/delete preserved as the original page had them: `clearAll` ("Start new batch") and `removeFile`. The original made no `cancelBatchJob`/`deleteBatchJob` call, so none was added, to keep data flow identical.
- Batch error banner gained a dismiss button and the progress track gained `role="progressbar"`; both match the Dashboard error-banner pattern and change no data flow.
- Added `JOB_STATE`/`FILE_TONE` lookup tables and a typed `StatTone` in place of nested ternaries and the untyped `color` prop.
- The queue panel gained a visible total-files counter ("N total"); the old page showed the count only in the heading text.
- Live functional pass via verify-speakeasy: not run, same live-instance block.
