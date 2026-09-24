# Phase 7 interface audit

## Scope and coverage

Repository scope for `gui/src/renderer/src`: the eleven main routes, the overlay, the ExportDialog and ModelDownloadDialog, the toasts, and the error fallback. Reviewed on `feat/ui-overhaul` at `85043b5` plus this phase's working tree (copy pass and audit fixes recorded below). The review was run before the fixes; each row carries its final status.

Stack and conventions: Electron 28 + React 18 + Tailwind 3 over a two-tier token layer (`styles/themes.css` semantic names, `styles/tokens.css` type/space/motion). Radix dialog, lucide icons, motion. Design conventions found: `CONTRIBUTING.md` (no design coverage), `docs/design/2026-09-23-ui-overhaul.md` (direction A; Light/Dark/System plus violet and ink accents). No component docs, no Storybook, no interface ADRs.

Boundary: the overlay's recording, locked, transcribing and loading states have no deterministic CDP trigger without a real recording; they were inspected in source and are listed under Not verified where visual judgment is at stake. The tray menu is native and excluded. Test files were reviewed only as copy consumers.

| Domain | Evidence inspected | Result |
| --- | --- | --- |
| Accessibility | Source; live CDP on a verify-speakeasy instance (accessible-name scan over all 11 routes, focus-visible probe, hit-area scan, computed styles) | 4 findings, 3 fixed |
| Layout | 26 fresh captures (11 routes x dark/light; overlay 80x72; export dialog); live CDP width probes at 600/450/300px on 4 routes | 1 finding, fixed |
| Writing | Full source pass over 43 tsx files; copy diff | 3 findings, 2 fixed |
| Typography | Source, computed sizes and measures, captures | 2 findings, 1 fixed |
| Colors | 19 rendered pairs measured live in both themes; 21 declared token pairs computed | 1 finding, fixed; no contrast failure otherwise |
| UI polish | Source, captures, motion audit | 2 findings, 1 fixed |

## Findings

| Severity | Domain | Location | Before | After | Why |
| --- | --- | --- | --- | --- | --- |
| HIGH | Layout | `gui/src/renderer/src/styles/globals.css:1845`, `pages/settings/AboutSettings.tsx:75` | `.table-row` collided with Tailwind's generated `table-row` display utility, which wins in the utilities layer and blockifies inside the grid; the Technology rows rendered as `Desktop frameworkElectron` (phase 5 capture confirms) | `.fact-row` | Two values ran together, so the About table read as broken text. Fixed; live computed styles show `display: flex` with the value at the panel's right edge |
| HIGH | Accessibility | `styles/globals.css:1969`, `pages/settings/AppearanceSettings.tsx:147` | Theme and accent radios are `sr-only`; keyboard focus landed on a 1x1 clipped input with no visible indicator | `.option:has(input:focus-visible)` draws the focus ring around the option card | A keyboard-reachable control had no visible focus indicator (escalation trigger). Fixed |
| HIGH | Colors | `components/ModelLoadingBanner.tsx:21` | Raw palette gradient (`from-blue-600/20 to-purple-600/20`) with `text-blue-200`/`text-gray-300`/`text-gray-400`; on the light canvas the heading measured about 1.3:1 | Accent tokens (`border-accent-border`, `bg-accent-muted`, `text-accent-text`) and content text tokens; lucide spinner | Body text failed its contrast requirement in Light (escalation trigger). Fixed; the light stress capture shows the banner readable |
| HIGH | Accessibility | `styles/globals.css:625` | An unbroken string (URL, ID, compound word) in a record body did not wrap and was clipped mid-line; the `Show full text` toggle never appeared because the overflow test cannot fire on a horizontally clipped box | `overflow-wrap: anywhere` on `.record-body` | Truncated content with no way to reach the full value (escalation trigger). Fixed; stress capture shows the full value across two lines |
| HIGH | Layout | `styles/globals.css` (`.page-head`, `.page-actions`, `.toolbar`, `.input-row`, `.record-head`, new `max-width: 560px` shell rule) | At 200% zoom on the 900px window the Dashboard Export button ended at x=490 in a 450px viewport and the Processing providers card at x=517, with no horizontal scroll; at 300px (600px minimum window at 200%) the whole shell clipped | `flex-wrap` on the header/toolbar/input/record rows; below 560px the sidebar becomes a scrollable top strip and content takes the full width | A control was unreachable at 200% zoom (escalation trigger). Fixed; live probes report zero clipped elements across dashboard, batch, model and processing at 600, 450 and 300px |
| MEDIUM | Accessibility | `hooks/useToast.ts:15`, `context/ToastProvider.tsx:25` | Error toasts auto-dismissed after 5 seconds | `toast.error` defaults to `duration = 0`; the toast stays until dismissed | Error toasts carrying no action should persist until dismissed. Fixed; the close button remains the exit |
| MEDIUM | Accessibility | `styles/globals.css:1711` | `.text-button` rendered a 19px-high hit target (Clear, Refresh, Add match) | `min-height: 24px` | Below the WCAG 2.5.8 24px baseline. Fixed |
| MEDIUM | Accessibility | `pages/settings/HotkeySettings.tsx:141` | Save disabled on an empty accelerator with the reason only in a `title`, which a disabled control cannot show | Inline `Press a key combination for this binding.` under the field | The disabled state named no recovery. Fixed |
| MEDIUM | Typography | `styles/globals.css:773`, `:1137`, `:1178` | Stat values, the batch percentage and the batch counters used proportional digits | `font-variant-numeric: tabular-nums` | Values shifted layout as they changed. Fixed |
| MEDIUM | UI polish | `components/ErrorBoundary.tsx:43` | Crash fallback hardcoded dark palette (`bg-gray-900`, `bg-red-500/10`, gray text) and `focus:ring`-only focus styling; copy read `System Malfunction` | Semantic tokens (`surface-canvas`, `danger-muted`, `danger-border`, content text), the global focus ring, copy `Something went wrong` / `Try again` / `Reload app` | The fallback ignored the theme layer and its focus rings. Fixed |
| MEDIUM | Accessibility | `components/ExportDialog.tsx:164`, `components/ModelDownloadDialog.tsx:116` | A backend error containing a long unbroken path expanded the dialog grid past `max-w-md`; the stress dialog showed the error block and title clipped | `.wrap-anywhere` (`overflow-wrap: anywhere`) on both error paragraphs | The error text escaped the dialog and took the title with it. Fixed; stress captures at 900 and 360 |
| MEDIUM | Writing | `api/client.ts:163` | API failures surface as `API Error (500): <detail>` in every error banner | Recommend raising `ApiError` messages through a plain-language mapping per failure class | Developer string shown to users, no stated recovery. Left open: a vocabulary change across every call site, and the status/detail has diagnostic value; needs a design decision |
| LOW | Typography | `pages/Stats.tsx:248` | The longest-transcription quote truncates at 100 characters with an ellipsis | Leave | Accepted: the full text is reachable in the Dashboard record with `Show full text` |
| LOW | UI polish | `components/ConfidenceText.tsx:24` | Unused component keeps `text-amber-400` / `text-red-400` | Delete in a cleanup pass | Accepted: not rendered anywhere; no user impact |

## Verification

Passed.

- Capture: `npm run capture:ui -- --out <temp> --theme dark,light` -> 26 captures, zero failures (11 routes x 2 themes, export dialog, overlay idle at 80x72). Committed under `docs/design/ui-captures/phase7/`.
- Live contrast, measured on a verify-speakeasy instance in both themes: 19 rendered pairs (lowest `nav group label` light 4.99:1; body 5.3-11.4; mode chips 7.8-14.4; focus ring 7.39 light / 11.21 dark; primary label 6.23 light / 5.49 dark) plus 21 declared token pairs (status text 6.71-11.36; control borders 3.59 light / 4.13 dark). All meet their required ratio.
- Live focus probe: `.nav-link` matches `:focus-visible` with the 2px `--focus` outline at 2px offset; input rings inherit the same rule.
- Live width probes after the fix: 600, 450 and 300px viewports on dashboard, batch, model and processing -> zero elements clipped or beyond the viewport.
- Live computed styles for the About table fix: `display: flex`, key right edge 338.7, value right edge 833.
- `break` stress: components rendered from the real source with fixture props, states captured in `stress-components-{dark,light}.png`, `stress-dialog-{dark,light}.png`, `stress-dialog-narrow-{dark,light}.png`. States exercised: default, disabled, loading, error, empty, long text including an unbroken 128-character string, narrow 320px container and 360px viewport, long option text, placeholder-only input. Both themes.
- Gates re-run after the fixes: lint, typecheck, `npm test` (51 passed), `check:tokens` OK, build clean.

Not verified.

- Overlay recording, locked, transcribing and loading visuals: no deterministic CDP trigger without a real recording; source-inspected only. The recording pill's stop and cancel wiring is covered by `test/phase6-surfaces.test.tsx`.
- Hover and active states: not statically forced in the harness (break leaves them to the pointer); focus was measured live, hover and active read from source.
- Screen-reader announcement with a real assistive technology: the environment has none; names and roles were checked from the DOM.
- macOS and Linux: Windows-only per the project doc.

## Verdict

`Approve`. No HIGH findings remain. One MEDIUM (`api/client.ts` error vocabulary) and two LOW rows stay as work to do with the reasons above.
