# ADR-0005: Threading and Concurrency Architecture

**Status:** Accepted

**Date:** 2026-01-20

**Decision Makers:** Project maintainers

**Related:** N/A

---

## Context

The application performs concurrent operations:
1. GUI must remain responsive while recording
2. Audio capture is continuous during recording
3. Transcription is CPU-intensive and can take seconds
4. Hotkey detection must always be active
5. Clipboard operations may block

A threading strategy is needed to ensure the UI stays responsive while performing heavy work.

## Decision

Implement a **multi-threaded architecture with clear separation**:
1. Main thread: GUI, system tray, hotkey monitoring
2. Background thread: Audio capture during recording
3. Background thread: Transcription processing
4. Event-based coordination using `threading.Event`
5. Thread-safe communication via queues and shared state

## Options Considered

### Option 1: Single-threaded (blocking)
- **Description:** Everything runs on the main thread
- **Pros:**
  - Simple implementation
  - No concurrency issues
- **Cons:**
  - UI freezes during recording/transcription
  - Poor user experience
  - Cannot respond to hotkeys during processing

### Option 2: Asyncio (single-threaded concurrency)
- **Description:** Use async/await for concurrent operations
- **Pros:**
  - Modern Python pattern
  - Explicit control flow
- **Cons:**
  - Audio libraries are blocking, not async-friendly
  - pynput doesn't support async
  - Mixing sync and async is complex

### Option 3: Multi-threaded (Selected)
- **Description:** Dedicated threads for blocking operations
- **Pros:**
  - Natural fit for blocking audio libraries
  - GUI stays responsive
  - Well-understood pattern
  - Works with existing libraries
- **Cons:**
  - Need thread-safe communication
  - Potential race conditions
  - GIL limits true parallelism for CPU work

## Rationale

Option 3 was selected because:
1. **Library Compatibility:** pynput, sounddevice, and audio libraries are blocking/sync
2. **UI Responsiveness:** Background threads keep GUI responsive
3. **Simplicity:** Threads are straightforward for this use case
4. **Proven Pattern:** Desktop applications commonly use this pattern

Thread responsibilities:
- **Main Thread:** GUI, event handling, hotkey detection via pynput
- **Recording Thread:** Audio capture from sounddevice
- **Processing:** Transcription happens synchronously but can be moved to thread

Synchronization mechanisms:
- `threading.Event` for start/stop recording
- Thread-safe queues for passing audio data
- Locks for shared state access

## Consequences

- **Positive:**
  - Responsive GUI
  - Hotkeys always available
  - Clean separation of concerns

- **Negative:**
  - More complex code
  - Need careful synchronization
  - Potential for deadlocks
  - Thread-safety concerns

- **Risk Mitigation:**
  - Minimal shared state
  - Use events for coordination
  - Avoid locks where possible
  - Clear thread ownership conventions

## Implementation

- [x] Main thread for GUI and hotkey detection
- [x] Background audio capture thread
- [x] Event-based recording start/stop
- [ ] Thread-safe transcription queue
- [ ] Proper cleanup on exit

## References

- `src/faster_whisper_hotkey/transcriber.py` - Recording thread implementation
- `src/faster_whisper_hotkey/gui.py` - Main thread GUI
- `src/faster_whisper_hotkey/transcribe.py` - Transcription processing
