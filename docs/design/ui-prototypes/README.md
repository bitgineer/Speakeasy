# UI direction bakeoff

Two throwaway prototypes were built for the same two screens (Dashboard, AI Processing settings) with identical content, then judged from renders at the app's real window size (900x670) and at 1280x800.

- `A-*` is Refined Dark: dense professional workspace, layered near-black surfaces, violet accent, two-column settings.
- `B-*` is Calm Light: warm paper surfaces, editorial spacing, type-forward hierarchy, single column.

Both cleared the floor: labeled controls, visible focus, keyboard-reachable structure, clean 320px reflow, and measured AA contrast. A measured 16 of 16 pairs; B's measurement table is in its prototype notes.

## Decision

A wins. At 900x670 (the app's real window), A shows three history records and most of the provider form; B shows two records and a sliver. SpeakEasy is used in short sessions and carries settings-heavy pages, so density and simultaneous visibility win.

Adopted from B into the A direction: the two-tier semantic token discipline, the measured-contrast table as a working method, and the warm light palette as the Light theme. The nine community themes from the old token layer are preserved unwired in `community-themes.css` and return later as skins over the semantic layer.

Reproduce: `npx playwright screenshot --viewport-size="900,670" file:///.../A/shell-dashboard.html out.png` from `gui/`. The HTML harness lives in the run's temp directory and is deleted once the direction is promoted.
