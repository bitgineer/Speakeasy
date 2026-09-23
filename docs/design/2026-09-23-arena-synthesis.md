# Arena synthesis: processing modes design

Task: candidate design packages for the SpeakEasy processing core (modes, providers, tone, seam).
Grounding: `grounding.md`. Candidates: `candidate-1`, `candidate-2`, `candidate-3`.

## Pick

Base: candidate 1 (settings-as-data with a pure resolver).

Cross-judge per-criterion scores (parent's transcription of the judge task output; no standalone
judge file was saved at judge time):

| Criterion | C1 | C2 | C3 |
|---|---|---|---|
| R1 usage-first coherence | 9 | 8 | 8 |
| R2 mode semantics | 7 | 9 | 8 |
| R3 provider boundary | 9 | 8 | 8 |
| R4 tone resolution | 9 | 8 | 7 |
| R5 fit with existing constraints | 9 | 8 | 7 |
| R6 interface depth | 8 | 9 | 7 |
| Total | 51 | 50 | 45 |

The judge recommended C1 as base with C2 as the synthesis partner; the parent's end-to-end read
agreed. Candidates 2 and 3 produced complete packages; no dropouts.

Reason: C1 was strongest on the repo's least forgiving constraints (settings to OpenAPI to TS
pipeline shape, key containment, legacy-hotkey migration, revive-or-delete calls for the dead
seams). C2's interface depth won its criteria, but its dict-keyed settings would generate weakly
typed `additionalProperties` and depend on insertion order for tone priority.

## Grafts

From candidate 2, by hand:

- Generation-based cancellation and `insertable` (C2 lines 421-457), replacing C1's
  cooperative-only token.
- Readiness surface, `describe_readiness` plus status route (C2 lines 315-328, 371-377).
- `sanitize` code-fence unwrap (C2 line 445) and the empty-transcript guard (C2 line 399).
- Tone prompt append semantics instead of replace (raised in C2's open questions; resolved in
  synthesis).

From candidate 3, by hand:

- The focused-app readout and pure platform parsers (C3 lines 261-271). Candidate 3 implemented
  these in Electron main with TS parsers; the synthesis re-homes the idea to the backend Python
  probes and pure `parse_*` functions, following candidate 1's placement.

Must-fix items the judge found across all three, resolved in the synthesis:

- Input-length guard: `MAX_LLM_INPUT_CHARS` with fallback (none of the three bounded input).
- `is_ai_enhanced` semantics: keep the wire name, change docstring and GUI label to "processed"
  (all three let cleanup-only differences set it).
- Pre-recording readiness surfacing (only C2 had it, now grafted).

## Rejections

- Per-mode provider/tone routing: no user story, adds a routing table to every resolution.
- Async two-phase enhancement: would revive `transcription_update` for a synchronous insert.
- Dict-keyed settings: pipeline and ordering friction.
- Per-vendor provider classes: four copies of one wire protocol.
- OS keyring, `active-win`, Electron-side detection, streaming, retries, deep-merge PUT.

## Verification

Synthesis verified by red-flag screen (no shallow module, no leakage, no temporal decomposition, no
pass-through) and by usage-first coherence in the final doc.

A fresh-eyes review (different model tier, no transcript available in this environment) flagged:
the resolver could not enforce key-required readiness without `keyed_provider_ids`; the fallback
text contradicted the mode table; the GUI record constructors needed to read the new fields; the C3
graft pointer described the idea, not C3's mechanism; the tone-append graft was missing from the
decision trail; and the doc's baseline was one commit stale. All were fixed in the design doc and
the trail before commit. The review's full flag list lives in the session record.

The real verification is the implementation predicate; see the design doc's verification section.
Not yet executed.

## Model diversity note

The environment has no per-call model selection for task subagents, so the three runners shared one
model and were separated by mandated design direction instead of model family. The cross-judge ran
on a different model (explore tier). Both limitations are recorded in the design doc.
