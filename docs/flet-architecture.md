---
type: architecture
title: Flet GUI Architecture
created: 2025-01-23
tags:
  - flet
  - gui
  - architecture
related:
  - "[[Phase-01-Foundation-and-Working-Prototype]]"
---

# Flet GUI Architecture

This document describes the architecture of the new Flet-based GUI for faster-whisper-hotkey, including how it connects to the existing transcription backend, the service layer pattern, thread safety considerations, and how to add new views.

## Overview

The Flet GUI architecture follows a **service-oriented pattern** with clear separation between:

1. **UI Layer** (`views/`) - Flet components that render the interface
2. **Service Layer** (`transcription_service.py`, `settings_service.py`) - Wraps backend functionality
3. **State Management** (`app_state.py`) - Thread-safe shared state
4. **Background Services** (`hotkey_manager.py`, `tray_manager.py`) - System integration

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flet Main Thread                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      FletApp (app.py)                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │ Transcription│  │   Settings   │  │    Header    │      │ │
│  │  │    Panel     │  │    Panel     │  │   & Controls │      │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │ │
│  └─────────┼─────────────────┼────────────────────────────────┘ │
│            │                 │                                   │
│  ┌─────────▼─────────────────▼─────────────────────────────┐   │
│  │              AppState (Shared State)                      │   │
│  │         - recording_state, audio_level, etc.             │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  HotkeyManager   │ │ TrayManager  │ │ Transcription│
    │  (Background)    │ │ (Background) │ │   Service    │
    └────────┬─────────┘ └──────────────┘ └──────┬───────┘
             │                                    │
             └──────────────────┬─────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ MicrophoneTranscriber │
                    │   (Existing Backend)  │
                    └───────────────────────┘
```

## Directory Structure

```
src/faster_whisper_hotkey/flet_gui/
├── __init__.py           # Package initialization
├── __main__.py           # Entry point with error handling
├── app.py                # Main Flet application class
├── app_state.py          # Shared state management
├── transcription_service.py  # Transcription service wrapper
├── settings_service.py   # Settings service wrapper
├── hotkey_manager.py     # Keyboard hotkey detection
├── tray_manager.py       # System tray integration
├── views/
│   ├── __init__.py
│   ├── transcription_panel.py  # Main transcription UI
│   └── settings_panel.py       # Settings configuration UI
└── (future views to be added)
```

## Service Layer Pattern

The service layer acts as a bridge between the Flet UI (which runs on the main thread) and the existing backend code (which may run in background threads).

### TranscriptionService

Located in `transcription_service.py`, this class wraps `MicrophoneTranscriber` from the existing backend.

**Key responsibilities:**
- Initialize and manage the `MicrophoneTranscriber` lifecycle
- Provide thread-safe event queue for UI updates
- Expose callback registration for state changes
- Handle recording control (start/stop/toggle)

**Event types:**
| Event | Data | Description |
|-------|------|-------------|
| `state_change` | `str` | Recording state changed (idle/recording/transcribing) |
| `transcription` | `str` | Completed transcription text |
| `transcription_start` | `float` | Transcription started with duration |
| `audio_level` | `float` | Audio input level 0.0-1.0 for visualization |
| `streaming_update` | `dict` | Streaming transcription update |
| `error` | `str` | Error message |

**Usage example:**
```python
# Create service
service = TranscriptionService(settings)
service.initialize()

# Register callbacks
service.on("state_change", lambda state: print(f"State: {state}"))
service.on("transcription", lambda text: print(f"Result: {text}"))

# Control recording
service.start_recording()
service.stop_recording()
```

### SettingsService

Located in `settings_service.py`, this class wraps the existing `Settings` module.

**Key responsibilities:**
- Load and save settings from disk
- Provide thread-safe get/set methods
- Validate settings values
- Notify subscribers of changes

**Usage example:**
```python
service = SettingsService()
settings = service.load()

# Get/set individual settings
model = service.get_model_name()
service.set_language("es")

# Subscribe to changes
unsubscribe = service.subscribe(lambda s: print("Settings changed!"))

# Save to disk
service.save()
```

## Thread Safety Considerations

The Flet GUI runs on a main thread, while transcription and hotkey detection run in background threads. To maintain thread safety:

### 1. Event Queue Pattern

Background threads communicate with the UI via thread-safe queues:

```python
# In background thread:
self._event_queue.put_nowait(TranscriptionEvent("state_change", "recording"))

# In Flet main thread (polling loop):
def process_events():
    while True:
        event = service.get_next_event(timeout=0.0)
        if event is None:
            break
        # Handle event in UI thread
```

### 2. Thread-Safe State

`AppState` uses `threading.RLock` to protect all state access:

```python
@property
def recording_state(self) -> RecordingState:
    """Get the current recording state (thread-safe)."""
    with self._lock:
        return self._recording_state
```

### 3. Lock-Protected Service Methods

Service methods that modify state use locks:

```python
def start_recording(self) -> bool:
    with self._lock:
        if not self._transcriber:
            return False
        # ... safe to modify state here
```

### 4. UI Updates Only on Main Thread

All Flet UI updates must occur on the main thread. The `_start_event_processing()` method in `FletApp` runs a timer that:
1. Processes events from service queues
2. Updates UI components
3. Schedules the next iteration

## How to Add New Views/Panels

Adding a new view to the Flet application involves three main steps:

### Step 1: Create the View Class

Create a new file in `views/` (e.g., `history_panel.py`):

```python
"""
History panel view for the Flet GUI.
"""

import flet as ft
from typing import Optional, Callable

class HistoryPanel:
    """Display transcription history."""

    def __init__(
        self,
        app_state: AppState,
        on_item_click: Optional[Callable] = None,
    ):
        self.app_state = app_state
        self._on_item_click = on_item_click
        self._list_view: Optional[ft.ListView] = None

    def build(self) -> ft.Container:
        """Build the history panel UI."""
        self._list_view = ft.ListView(
            expand=True,
            spacing=10,
        )

        return ft.Container(
            content=self._list_view,
            padding=ft.padding.all(20),
            expand=True,
        )

    def add_item(self, text: str):
        """Add a transcription to the history."""
        self._list_view.controls.append(
            ft.Text(text)
        )
        self._list_view.update()

    def clear(self):
        """Clear all history items."""
        self._list_view.controls.clear()
        self._list_view.update()
```

### Step 2: Integrate into FletApp

Add the view to `app.py`:

```python
from .views.history_panel import HistoryPanel

class FletApp:
    def __init__(self):
        # ... existing code ...
        self._history_panel: Optional[HistoryPanel] = None
        self._current_view = "transcription"  # Add "history" as an option

    def _build_content_area(self) -> ft.Container:
        """Build the main content area."""
        # Create history panel
        self._history_panel = HistoryPanel(
            self.app_state,
            on_item_click=self._on_history_item_click,
        )

        history_content = ft.Column(
            [
                self._history_panel.build(),
                self._build_history_controls(),
            ],
            expand=True,
        )

        # Add to the stack
        self._content_stack = ft.Stack([
            # ... existing views ...
            ft.Container(
                content=history_content,
                expand=True,
                visible=False,
                key="history",
            ),
        ])

        return ft.Container(content=self._content_stack, expand=True)

    def _on_history_item_click(self, item):
        """Handle history item click."""
        # Your handling logic
        pass
```

### Step 3: Add Navigation

Add navigation to your new view (e.g., in the controls or header):

```python
def _build_controls(self) -> ft.Container:
    """Build the bottom control panel."""
    history_button = ft.IconButton(
        icon=ft.icons.HISTORY,
        tooltip="History",
        on_click=lambda _: self._switch_view("history"),
    )

    # ... add to controls row
```

## Component Data Flow

### Recording Flow

1. User presses hotkey → `HotkeyManager` detects key press
2. `HotkeyManager` posts event to queue → `FletApp` processes it
3. `FletApp` calls `TranscriptionService.start_recording()`
4. `TranscriptionService` calls `MicrophoneTranscriber.start_recording()`
5. `MicrophoneTranscriber` emits state changes via callbacks
6. `TranscriptionService` puts events in queue
7. `FletApp` timer processes events, updates `AppState`
8. `TranscriptionPanel` reflects new state

### Settings Change Flow

1. User modifies settings in `SettingsPanel`
2. User clicks "Save" → validates inputs
3. `SettingsService.set_*()` methods update settings
4. `SettingsService.save()` persists to disk
5. `FletApp._on_settings_saved()` is called
6. `TranscriptionService.reinitialize()` reloads the transcriber
7. View switches back to transcription panel

## Key Design Decisions

### Why Flet?

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Python-native**: No need for separate UI code (unlike Qt/WebView)
- **Modern look**: Material Design 3 out of the box
- **Responsive**: Automatic layout management

### Why Service Layer?

- **Separation of concerns**: UI doesn't directly touch backend
- **Testability**: Services can be tested independently
- **Flexibility**: Easy to swap backends or add new UI frameworks
- **Thread safety**: Centralized place to handle threading issues

### Why Event Queue?

- **Non-blocking**: Background threads don't freeze the UI
- **Decoupling**: Services don't need to know about Flet internals
- **Reliability**: Events aren't lost if UI is busy

## Related Files

- `transcriber.py` - Core transcription engine
- `settings.py` - Settings persistence and validation
- `config.py` - Available models and languages
- `Phase-01-Foundation-and-Working-Prototype.md` - Implementation tasks
