# ADR-0004: Settings Persistence Architecture

**Status:** Accepted

**Date:** 2026-01-20

**Decision Makers:** Project maintainers

**Related:** N/A

---

## Context

The application needs to persist various types of configuration:
- User preferences (language, model selection, etc.)
- Keyboard shortcuts/hotkeys
- Application state (onboarding completion, window positions)
- Transcription history

Multiple persistence strategies exist, each with trade-offs in complexity, performance, and usability.

## Decision

Implement a **JSON-based settings persistence system** with:
1. Dataclass-based configuration schema for type safety
2. JSON file storage in `~/.config/faster_whisper_hotkey/`
3. Separate files for settings and history
4. Default values handling
5. First-run detection for onboarding

## Options Considered

### Option 1: No persistence (command-line args only)
- **Description:** All configuration via command-line arguments
- **Pros:**
  - No storage complexity
  - Explicit configuration
- **Cons:**
  - Poor UX for GUI users
  - No settings to remember between sessions
  - Cannot implement onboarding

### Option 2: Database (SQLite)
- **Description:** Use SQLite for all persistence
- **Pros:**
  - Structured queries
  - ACID guarantees
  - Good for large history
- **Cons:**
  - Overkill for simple settings
  - Requires migration strategy
  - Harder for users to edit manually

### Option 3: JSON files (Selected)
- **Description:** Human-readable JSON files
- **Pros:**
  - Simple and transparent
  - Users can edit manually
  - Easy to debug
  - No migrations needed for simple changes
- **Cons:**
  - No schema validation
  - Manual parsing needed
  - Concurrency issues if multiple instances

## Rationale

Option 3 was selected because:
1. **Simplicity:** JSON is easy to read, write, and debug
2. **User Control:** Users can edit settings with a text editor
3. **Sufficient:** Settings are simple key-value pairs, don't need database
4. **Portable:** Easy to backup and migrate settings
5. **Type Safety:** Python dataclasses provide compile-time type checking

The settings system uses:
- **Dataclass:** `@dataclass class Settings` with type annotations
- **JSON schema:** Simple key-value pairs with nested structures
- **Default handling:** `data.setdefault()` for new fields
- **Location:** XDG-compliant config directory

## Consequences

- **Positive:**
  - Users can manually edit settings
  - Easy to backup and restore
  - Transparent configuration
  - Type safety via dataclasses

- **Negative:**
  - No validation of user edits
  - Need to handle missing/corrupt files
  - Adding new fields requires default handling
  - Not suitable for high-concurrency scenarios

- **Risk Mitigation:**
  - Graceful handling of corrupt/missing settings (use defaults)
  - Validation when loading settings
  - Document the settings schema
  - Add version field for future migrations

## Implementation

- [x] Create Settings dataclass in `settings.py`
- [x] Implement `load_settings()` and `save_settings()`
- [x] Use XDG config directory (`~/.config/faster_whisper_hotkey/`)
- [x] Add onboarding_completed field for first-run detection
- [x] Implement history persistence with separate JSON file
- [ ] Add settings version field for migrations

## References

- `src/faster_whisper_hotkey/settings.py` - Settings dataclass and persistence
- `src/faster_whisper_hotkey/config.py` - Default configuration values
