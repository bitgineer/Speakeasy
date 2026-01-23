# ADR-0001: Dual Interface Architecture (CLI + GUI)

**Status:** Accepted

**Date:** 2026-01-20

**Decision Makers:** Project maintainers

**Related:** N/A

---

## Context

The faster-whisper-hotkey application is a push-to-talk transcription tool that needs to serve multiple user groups:
- Power users who prefer command-line interfaces and scripting
- Desktop users who want a system tray application with visual feedback

A single interface would limit the application's accessibility and use cases. The application needs to support both workflows without code duplication or maintenance burden.

## Decision

Implement a **dual interface architecture** with:
1. A full-featured CLI with subcommands (record, transcribe, settings, history, batch)
2. A GUI system tray application using tkinter/pystray
3. A single entry point (`__main__.py`) that dispatches to the appropriate interface
4. Shared core logic between both interfaces

## Options Considered

### Option 1: CLI-only application
- **Description:** Only provide command-line interface
- **Pros:**
  - Simpler implementation
  - Easier to test
  - Lower dependency footprint
- **Cons:**
  - Poor UX for non-technical users
  - No visual feedback during recording
  - No system tray integration

### Option 2: GUI-only application
- **Description:** Only provide graphical interface
- **Pros:**
  - Better user experience for casual users
  - Visual status indicators
  - Easier discovery of features
- **Cons:**
  - Cannot be scripted or automated
  - Poor for power users
  - Requires display/server

### Option 3: Dual interface with shared core (Selected)
- **Description:** Both CLI and GUI interfaces using shared core logic
- **Pros:**
  - Serves all user types
  - Feature parity between interfaces
  - Scriptable AND user-friendly
  - Can use CLI for background tasks
- **Cons:**
  - More complex to maintain
  - Need to ensure both interfaces stay in sync

## Rationale

Option 3 was selected because:
1. **Accessibility:** Both technical and non-technical users can use the application
2. **Flexibility:** Power users can script workflows with the CLI while casual users get a friendly GUI
3. **Feature Parity:** Shared core logic ensures both interfaces have the same capabilities
4. **Future-Proofing:** The architecture supports adding more interfaces (e.g., web UI) without duplicating logic

The dispatch pattern in `__main__.py` enables both `python -m faster_whisper_hotkey` (GUI default) and `faster-whisper-hotkey <subcommand>` (CLI explicit) usage.

## Consequences

- **Positive:**
  - Broader user appeal
  - CLI can be used for automation and scripting
  - GUI provides visual feedback and system tray integration
  - Both interfaces use the same transcription engine, ensuring consistent behavior

- **Negative:**
  - More code to maintain
  - Need to keep both interfaces in sync when adding features
  - Testing burden is higher (need to test both interfaces)

- **Risk Mitigation:**
  - Shared core logic (`transcriber.py`, `models.py`) minimizes duplication
  - Dispatch logic is centralized in `__main__.py`
  - Feature additions must include both CLI and GUI paths

## Implementation

- [x] Create dispatch logic in `__main__.py`
- [x] Implement CLI subcommands in `cli.py`
- [x] Implement GUI in `gui.py` with system tray
- [x] Refactor core logic into shared modules
- [x] Ensure feature parity between interfaces

## References

- `src/faster_whisper_hotkey/__main__.py` - Entry point and dispatch logic
- `src/faster_whisper_hotkey/cli.py` - CLI implementation
- `src/faster_whisper_hotkey/gui.py` - GUI implementation
