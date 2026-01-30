# Project Roadmap

**Goal:** Clean up technical debt and consolidate the codebase around the new backend architecture.

## Phase 1: Legacy Cleanup & Consolidation
- **Goal:** Remove unused legacy code (`src/faster_whisper_hotkey`), consolidate project structure, and verify no regressions.
- **Status:** planned
- **Description:** Systematically review and remove the legacy `src/` directory. Verify `backend/` is the sole server. Ensure GUI points to the correct endpoints. Create a manifest of removed files for safety.

## Phase 2: Grammar Enhancements
- **Goal:** Improve grammar correction quality and transcription coherence.
- **Status:** complete
- **Plans:** 1 plans
- **Completed:** Fri Jan 30 2026
- **Description:** Refactor grammar processor to support optimized prompt templates and coherence restoration tasks using CoEdit and Flan-T5 models, preserving user tone.

## Phase 3: Overlay Improvements
- **Goal:** Create a pixel-perfect click-through overlay with improved visuals.
- **Status:** complete
- **Plans:** 2 plans
- **Completed:** Fri Jan 30 2026
- **Description:** Refine the desktop overlay to support pass-through clicks, hover expansion, and smoother animations using Electron Input Masking.
Plans:
- [x] 03-01-PLAN.md — Infrastructure & IPC
- [x] 03-02-PLAN.md — UI Components & Logic

### Phase 03.1: Recording Locked UI Indication (INSERTED) - Complete

**Goal:** Provide visual indication for hands-free locked recording state.
**Depends on:** Phase 3
**Status:** complete
**Plans:** 1 plans
**Completed:** Fri Jan 30 2026

Plans:
- [x] 03.1-01-PLAN.md — UI Components & Logic

**Details:**
Address the recording Locked: (Long press) there is no UI indication that we have made that switch over only through the backend.

### Phase 03.2: Remove Background Beneath States (INSERTED)

**Goal:** Remove the background from the recording overlay to allow true transparency.
**Depends on:** Phase 3
**Status:** complete
**Plans:** 1 plans
**Completed:** Fri Jan 30 2026

Plans:
- [x] 03.2-01-PLAN.md — CSS Architecture Refactor

**Details:**
Refactor CSS to scope background styles to layout components instead of global body tags.

### Phase 03.3: Center Overlay Positioning (INSERTED) - Complete

**Goal:** Implement active display tracking for the recording overlay.
**Depends on:** Phase 3.2
**Status:** complete
**Plans:** 1 plans
**Completed:** Fri Jan 30 2026

Plans:
- [x] 03.3-01-PLAN.md — Overlay Tracking Logic

**Details:**
Center the overlay to the user's center of the screen on the X axis. The overlay follows the mouse across screen but in the same position (height a few pixels above taskbar).

### Phase 03.4: Fix Batch Transcription (INSERTED)

**Goal:** Fix batch transcription attribute error and implement UI status feedback.
**Depends on:** Phase 3.3
**Status:** complete
**Plans:** 2 plans
**Completed:** Fri Jan 30 2026

Plans:
- [x] 03.4-01-PLAN.md — Backend Fix & Retry Logic
- [x] 03.4-02-PLAN.md — UI Error Feedback Improvements

**Details:**
- Fix Backend: `TranscriberService` object has no attribute `transcribe_file` error.
- Fix Frontend: User is unaware of failure status; add visual indication of batch progress/errors.

### Phase 03.5: Stabilize Batch Transcription (INSERTED)

**Goal:** Fix CUDA illegal memory access errors and ensure robust error recovery during batch processing.
**Depends on:** Phase 3.4
**Status:** complete
**Plans:** 1 plans
**Completed:** Fri Jan 30 2026

Plans:
- [x] 03.5-01-PLAN.md — Resilience & Thread Safety

**Details:**
- Investigate and fix `CUDA error: an illegal memory access was encountered` during batch transcription.
- Ensure the application handles CUDA errors gracefully (e.g., re-initializing the model or falling back to CPU) without crashing the entire batch.
- Fix "State change callback error: no running event loop" log spam.
