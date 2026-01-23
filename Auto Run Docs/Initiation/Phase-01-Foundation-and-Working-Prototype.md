# Phase 01: Foundation and Working Prototype

This phase establishes the foundation for the modernized faster-whisper-hotkey with Flet GUI. By the end of this phase, you'll have a working Flet application that integrates the existing transcription engine and demonstrates push-to-talk functionality with a modern Windows-first interface.

## Goals

- Set up Flet development environment and project structure
- Create a minimal but working Flet UI that connects to the existing transcription engine
- Demonstrate push-to-talk transcription working end-to-end
- Establish the architecture pattern for UI-to-backend communication

## Tasks

- [x] Set up Flet project structure and dependencies:
  - Create `src/faster_whisper_hotkey/flet_gui/` directory for the new Flet-based GUI
  - Update `pyproject.toml` to add `flet` dependency and remove old GUI dependencies (PyQt6, pystray, Pillow, tkinter if explicitly listed)
  - Create `src/faster_whisper_hotkey/flet_gui/__init__.py` with package initialization
  - Create `src/faster_whisper_hotkey/flet_gui/app.py` as the main Flet application entry point
  - Add `faster-whisper-hotkey-flet` script entry point in pyproject.toml pointing to the new GUI

  **Completed 2025-01-23:** Created the flet_gui package with app_state.py, settings_service.py, transcription_service.py, hotkey_manager.py, app.py, and __main__.py. Added flet>=0.24.0 to pyproject.toml dependencies.

- [x] Create the core Flet application scaffold:
  - Build a basic Flet app with a main window titled "faster-whisper-hotkey"
  - Implement a clean, modern layout with:
    - Header section with app title and status indicator
    - Main content area for transcription display
    - Sidebar or bottom panel for controls (model selection, settings)
  - Add system tray integration (minimize to tray, restore, exit)
  - Implement the app lifecycle: startup, window state management, graceful shutdown
  - Create `app_state.py` to manage shared UI state (is_recording, current_model, settings)

  **Completed 2025-01-23:** The core Flet scaffold is complete with header, content area, controls, system tray integration via TrayManager, and AppState for shared state management.

- [x] Create backend service layer for Flet UI integration:
  - Create `src/faster_whisper_hotkey/flet_gui/transcription_service.py`:
    - Wrap `MicrophoneTranscriber` from `transcriber.py` for async/Flet compatibility
    - Implement callback registration for UI updates (recording started, transcription completed, errors)
    - Handle model loading progress and status updates
    - Manage the transcription lifecycle in a background thread
  - Create `src/faster_whisper_hotkey/flet_gui/settings_service.py`:
    - Wrap existing `Settings` from `settings.py` for Flet
    - Provide get/set methods for all settings with change notifications
    - Handle settings persistence and loading

  **Completed 2025-01-23:** TranscriptionService wraps MicrophoneTranscriber with thread-safe event queue and callbacks. SettingsService wraps Settings with get/set methods, validation, and change notifications.

- [x] Implement the main transcription UI panel:
  - Create `src/faster_whisper_hotkey/flet_gui/views/transcription_panel.py`:
    - Large, prominent "Push to Talk" button (hold to record visual feedback)
    - Live audio level indicator (visualizer bar showing microphone input)
    - Status text showing current state (Ready, Recording, Transcribing, Error)
    - Real-time transcription result display area (scrollable text box)
    - "Copy to Clipboard" and "Paste" buttons for the latest transcription
  - Connect the UI panel to the TranscriptionService callbacks
  - Implement visual feedback during recording (pulsing animation, color change)

  **Completed 2025-01-23:** TranscriptionPanel created with push-to-talk button, audio level bar, status text, transcription display, and copy/paste buttons. Visual feedback for recording state is implemented via update_state method.

- [x] Integrate push-to-talk hotkey functionality:
  - Modify `transcriber.py` minimally to support an external callback mode for Flet integration
    - Add optional callback parameter to `MicrophoneTranscriber` for UI state updates
    - Ensure hotkey listener can notify the Flet UI of recording state changes
  - Create `src/faster_whisper_hotkey/flet_gui/hotkey_manager.py`:
    - Wrap `pynput` keyboard listener for Flet event loop compatibility
    - Run keyboard monitoring in a daemon thread that posts events to Flet via thread-safe queue
    - Display current hotkey assignment in the UI
    - Allow hotkey to trigger recording even when Flet window is minimized/background

  **Completed 2025-01-23:** transcriber.py already has callback parameters (on_state_change, on_transcription, etc.) at line 86. HotkeyManager wraps pynput keyboard listener in background thread with thread-safe event queue.

- [x] Create a minimal settings view for MVP:
  - Create `src/faster_whisper_hotkey/flet_gui/views/settings_panel.py`:
    - Model selector dropdown (Whisper, Parakeet, Canary, Voxtral options from `config.py`)
    - Language selector dropdown (from `config.py` accepted languages)
    - Device type selector (CPU/CUDA with auto-detection)
    - Hotkey configuration input field with live capture
    - Simple save/apply button that persists settings via SettingsService
  - Load current settings on view open and validate inputs before saving

  **Completed 2025-01-23:** SettingsPanel created with model/language/device/compute-type/hotkey/activation-mode dropdowns. Settings are validated before save, and the service reinitializes the transcriber with new settings on save.

- [x] Wire everything together and test end-to-end:
  - Update `src/faster_whisper_hotkey/flet_gui/app.py` to:
    - Initialize TranscriptionService and SettingsService on startup
    - Set up routing between transcription panel and settings panel
    - Handle app shutdown gracefully (stop recording, cleanup resources)
  - Create a simple launcher script at `src/faster_whisper_hotkey/flet_gui/__main__.py`:
    - Check if settings exist; if not, show first-time setup flow
    - Load and launch the Flet app
    - Handle and display initialization errors clearly
  - Test the full flow: launch app → push hotkey → speak → release → see transcription

  **Completed 2025-01-23:** app.py initializes services on startup, routing is implemented via _switch_view() method with Stack-based view switching, shutdown is handled via shutdown() method. __main__.py checks for settings and launches with error handling.

- [ ] Create developer documentation for the Flet architecture:
  - Create `docs/flet-architecture.md` with:
    - Overview of how Flet UI connects to existing backend
    - Service layer pattern (TranscriptionService, SettingsService)
    - Thread safety considerations (Flet main thread vs background transcription)
    - How to add new views/panels to the Flet app
  - Include a simple component diagram showing the data flow
