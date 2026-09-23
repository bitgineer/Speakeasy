# AI processing modes: modes, providers, tone

Status: synthesized design, ready to implement. Baseline `86735c0`. Decision trail:
`docs/design/2026-09-23-ai-processing-modes.decisions.tsv`.

This is the arena synthesis for the processing core: Write / Command / Dictate modes, selectable
LLM providers (local, OpenAI, Groq, custom), and per-app tone profiles. The model-catalog extension
(user-pasted model IDs) is a second unit sketched at the end, not designed here.

## Problem

SpeakEasy turns speech into text on one path: ASR, optional regex cleanup, then history, WebSocket,
clipboard, and the HTTP response. The new program inserts an LLM step with mode-dependent behavior
and per-app context. The hard constraints come from the existing system.

- Settings are one `AppSettings` model, persisted as JSON, shipped to the GUI through the
  OpenAPI-to-TypeScript pipeline, and written by a `PUT` that replaces top-level fields and filters
  `None`. Nested groups are new ground.
- There is no secret storage. The API returns whole settings to the renderer.
- The paste path must never hang on a network call. A timeout, a cancellation on new recording, and
  a fallback to the raw transcript are requirements.
- History must keep raw and processed text recoverable. The `original_text` / `is_ai_enhanced` seams
  were pinned for this feature and are currently inert. `update_text` and a `transcription_update`
  listener are dead. A previous grammar feature was deleted for being dead code, so this feature
  ships wired or not at all.
- The global hotkey is single-slot in the Electron main process. Modes need several bindings, and
  registration failure currently fails silently after erasing the previous binding.
- The `instruction` field on the stop request is Voxtral-only. Modes cannot ride on it.

## Usage (caller's view)

### Settings, as the user edits them

```jsonc
{
  "active_mode": "write",              // the chips and the primary hotkey use this
  "active_provider_id": "ollama",      // "" = none; LLM modes degrade to dictation
  "default_tone": {
    "name": "Default",
    "prompt": "",                      // empty = the built-in rewrite instruction only
    "matches": []
  },
  "tone_profiles": [
    { "name": "Slack",   "prompt": "Casual and short.",  "matches": [{ "field": "app",   "pattern": "slack" }] },
    { "name": "GitHub",  "prompt": "Structured, issue-comment tone.", "matches": [{ "field": "title", "pattern": "github" }] }
  ],
  "command_prompt": "The user will speak an instruction. Carry it out and output only the text to insert.",
  "providers": [
    { "id": "ollama", "label": "Local",  "kind": "local",
      "base_url": "", "model": "llama3.1:8b", "timeout_seconds": 20 },
    { "id": "mygroq", "label": "Groq",   "kind": "groq",
      "base_url": "", "model": "llama-3.3-70b-versatile", "timeout_seconds": 15 }
  ],
  "hotkeys": [
    { "accelerator": "ctrl+shift+space", "trigger": "toggle",       "mode": null },
    { "accelerator": "ctrl+shift+w",     "trigger": "toggle",       "mode": "write" },
    { "accelerator": "ctrl+shift+d",     "trigger": "push-to-talk", "mode": "dictate" }
  ]
}
```

API keys are not in this file. They live in `~/.speakeasy/secrets.json`, written only through
`PUT /api/settings/providers/{id}/key`. `GET /api/settings` never contains a key.

### The stop route, the only production call site

```python
settings = settings_service.get()
result = await asyncio.to_thread(transcriber.stop_and_transcribe, language=..., ...)

run = begin_processing()                    # cancels the previous stop's in-flight call
app = await asyncio.to_thread(detect_focused_app)
keyed = frozenset(p.id for p in settings.providers if get_key(p.id))
plan = resolve_processing(settings, body.mode, app, keyed)
provider = plan.rewrite.provider if plan.rewrite else None
complete = build_provider_client(provider, get_key(provider.id)) if provider else None

outcome = await execute_plan(plan, result.text, complete=complete, run=run)

original = result.text if outcome.text != result.text else None
record = await history.add(text=outcome.text, original_text=original, ...)
await broadcast("transcription", TranscriptionEvent(
    id=record.id, text=outcome.text, duration_ms=result.duration_ms,
    original_text=original, processing_error=outcome.error,
).model_dump())
if _resolve_auto_paste(body.auto_paste) and outcome.insertable:
    insert_text(outcome.text)
return TranscribeStopResponse(..., mode=plan.mode, original_text=original, processing_error=outcome.error)
```

The response, the WebSocket event, the clipboard, and history all read the same outcome. The old
split (history raw, everything else cleaned) is gone.

### A unit test with zero I/O

```python
def test_write_selects_slack_tone():
    settings = AppSettings(
        active_mode="write", active_provider_id="p",
        providers=[LlmProvider(id="p", kind="local", model="m")],
        tone_profiles=[ToneProfile(name="Slack", prompt="Casual.", matches=[AppMatch(field="app", pattern="slack")])],
    )
    plan = resolve_processing(
        settings, None, FocusedApp(key="slack", title="general - Slack"), frozenset()
    )
    assert plan.mode is ProcessingMode.WRITE
    assert "Casual." in plan.rewrite.system_prompt
    assert plan.cleanup is None
```

## Shape

### Module map

| File | Kind | Contents |
|---|---|---|
| `backend/speakeasy/services/settings.py` | data | `ProcessingMode`, `ProviderKind`, `AppMatch`, `ToneProfile`, `LlmProvider`, `HotkeyBinding`, `AppSettings` fields, legacy-hotkey migration |
| `backend/speakeasy/core/processing.py` | pure + coordinator | `FocusedApp`, `CleanupSpec`, `RewriteSpec`, `ProcessingPlan`, `ProcessResult`, `ProviderError`, `ProcessingRun`, `begin_processing`, `cancel_processing`, `matches_app`, `resolve_processing`, `describe_readiness`, `execute_plan` |
| `backend/speakeasy/core/providers.py` | impure, thin | `PROVIDER_ADAPTERS`, `complete_openai_compatible`, `build_provider_client`, kind defaults |
| `backend/speakeasy/services/secrets.py` | impure, thin | `get_key`, `set_key` over `~/.speakeasy/secrets.json` |
| `backend/speakeasy/utils/focused_app.py` | impure, thin | `detect_focused_app` plus pure `parse_*` functions per platform |
| `backend/speakeasy/server.py` | shell | stop seam, start-cancels-processing, key endpoints, status endpoint, focused-app endpoint |
| `gui/src/main/hotkey.ts` | shell | binding registry with rollback, multi-chord push-to-talk, stop body mode |
| `gui/src/renderer/src/pages/settings/ProcessingSettings.tsx` | UI | providers, keys, tones, default tone, command prompt |
| `gui/src/renderer/src/components/ModeChips.tsx` | UI | active-mode chips |

### Persisted types

```python
class ProcessingMode(StrEnum):
    WRITE = "write"; COMMAND = "command"; DICTATE = "dictate"

class ProviderKind(StrEnum):
    LOCAL = "local"; OPENAI = "openai"; GROQ = "groq"; CUSTOM = "custom"

class AppMatch(BaseModel):
    field: Literal["app", "title"]      # app = normalized identifier, title = window title
    pattern: str = Field(..., min_length=1, max_length=200)

class ToneProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(default="", max_length=4000)
    matches: list[AppMatch] = Field(default_factory=list)   # empty = manual selection only

class LlmProvider(BaseModel):
    """One OpenAI-compatible chat endpoint. Credentials are not here; see secrets.py."""
    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$", max_length=50)
    label: str = Field(default="", max_length=100)
    kind: ProviderKind = ProviderKind.LOCAL
    base_url: str = ""                  # empty = the kind's default (local = Ollama)
    model: str = Field(default="", max_length=200)
    timeout_seconds: float = Field(default=20.0, ge=1.0, le=120.0)

class HotkeyBinding(BaseModel):
    accelerator: str = Field(..., pattern=r"^[a-zA-Z0-9+]+$", max_length=50)
    trigger: Literal["toggle", "push-to-talk"] = "toggle"
    mode: ProcessingMode | None = None  # None = use active_mode at press time

# AppSettings additions
active_mode: ProcessingMode = ProcessingMode.DICTATE
active_provider_id: str = ""            # "" = none, because PUT filters None and cannot clear
default_tone: ToneProfile = Field(default_factory=_default_tone)
tone_profiles: list[ToneProfile] = Field(default_factory=list)
command_prompt: str = Field(default=DEFAULT_COMMAND_PROMPT, max_length=4000)
providers: list[LlmProvider] = Field(default_factory=list)
hotkeys: list[HotkeyBinding] = Field(default_factory=_default_hotkeys)
```

`active_provider_id` is a string on purpose. The update path filters `None`, so a nullable field
could be set but never cleared. Empty string encodes "none" (documented on the model).

### Runtime types

```python
class FocusedApp(BaseModel):
    model_config = ConfigDict(frozen=True)
    key: str                            # normalized: exe stem (Windows), bundle id (macOS), app_id/WM_CLASS (Linux)
    title: str = ""

class CleanupSpec(frozen):   custom_fillers: list[str]
class RewriteSpec(frozen):   provider: LlmProvider; system_prompt: str

class ProcessingPlan(frozen):
    mode: ProcessingMode
    cleanup: CleanupSpec | None         # regex cleanup runs iff not None
    rewrite: RewriteSpec | None         # the LLM runs iff not None

class ProcessResult(frozen):
    text: str
    error: str | None = None            # safe, human-readable reason; None on success
    insertable: bool = True             # False only when a newer recording superseded this run

class LlmRequest(frozen):   system: str; user: str
class LlmResponse(frozen):  text: str
CompleteFn = Callable[[LlmRequest], Awaitable[LlmResponse]]

class ProviderError(Exception):
    reason: Literal["timeout", "connection", "auth", "rate_limit", "server", "bad_response", "cancelled"]
    detail: str                         # never contains a key, a prompt, or a response body
```

Illegal states are encoded away. A plan cannot claim an LLM without a provider (`rewrite is None`
when none is usable). A `RewriteSpec` carries the exact provider and resolved prompt, so the
executor never re-resolves. The degraded state is derived, not stored.

### Mode semantics

| Mode | Regex cleanup | LLM | System prompt | Fallback |
|---|---|---|---|---|
| `dictate` | `safe_cleanup` iff `enable_text_cleanup` | no | n/a | never degrades |
| `write` | fallback only | yes | built-in rewrite instruction plus the matched tone prompt | fallback text, error set |
| `command` | fallback only | yes | `settings.command_prompt` | fallback text, error set |

Cleanup does not run before the LLM. The regex filler list removes meaning-bearing words, and the
prompt handles fillers better. Command must not be cleanup-mangled ("add a comma before so" must
reach the model intact). The `cleanup` spec in a plan describes the fallback text, the text a
failed or degraded run inserts, so a failed Write still delivers usable dictation rather than raw
filler. Tone profiles apply to write only.

### Resolution, pure and total

```python
def resolve_processing(
    settings, mode: ProcessingMode | None, app: FocusedApp | None,
    keyed_provider_ids: frozenset[str],
) -> ProcessingPlan:
    """Pure and total. keyed_provider_ids is data, not I/O, so execution and readiness resolve
    the same way. Fallback chain:
       mode := mode or settings.active_mode
       dictate -> fallback cleanup per settings; no rewrite
       write   -> first matching tone profile, else default_tone
       command -> command_prompt
       no ready provider (missing, no model, custom without base_url, or required key absent)
                 -> fallback cleanup per settings, no rewrite (degrade, never raise)
       unknown app -> default_tone."""
```

Provider readiness: model non-empty, base URL resolvable (custom requires one), and a stored key
when the kind requires one. `matches_app` is a case-insensitive substring test against `key` for
`field="app"` and against `title` for `field="title"`, first profile in list order wins.

Readiness is derived from the same function so it cannot drift:

```python
class ModeReadiness(frozen):  mode: ProcessingMode; ready: bool; reason: str | None
def describe_readiness(settings, keyed_provider_ids: frozenset[str]) -> list[ModeReadiness]
```

Both functions take the same `keyed_provider_ids`, so a plan cannot claim a provider whose
required key is absent, and the status route reports exactly what execution will do.

### Execution, async with real cancellation

```python
class ProcessingRun:
    """Single-slot owner of the in-flight provider call.
    The app records one session at a time, so one slot is the true invariant."""
    generation: int = 0
    task: asyncio.Task | None = None

    def supersede(self) -> None:
        """Invalidate the current generation and cancel the in-flight task. Idempotent."""

_active_run = ProcessingRun()
def begin_processing() -> ProcessingRun:  # supersede, then hand back the current run
def cancel_processing() -> None:           # supersede (called by /api/transcribe/start)

async def execute_plan(plan, text, *, complete, run) -> ProcessResult:
    """Never raises for provider trouble. Order:
       fallback = cleanup(text) if plan.cleanup else text   # what a degraded run inserts
       plan.rewrite is None or complete is None -> return ProcessResult(fallback)
       not text.strip()                          -> ProcessResult(fallback)             # nothing to send
       len(text) > MAX_LLM_INPUT_CHARS           -> ProcessResult(fallback, error="transcript too long for AI processing")
       task = create_task(complete(LlmRequest(system=plan.rewrite.system_prompt, user=text)))
       run.task = task
       await wait_for(task, plan.rewrite.provider.timeout_seconds)
       timeout / ProviderError                   -> ProcessResult(fallback, error=...)
       superseded (generation moved) or cancelled by supersede
                                                 -> ProcessResult(fallback, error="cancelled", insertable=False)
       result = sanitize(response.text)          # strip, unwrap one whole-response code fence
       empty result                              -> ProcessResult(fallback, error="empty response")
       otherwise                                 -> ProcessResult(result)"""
```

`MAX_LLM_INPUT_CHARS` is a named constant (6000) with fallback. It is where the judge's shared
weakness (unbounded provider input) is fixed; a long dictation degrades to its clean raw text
instead of overflowing a context window mid-paste.

`processing_start` calls `cancel_processing()` before starting the recorder. When a run is
superseded, history still records the text (the utterance is never lost) but nothing is pasted.

### Provider boundary

```python
async def complete_openai_compatible(provider, request, api_key, *, client: httpx.AsyncClient | None = None) -> LlmResponse:
    """POST {base_url}/chat/completions, non-streaming, temperature 0.
    Raises ProviderError with a safe detail. Never logs the key, the prompt, or the response body."""

PROVIDER_ADAPTERS: dict[ProviderKind, ProviderAdapter] = { ... openai-compatible covers all four kinds ... }
def build_provider_client(provider, api_key) -> CompleteFn:  # text in, text out
```

Kind defaults: local is `http://127.0.0.1:11434/v1` (Ollama; LM Studio uses the same shape), openai
is `https://api.openai.com/v1`, groq is `https://api.groq.com/openai/v1`, custom has no default.
Keys are required for openai and groq only. `httpx` moves from the dev extra to runtime
dependencies; it is already in the lockfile and provides per-request timeouts, `AsyncClient`
cancellation, and `MockTransport` for tests. Error taxonomy: 401/403 auth, 429 rate limit, 5xx
server, timeout, connection, bad_response. No streaming, no retries. The provider call runs in the
backend, never the renderer.

### Secrets

`~/.speakeasy/secrets.json`, a flat `{provider_id: key}` map, written atomically (`os.replace`) with
0600 permissions where the platform supports them. Only `services/secrets.py` reads key material.

- `PUT /api/settings/providers/{id}/key` body `{"key": "..."}`. Empty string clears. 404 for an
  unknown provider id. The request model is the only wire schema that mentions a key, and it has no
  read path.
- `GET /api/settings/provider-keys` returns `{"<provider_id>": true|false}` for the settings UI.

A schema test asserts no persisted or returned component carries a key field.

### Focused app

```python
def detect_focused_app() -> FocusedApp | None:
    """Best-effort probe, never raises. None means unknown; the resolver falls back to default_tone."""
```

Platform probes, no new dependencies, following the pattern already in `paste.py`.

| Platform | Probe | key normalization | title |
|---|---|---|---|
| Windows | `ctypes` GetForegroundWindow, GetWindowThreadProcessId, QueryFullProcessImageNameW | exe stem, lowercased | window text |
| macOS | `osascript` System Events frontmost process | bundle id if available, else lowercased name | front window name (empty without Accessibility permission) |
| Linux X11 | `xdotool getactivewindow` + `xprop WM_CLASS` | WM_CLASS instance, lowercased | window name |
| Linux Wayland | `swaymsg -t get_tree` focused node | `app_id`, lowercased | node name |
| other / missing tools | `None` | | |

The parse step is split into pure `parse_windows`, `parse_macos`, `parse_linux_x11`,
`parse_linux_wayland` functions so the normalization is unit-testable without a desktop session.
`GET /api/focused-app` returns the current detection for the settings page readout, so users can
discover the identifier they need to match. The probe runs on the stop path inside
`asyncio.to_thread`; a failed or slow probe never blocks the transcription.

Browser-hosted apps (GitHub inside Chrome) match only through title rules. Stated limitation.

### The seam in `transcribe_stop`

The current lines `server.py:572-610` are replaced by the call site above. Plus:

- `TranscribeStopRequest` gains `mode: ProcessingMode | None = None`. `None` means the persisted
  `active_mode`; the main process sends an explicit mode only when the pressed binding carries one.
- `TranscribeStopResponse` gains `original_text`, `processing_error`, `mode`.
- `TranscriptionEvent` gains `original_text: str | None = None` and
  `processing_error: str | None = None`. Defaults keep existing schema pins valid.
- History stores `text=outcome.text` and `original_text=raw` when they differ. This makes the
  history list, the response, the WebSocket event, and the clipboard agree, and it lights up the
  existing Processed/Original toggle.
- `is_ai_enhanced` keeps its wire name and derivation (`original_text` exists and differs). Its
  docstring and the GUI label change to "processed", because cleanup-only differences also set it.
  Renaming the field would churn the pinned contract for a wording win; recorded as a tradeoff.
- Delete `HistoryService.update_text` and its test, the GUI `transcription_update` listener and its
  store case, and the stale grammar references in `core/README.md`, `services/README.md`, and
  docstrings. Processing completes before the single insert, so a two-phase update has no producer.
- Fix the record path inside the blast radius. Both `App.tsx`'s `recording:complete` handler and
  the store's WebSocket handler build records with hardcoded `original_text: null,
  is_ai_enhanced: false`; both must read the new response and event fields. The store's upsert
  replaces by id, so whichever handler loses the race cannot overwrite the processed record with a
  stale one.

Live captions stay regex-cleanup only. Batch stays unchanged. Both stated as non-goals.

### Delivery

- Settings carry `hotkeys: list[HotkeyBinding]`. A `mode: null` binding behaves exactly like today
  (records in `active_mode`); a concrete mode dedicates the binding.
- Legacy migration: a `model_validator(mode="before")` maps an old file's `hotkey` / `hotkey_mode`
  into one `mode: null` binding when `hotkeys` is absent, then drops the legacy keys.
- Electron main: `registerHotkeys(bindings)` is transactional. Register the new set; on any failure
  unregister what was installed, re-register the previous set, and return
  `{ ok: false, failed: [{accelerator, error}] }`. State commits only on full success. Push-to-talk
  keeps one uiohook listener with per-chord pressed-state maps.
- `startRecording(mode)` stores the recording's mode and broadcasts `recording:start` with `{mode}`
  (explicit binding mode, or null for active-mode). `stopRecording()` sends `{mode}` in the stop
  body only when the binding carried one.
- IPC: `hotkey:register` takes `{bindings}`; `hotkey:current` returns bindings; `App.tsx` surfaces
  registration failures through the existing toast instead of ignoring `{success:false}`.
- Renderer: `ModeChips` (Write / Command / Dictate) on the Dashboard writes `active_mode`. The
  overlay shows the active mode on the idle pill (it already polls settings every 2s) and the
  explicit mode during a bound recording. A `processing_error` in the stop response surfaces as a
  toast, so degraded Write never looks like success.
- `ProcessingSettings` page: provider list with preset templates (Local, OpenAI, Groq, Custom),
  write-only key fields backed by `provider-keys`, tone profile editor with match rules, default
  tone editor, command prompt editor. `HotkeySettings` becomes a bindings list editor.

### Settings schema and update semantics

- New nested models become named OpenAPI components; the GUI type aliases extend `types.ts`.
  Regenerate with `cd backend && uv run python scripts/export_openapi.py` and
  `cd gui && npm run gen:api`; CI checks both.
- `SettingsUpdateRequest` mirrors the new top-level fields (`| None = None`) and reuses the nested
  models, so there is no duplicate shape. The endpoint catches `ValidationError` and returns 400.
- Existing update semantics stand. Top-level replace, `None` filtered, nested groups replace
  wholesale, `[]` clears a list, `""` clears `active_provider_id`. Documented in the endpoint
  docstring.
- Migration needs no versioning. New fields have defaults, so old files load unchanged. The
  all-or-nothing load fallback stays; it is flagged as a risk because a hand-edited provider entry
  can reset everything.

### Readiness endpoint

`GET /api/processing/status` returns `{"modes": [{"mode", "ready", "reason"}], "provider_id"}`,
computed by `describe_readiness` plus key presence. The settings page and the chips use it to show
"Write needs a provider" before the user speaks.

## Synthesis decision

Arena base: **candidate 1** (settings-as-data with a pure resolver), scores 51/60 against candidate
2's 50 and candidate 3's 45. Candidate 1 was strongest exactly where the repo's constraints are
sharpest: the settings-to-OpenAPI-to-TS pipeline (list shapes, migration validator, `""` encoding of
the None filter), key containment, and the explicit revive-or-delete decisions for the dead seams.
The cross-judge agreed and named candidate 2 the synthesis partner rather than the base, because
its dict-keyed settings would round-trip as weakly typed `additionalProperties` and depend on
insertion order for tone priority.

Grafted from candidate 2, by hand:

- Generation-based cancellation and the `insertable` outcome, replacing candidate 1's
  cooperative-only token. A superseded run cancels the in-flight HTTP call instead of waiting out
  the timeout, and can never paste stale text.
- The readiness surface (`describe_readiness` plus the status route), which candidate 1 computed
  but never exposed.
- `sanitize` (strip, unwrap one code fence) and the empty-transcript guard.
- Tone prompts append to the built-in instruction instead of replacing it, so a sparse user prompt
  cannot weaken the rewrite contract.

Grafted from candidate 3:

- The `GET /api/focused-app` readout and the split of pure platform parsers from the spawn.
- The explicit user-visible fallback signal: a degraded Write shows a toast, never silent success.

Rejected, with reasons: per-mode provider and tone routing (no user story for v1, adds a routing
table to every resolution), async two-phase enhancement (it would revive `transcription_update` for
a synchronous insert, the temporal-decomposition red flag; pasting raw and replacing edited text is
worse than waiting), dict-keyed settings (pipeline and ordering friction above), per-vendor provider
classes (four copies of one wire protocol), an OS keyring (new dependency, platform failure modes;
`SecretStore` is the seam), `active-win` and Electron-side detection (native dependency or a second
platform implementation; the overlay is non-focusable, so the backend sees the same target window),
streaming (the result is inserted once), retries (the fallback is the retry), and a deep-merge PUT
(changes the pinned update contract for one feature).

Model-diversity limitation: this environment's task tool has no per-call model selection, so the
three runners ran on the same configured model with structurally distinct mandated directions
instead of three model families. The cross-judge ran on a different model than the runners. The
graft step is by the parent, by hand.

## Tradeoffs accepted

- We accept sync stop latency up to the provider timeout (default 20s, per provider) in exchange for
  one code path, truthful history, and a final paste.
- We accept one active provider for all LLM modes, and tones that apply to write only.
- We accept a second credential file and two credential write paths so no key can reach
  `GET /api/settings`, the schema, the renderer, or logs.
- We accept plaintext `secrets.json` (0600 best effort) instead of a keyring dependency in v1.
- We accept substring app matching with first-match list order, and title-only matching for
  browser-hosted apps.
- We accept `is_ai_enhanced` covering cleanup-only differences, keeping the pinned field name and
  changing the label instead.
- We accept `MAX_LLM_INPUT_CHARS` as a constant (6000) rather than a setting, for now.
- We accept deleting `update_text` and the `transcription_update` listener; if processing ever goes
  async they return with a real producer.
- We accept `httpx` as a runtime dependency.
- We accept the all-or-nothing settings load fallback with nested data; flagged as a risk.

## Alternatives considered

- **An `AIProcessingService` class holding clients and mode state.** More surface (lifecycle,
  injected clients, synchronization) hiding the same policy. The pure resolver plus a one-slot run
  owner is smaller and testable without I/O. Lost on interface depth.
- **Minimal-diff procedural module with module-level cancellation globals.** Smallest diff, but its
  plan admitted an invalid combination, its cancellation path could paste stale text, and it
  revived `transcription_update` for a synchronous step. The extra structure in this shape buys
  real invariants.
- **Dict-keyed settings.** Weakly typed `additionalProperties` in TS and insertion-order tone
  priority. Lists are the pipeline-friendly shape.
- **Focused-app detection in Electron main.** Adds a native dependency or a second platform
  implementation in TS, and ships OS facts across a process boundary for no gain.
- **Strict referential validation at load time.** Would let one dangling reference reset the whole
  settings file; the resolver degrades the affected mode instead, which is the honest boundary.

## Open product decisions

These are preference calls the implementation will make one way unless redirected. Recommendations
baked into the design are in parentheses.

1. **Command mode scope.** V1 treats the utterance as an instruction that produces the inserted
   text ("write a reply declining the meeting"). Selection-aware editing ("make this shorter")
   needs selection capture and is deferred. (Utterance-only.)
2. **Default active mode.** Dictate, the privacy-safe default; a fresh install with no provider
   still works. Write is one chip away. (Dictate.)
3. **Provider naming.** Presets are Local / OpenAI / Groq / Custom. The competitor's "Fluid
   Intelligence" names their engine; SpeakEasy's local option is named for what it is. (Local.)
4. **README privacy copy.** "No API keys" becomes "Works fully offline. Cloud AI is optional and
   only runs when you configure a provider." (Change it.)
5. **History label.** The toggle becomes "Processed / Original" while the wire field keeps the name
   `is_ai_enhanced`. (Change the label.)
6. **macOS and Linux probes are untested on this Windows machine.** They are guarded and degrade to
   the default tone. Someone needs to verify them on real systems before release.

## Implementation phases

Each phase ends in a verifiable state. Commit per unit; run the gate before the next phase.

- **Phase 0. Scaffold.** Branch `feat/ai-processing-modes`, baseline test runs captured, this doc
  and the decision trail committed. Gate: backend pytest, gui lint/typecheck/test recorded as the
  pre-change baseline.
- **Phase 1. Settings, secrets, schema.** Nested processing models, migration validator,
  `SettingsUpdateRequest`, key endpoints, `secrets.py`, OpenAPI and `gen:api` regeneration.
  Gate: settings round-trip and migration tests, secret tests, no-key-leak schema test,
  `export_openapi.py --check`, `gen:api` diff clean.
- **Phase 2. Pure core.** `core/processing.py` plan types, `resolve_processing`, `matches_app`,
  `describe_readiness`. Gate: new pytest files green (mode fallback, degrade, tone match, readiness).
- **Phase 3. Executor and providers.** `execute_plan` with supersession, timeout, guards, sanitize;
  `core/providers.py`; focused-app probes and pure parsers. Gate: executor tests with fake async
  completions, MockTransport adapter tests, parser tests.
- **Phase 4. Server seam.** Rewrite `transcribe_stop`, cancel on start, contract and response
  fields, delete the dead seams, status and focused-app endpoints, history dedupe fix. Gate: full
  backend pytest, schema contract, `--check` clean.
- **Phase 5. Electron main.** Binding registry with rollback, IPC changes, stop body mode,
  `recording:start` payload. Gate: vitest, typecheck.
- **Phase 6. Renderer.** Mode chips, processing settings page, hotkey editor, overlay indicator,
  history label, error toast. Gate: lint, typecheck, vitest, Playwright smoke.
- **Phase 7. Docs and whole-artifact verification.** README and docs updates, a committed
  end-to-end script driving the backend with a stub OpenAI-compatible provider, jev_review loop,
  unslop and no-comments passes, opening the PR. Gate: the verification predicate below.

**Phase 8, separate unit. Model catalog.** User-pasted model IDs: a `user_models` list in settings
merged into `GET /api/models`, a free-text add control in `ModelSelector`, pass-through fixes in
`_resolve_hf_name`, cache identity for Whisper short names, and a guard on the crashing canary
languages route. Own design sketch and tests; deliberately not designed here.

## Verification predicate

The work is done when the full suite is green and a committed script drives the real backend
surface with a stub OpenAI-compatible provider to show:

1. Dictate never calls the provider; the inserted text is the cleaned raw text.
2. Write calls the provider and the response, WebSocket event, clipboard text, and history all
   carry the rewritten text, with the raw text stored as `original_text`.
3. A tone profile matching the focused app selects its prompt; an unknown app uses the default.
4. Provider failure, timeout, and an oversized transcript each fall back to the fallback text
   (what dictate would insert; cleanup per settings) within the timeout plus one second, with
   `processing_error` set and no paste when superseded.
5. `GET /api/settings`, committed `openapi.json`, and the logs contain no key value.
6. The GUI checks pass, and the live app registers multiple hotkeys, publishes the active mode to
   the overlay, and surfaces a degraded Write as a toast.

## Next implementation step

Phase 0, then Phase 1. The first code writes the settings models and `SecretStore`, regenerates the
schema, and lands the settings and secret tests. Everything else fills in against that contract.
