# Research: Interactive Onboarding Overlay

## Executive Summary

The faster-whisper-hotkey application is a tkinter-based GUI application with system tray integration. It currently has no onboarding or first-run tutorial experience. The app uses keyboard shortcuts (hotkeys) extensively but lacks an interactive tutorial to introduce these features to new users. An onboarding overlay can be implemented using tkinter's `Toplevel` windows with modal behavior, following existing patterns in `hotkey_dialog.py`.

## Architecture

```
User launches app
    ↓
Check for first-run (onboarding_completed flag in settings)
    ↓
If first-run: Show OnboardingOverlay
    ↓
Progress through tutorial steps
    ↓
Mark onboarding as completed
    ↓
User can access normal app features
```

### Existing Components to Integrate With

1. **`gui.py`** - Main GUI application with system tray
2. **`hotkey_dialog.py`** - Pattern for modal dialogs with key capture
3. **`settings.py`** - Settings persistence (add `onboarding_completed` field)
4. **`shortcuts_manager.py`** - Shortcuts configuration

## Critical Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/faster_whisper_hotkey/gui.py` | 1-530 | Main GUI entry point, system tray, settings window |
| `src/faster_whisper_hotkey/hotkey_dialog.py` | 1-266 | Modal dialog pattern for hotkey capture |
| `src/faster_whisper_hotkey/settings.py` | 1-84 | Settings dataclass and persistence |
| `src/faster_whisper_hotkey/shortcuts_manager.py` | 1-498 | Keyboard shortcuts management |

## Data Flow

```
Application Start
    ↓
load_settings() → Check onboarding_completed
    ↓
If not completed:
    OnboardingOverlay.show()
    ↓
    Step 1: Welcome
    ↓
    Step 2: System Tray Introduction
    ↓
    Step 3: Recording Hotkey (Interactive)
    ↓
    Step 4: Settings Window (Interactive)
    ↓
    Step 5: History Panel (Interactive)
    ↓
    Step 6: Completion
    ↓
    Save onboarding_completed = True
```

## Dependencies

- **Requires:**
  - `tkinter` - For overlay UI (already used)
  - `settings.py` - For first-run detection and completion tracking
  - `gui.py` - Main application to trigger onboarding

- **Required by:**
  - `gui.py` - Will call the onboarding module on startup

## Patterns & Conventions

### Modal Dialog Pattern (from `hotkey_dialog.py`)

```python
class TutorialDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.transient(parent)  # Stays on top
        self.dialog.grab_set()  # Modal - blocks other windows
        # Center on parent
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.dialog.geometry(f"+{x}+{y}")
```

### Settings Persistence Pattern (from `settings.py`)

```python
# Add to Settings dataclass
@dataclass
class Settings:
    # ... existing fields ...
    onboarding_completed: bool = False

# In load_settings(), add:
data.setdefault("onboarding_completed", False)
```

### UI Frame Pattern (from `gui.py`)

```python
main_frame = ttk.Frame(dialog, padding=20)
main_frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(main_frame, text="Title", font=("", 12, "bold")).pack(anchor=tk.W)
ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(5, 10))
```

## Edge Cases & Gotchas

1. **No settings file on first run** - `load_settings()` returns `None`; need to handle gracefully
2. **Hidden root window** - Main tkinter root is hidden (`withdraw()`), onboarding should show anyway
3. **System tray icon in separate thread** - Onboarding runs in main thread, need to coordinate
4. **User closes onboarding prematurely** - Should offer to skip, with option to resume later
5. **Screen size differences** - Onboarding window should be reasonably sized and positioned
6. **Cross-platform differences** - Window positioning and behavior may vary on Windows/Linux/macOS

## Risks

- **Risk 1**: Onboarding might annoy repeat users
  - **Mitigation**: Add "Skip" button on each step, store completion flag

- **Risk 2**: Tutorial might become outdated if features change
  - **Mitigation**: Keep tutorial focused on core, stable features

- **Risk 3**: Modal dialogs can be disruptive
  - **Mitigation**: Make onboarding skippable, offer "Show Tutorial Again" option in settings

- **Risk 4**: Interactive steps may fail if user doesn't perform action
  - **Mitigation**: Add timeout and "Skip This Step" option

## Recommendations

### Implementation Plan

1. **Create `onboarding.py` module** with:
   - `OnboardingOverlay` class for managing tutorial flow
   - Individual step classes or methods
   - Interactive verification for key actions

2. **Tutorial Steps** (Show, Don't Tell approach):
   - **Step 1**: Welcome - Explain what the app does
   - **Step 2**: System Tray - Point to tray icon, have user click it
   - **Step 3**: Start Recording - Have user press the hotkey to record
   - **Step 4**: Settings - Guide user to open settings
   - **Step 5**: Completion - Summary and offer to show shortcuts panel

3. **Add to `settings.py`**:
   - `onboarding_completed: bool = False` field
   - `onboarding_version: int = 1` for future updates

4. **Integrate in `gui.py`**:
   - Check `onboarding_completed` on startup
   - Show onboarding if not completed
   - Add "Show Tutorial" menu option

5. **Design Considerations**:
   - Use consistent styling with existing dialogs
   - Progress indicator (Step X of Y)
   - Highlight/spotlight effect for UI elements to interact with
   - Success feedback when user completes interactive steps

### Code Structure

```python
# src/faster_whisper_hotkey/onboarding.py

class OnboardingOverlay:
    """Interactive onboarding tutorial for first-time users."""

    def __init__(self, parent, gui_ref, on_complete=None):
        self.parent = parent
        self.gui_ref = gui_ref  # Reference to WhisperHotkeyGUI
        self.on_complete = on_complete
        self.current_step = 0
        self.window = None

    def show(self):
        """Show the onboarding overlay."""
        # Create window, show first step

    def _show_step(self, step_index):
        """Show a specific tutorial step."""
        # Steps: welcome, tray_icon, hotkey, settings, complete

    def _next_step(self):
        """Advance to next step."""

    def _skip(self):
        """Skip the onboarding."""

    def complete(self):
        """Mark onboarding as complete."""
        # Save to settings
        # Call on_complete callback
```

## Next Steps

1. Create the `onboarding.py` module
2. Add `onboarding_completed` field to Settings
3. Integrate onboarding trigger in `gui.py`
4. Implement individual tutorial steps with interactive verification
5. Add "Show Tutorial" menu option for later access
