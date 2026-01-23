# ADR-0003: Cross-Platform Support Strategy

**Status:** Accepted

**Date:** 2026-01-20

**Decision Makers:** Project maintainers

**Related:** N/A

---

## Context

The application is a desktop tool that needs to work on multiple operating systems with different audio systems:
- **Linux:** Uses PulseAudio for audio I/O
- **Windows:** Uses different audio APIs and terminal handling
- **macOS:** (Future support) CoreAudio

Platform differences affect:
- Audio device enumeration and selection
- Hotkey handling (pynput behavior varies)
- Terminal/console handling for CLI
- System tray implementation

## Decision

Implement **cross-platform support through conditional imports and platform abstraction**:
1. Use conditional imports for platform-specific dependencies
2. Abstract audio device handling
3. Use cross-platform libraries (pynput, pystray) where possible
4. Add platform-specific dependencies as optional
5. Lazy load platform-specific modules to avoid import errors

## Options Considered

### Option 1: Linux-only support
- **Description:** Only support Linux with PulseAudio
- **Pros:**
  - Simpler implementation
  - Can use Linux-specific features
- **Cons:**
  - Excludes Windows and macOS users
  - Limits potential user base

### Option 2: Separate codebases per platform
- **Description:** Fork the code for each platform
- **Pros:**
  - Each platform can be optimized
  - No cross-platform compromises
- **Cons:**
  - Maintenance nightmare
  - Feature divergence
  - More complex release process

### Option 3: Single codebase with platform abstraction (Selected)
- **Description:** Conditional imports and abstraction layers
- **Pros:**
  - Single codebase to maintain
  - Features stay in sync across platforms
  - Easier release process
- **Cons:**
  - More complex code structure
  - Platform-specific bugs harder to isolate
  - Some features limited by lowest common denominator

## Rationale

Option 3 was selected because:
1. **Maintainability:** Single codebase reduces maintenance burden
2. **Consistency:** Features work the same on all platforms
3. **Extensibility:** Adding new platforms is straightforward
4. **User Experience:** Users can switch platforms without relearning

Key implementation strategies:
- **Conditional imports:** `try: import pulsectl except ImportError: pass`
- **Lazy loading:** Import pynput only when GUI starts, not at module load
- **Platform detection:** Use `sys.platform` to branch at runtime
- **Optional dependencies:** Platform-specific packages aren't required on other platforms

## Consequences

- **Positive:**
  - Users on all platforms can use the application
  - Single documentation and feature set
  - CI can test all platforms in one pipeline

- **Negative:**
  - More complex code with many conditional branches
  - Platform-specific bugs harder to reproduce
  - Some platform-specific features cannot be exposed
  - Testing burden increases

- **Risk Mitigation:**
  - Platform-specific tests in CI
  - Clear documentation of platform differences
  - Fallback behavior when platform features unavailable
  - Users can report platform-specific issues

## Implementation

- [x] Add conditional imports for pulsectl (Linux)
- [x] Add windows-curses for Windows terminal support
- [x] Lazy load pynput to avoid headless environment issues
- [x] Platform-specific audio device handling
- [x] Cross-platform system tray with pystray
- [ ] Add macOS support (future)
- [ ] Platform-specific CI tests

## References

- `src/faster_whisper_hotkey/transcriber.py` - Audio device handling
- `src/faster_whisper_hotkey/terminal.py` - Cross-platform terminal output
- `pyproject.toml` - Platform-specific dependencies (windows-curses)
