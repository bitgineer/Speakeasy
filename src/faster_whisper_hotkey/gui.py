"""
System tray GUI for faster-whisper-hotkey.

This module provides the main graphical user interface through a system
tray icon. It manages the transcription service, settings, history panel,
and user onboarding.

Classes
-------
TrayIcon
    System tray icon with dynamic status indication and animated recording state.

WhisperHotkeyGUI
    Main GUI application with system tray integration.

Functions
---------
main
    Entry point for GUI mode.

Notes
-----
The tray icon displays different colors based on state: green (idle),
red (recording with pulsing animation), orange (transcribing), and shows a
privacy shield when privacy mode is enabled. The tooltip shows current model
and status, and single-click actions are available for quick recording control.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import time
import math

# Handle pystray import
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"Required packages not installed: {e}")
    print("Run: pip install pystray Pillow")
    sys.exit(1)

from .settings import load_settings, save_settings, Settings, SETTINGS_FILE
from .history_panel import HistoryPanel
from .hotkey_dialog import show_hotkey_dialog
from .shortcuts_panel import show_shortcuts_panel
from .settings_panel import SettingsPanel
from .text_processing_panel import show_text_processing_panel
from .dictionary_panel import show_dictionary_panel
from .snippets_panel import show_snippets_panel
from .toast_notification import show_toast
from .progress_popup import ProgressPopup
from .recording_overlay import RecordingOverlayManager
from .theme import ThemeManager
from .shortcuts_integrator import get_shortcuts_integrator, initialize_shortcuts_system

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TrayIcon:
    """System tray icon with status indication and animated recording state."""

    # Colors for different states
    COLORS = {
        "idle": "#4CAF50",       # Green
        "recording": "#F44336",  # Red
        "transcribing": "#FF9800",  # Orange
    }

    def __init__(self, size: int = 64):
        self.size = size
        self.pulse_phase = 0.0  # For pulsing animation

    def create(self, state: str = "idle", privacy_mode: bool = False, pulse: float = 0.0) -> Image.Image:
        """Create an icon image for the given state.

        Parameters
        ----------
        state : str
            The state: "idle", "recording", or "transcribing"
        privacy_mode : bool
            Whether privacy mode is enabled
        pulse : float
            Pulse value from 0.0 to 1.0 for recording animation
        """
        color = self.COLORS.get(state, self.COLORS["idle"])

        # Create image
        image = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw pulsing outer ring for recording state
        if state == "recording" and pulse > 0:
            # Calculate pulse radius and opacity
            base_margin = 4
            max_pulse_radius = 10
            pulse_radius = base_margin + (max_pulse_radius * pulse)

            # Calculate opacity (fade out as it expands)
            opacity = int(255 * (1.0 - pulse))

            # Draw pulsing ring with transparency
            ring_size = self.size - int(pulse_radius * 2)

            # Create a temporary image for the pulsing ring with alpha
            temp_image = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_image)

            # Color with alpha for pulsing effect
            pulse_color = (*self._hex_to_rgb(color), opacity)

            temp_draw.ellipse(
                [pulse_radius, pulse_radius,
                 self.size - pulse_radius, self.size - pulse_radius],
                fill="",
                outline=pulse_color,
                width=3
            )

            # Composite the pulsing ring onto the main image
            image = Image.alpha_composite(image, temp_image)
            draw = ImageDraw.Draw(image)

        # Draw main circle
        margin = 4
        draw.ellipse(
            [margin, margin, self.size - margin, self.size - margin],
            fill=color,
            outline="#FFFFFF",
            width=2
        )

        # Draw microphone icon (simplified)
        center = self.size // 2
        mic_width = self.size // 4
        mic_height = self.size // 3

        # Mic body
        draw.rounded_rectangle(
            [center - mic_width//2, center - mic_height//2,
             center + mic_width//2, center + mic_height//2],
            radius=mic_width//2,
            fill="#FFFFFF"
        )

        # Mic stand
        draw.arc(
            [center - mic_width, center,
             center + mic_width, center + mic_height],
            start=0, end=180,
            fill="#FFFFFF",
            width=2
        )
        draw.line(
            [center, center + mic_height//2 + 4, center, center + mic_height],
            fill="#FFFFFF",
            width=2
        )

        # Draw privacy shield overlay if privacy mode is active
        if privacy_mode:
            shield_size = self.size // 4
            shield_x = self.size - shield_size - 2
            shield_y = 2

            # Shield background
            draw.polygon(
                [
                    (shield_x, shield_y),
                    (shield_x + shield_size, shield_y),
                    (shield_x + shield_size, shield_y + shield_size - 2),
                    (shield_x + shield_size // 2, shield_y + shield_size),
                    (shield_x, shield_y + shield_size - 2),
                ],
                fill="#2196F3",  # Blue for privacy shield
                outline="#FFFFFF",
                width=1
            )

            # Shield lock symbol
            lock_center_x = shield_x + shield_size // 2
            lock_center_y = shield_y + shield_size // 2
            lock_width = shield_size // 3

            # Lock body
            draw.rectangle(
                [lock_center_x - lock_width // 2, lock_center_y,
                 lock_center_x + lock_width // 2, lock_center_y + lock_width // 2],
                fill="#FFFFFF"
            )
            # Lock shackle
            draw.arc(
                [lock_center_x - lock_width // 3, lock_center_y - lock_width // 3,
                 lock_center_x + lock_width // 3, lock_center_y + lock_width // 6],
                start=0, end=180,
                fill="#FFFFFF",
                width=2
            )

        return image

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class WhisperHotkeyGUI:
    """Main GUI application with system tray."""

    def __init__(self):
        self.settings = load_settings()
        self.transcriber = None
        self.transcriber_thread = None
        self.is_running = False
        self.current_state = "idle"  # idle, recording, transcribing
        self.privacy_mode = getattr(self.settings, 'privacy_mode', False) if self.settings else False

        # Create tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()

        # Create tray icon
        self.tray_icon_generator = TrayIcon()
        self.icon = None

        # Animation state for pulsing recording indicator
        self.animation_running = False
        self.animation_thread = None
        self.pulse_value = 0.0
        self.last_state = "idle"

        # History panel
        history_max = self.settings.history_max_items if self.settings else 50
        self.history_panel = HistoryPanel(max_items=history_max)
        # Sync privacy mode with history panel
        self.history_panel.update_privacy_mode(self.privacy_mode)

        # Settings window reference
        self.settings_window = None

        # Shortcuts panel reference
        self.shortcuts_panel = None

        # Onboarding overlay reference
        self.onboarding = None

        # Progress popup for transcription feedback
        self.progress_popup = None
        self.transcription_start_time = None
        self.current_audio_duration = None

        # Dictionary panel reference
        self.dictionary_panel = None

        # Snippets panel reference
        self.snippets_panel = None
        # Theme manager for dark/light mode
        self.theme_manager = None
        self.root.after(100, self._init_theme_manager)

        # Track recording state for notifications
        self.recording_start_notified = False

        # Recording overlay manager
        self.recording_overlay = RecordingOverlayManager(self.root)

        # Shortcuts integrator
        self.shortcuts_integrator = None
        self._init_shortcuts_system()


    def _init_shortcuts_system(self):
        """Initialize the shortcuts system and register action handlers."""
        try:
            initialize_shortcuts_system()
            self.shortcuts_integrator = get_shortcuts_integrator()
            self._register_shortcut_handlers()
            logger.info("Shortcuts system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize shortcuts system: {e}")

    def _register_shortcut_handlers(self):
        """Register action handlers for shortcuts."""
        if not self.shortcuts_integrator:
            return

        # Register handlers for common shortcuts
        self.shortcuts_integrator.register_action_handler('show_history', self.show_history)
        self.shortcuts_integrator.register_action_handler('show_settings', self.show_settings)
        self.shortcuts_integrator.register_action_handler('show_shortcuts', self.show_shortcuts)
        self.shortcuts_integrator.register_action_handler('show_dictionary', self.show_dictionary)
        self.shortcuts_integrator.register_action_handler('show_snippets', self.show_snippets)
        self.shortcuts_integrator.register_action_handler('show_text_processing', self.show_text_processing)
        self.shortcuts_integrator.register_action_handler('copy_last', self._shortcut_copy_last)
        self.shortcuts_integrator.register_action_handler('clear_history', self._shortcut_clear_history)
        self.shortcuts_integrator.register_action_handler('toggle_app', self.toggle_transcriber)
        self.shortcuts_integrator.register_action_handler('exit_app', self.exit_app)
        self.shortcuts_integrator.register_action_handler('toggle_privacy', self._shortcut_toggle_privacy)
        self.shortcuts_integrator.register_action_handler('record_start', self._shortcut_record_start)
        self.shortcuts_integrator.register_action_handler('record_stop', self._shortcut_record_stop)

        logger.info("Shortcut handlers registered")

    def _shortcut_copy_last(self):
        """Copy the last transcription to clipboard."""
        if self.history_panel and self.history_panel.history:
            last_item = self.history_panel.history[-1]
            text = last_item.get('text', '')
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                show_toast("Last transcription copied to clipboard", title="Copied", duration=2000)

    def _shortcut_clear_history(self):
        """Clear the transcription history."""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            if self.history_panel:
                self.history_panel.clear_history()
            show_toast("History cleared", title="Cleared", duration=2000)

    def _shortcut_toggle_privacy(self):
        """Toggle privacy mode."""
        if self.settings:
            self.settings.privacy_mode = not getattr(self.settings, 'privacy_mode', False)
            self.privacy_mode = self.settings.privacy_mode
            # Save settings
            save_settings(self.settings.__dict__)
            # Update history panel
            if self.history_panel:
                self.history_panel.update_privacy_mode(self.privacy_mode)
            # Show notification
            status = "enabled" if self.privacy_mode else "disabled"
            show_toast(f"Privacy mode {status}", title="Privacy Mode", duration=2000)

    def _shortcut_record_start(self):
        """Start recording immediately."""
        if self.transcriber and not self.transcriber.is_recording:
            self.transcriber.start_recording()

    def _shortcut_record_stop(self):
        """Stop recording and transcribe."""
        if self.transcriber and self.transcriber.is_recording:
            self.transcriber.stop_recording_and_transcribe()

    def _init_theme_manager(self):
        """Initialize the theme manager (delayed to avoid issues with early window creation)."""
        if self.theme_manager is None:
            # Get theme mode from settings
            theme_mode = getattr(self.settings, 'theme_mode', 'system') if self.settings else 'system'

            # Create save callback to persist theme changes to main settings
            def save_theme_callback(mode: str):
                if self.settings:
                    self.settings.theme_mode = mode
                    # Save to settings file
                    from .settings import save_settings
                    save_settings(self.settings.__dict__)

            self.theme_manager = ThemeManager(
                self.root,
                initial_mode=theme_mode,
                save_callback=save_theme_callback
            )
            # Apply theme to all existing windows
            self._apply_theme_to_all_windows()

    def _apply_theme_to_all_windows(self):
        """Apply current theme to all windows."""
        if self.theme_manager:
            # Apply to root
            self.theme_manager.apply_theme()
            # Apply to settings window if exists
            if self.settings_window and self.settings_window.winfo_exists():
                self.theme_manager.apply_to_window(self.settings_window)
            # Apply to other windows
            if hasattr(self, 'history_panel') and self.history_panel.window:
                if self.history_panel.window.winfo_exists():
                    self.theme_manager.apply_to_window(self.history_panel.window)

    def _on_theme_changed(self, mode: str):
        """Callback when theme is changed."""
        if self.theme_manager:
            self.theme_manager.set_mode(mode)
            self._apply_theme_to_all_windows()
    def create_menu(self):
        """Create the tray menu."""
        menu_items = [
            pystray.MenuItem(
                "Status: " + ("Running" if self.is_running else "Stopped"),
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start" if not self.is_running else "Stop",
                self.toggle_transcriber
            ),
            pystray.MenuItem("Settings...", self.show_settings),
            pystray.MenuItem("Shortcuts...", self.show_shortcuts),
            pystray.MenuItem("Text Processing...", self.show_text_processing),
            pystray.MenuItem("Dictionary...", self.show_dictionary),
            pystray.MenuItem("Snippets...", self.show_snippets),
            pystray.MenuItem("History", self.show_history),
            pystray.MenuItem("Show Tutorial...", self.show_tutorial),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app),
        ]
        return pystray.Menu(*menu_items)

    def toggle_transcriber(self, icon=None, item=None):
        """Start or stop the transcriber."""
        if self.is_running:
            self.stop_transcriber()
        else:
            self.start_transcriber()

    def start_transcriber(self):
        """Start the transcription service."""
        if self.is_running:
            return

        self.settings = load_settings()
        if not self.settings:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                "No settings found. Please configure settings first."
            ))
            return

        try:
            # Import here to avoid circular imports
            from .transcriber import MicrophoneTranscriber

            self.transcriber = MicrophoneTranscriber(
                self.settings,
                on_state_change=self.on_state_change,
                on_transcription=self.on_transcription,
                on_transcription_start=self.on_transcription_start,
                on_audio_level=self.on_audio_level
            )

            self.is_running = True
            self.update_icon("idle")
            self.update_menu()

            # Start shortcuts keyboard listener
            if self.shortcuts_integrator:
                self.shortcuts_integrator.start_keyboard_listener()

            # Run transcriber in background thread
            self.transcriber_thread = threading.Thread(
                target=self._run_transcriber,
                daemon=True
            )
            self.transcriber_thread.start()

            logger.info("Transcriber started")

        except Exception as e:
            logger.error(f"Failed to start transcriber: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Failed to start transcriber:\n{e}"
            ))

    def _run_transcriber(self):
        """Run the transcriber (in background thread)."""
        try:
            self.transcriber.run()
        except Exception as e:
            logger.error(f"Transcriber error: {e}")
        finally:
            self.is_running = False
            # Stop shortcuts keyboard listener
            if self.shortcuts_integrator:
                self.shortcuts_integrator.stop_keyboard_listener()
            self.update_icon("idle")
            self.update_menu()

    def stop_transcriber(self):
        """Stop the transcription service."""
        if not self.is_running:
            return

        self.is_running = False
        if self.transcriber:
            self.transcriber.stop()
            self.transcriber = None

        # Stop shortcuts keyboard listener
        if self.shortcuts_integrator:
            self.shortcuts_integrator.stop_keyboard_listener()

        self.update_icon("idle")
        self.update_menu()
        logger.info("Transcriber stopped")

    def on_state_change(self, state: str):
        """Callback when transcriber state changes."""
        self.last_state = self.current_state
        self.current_state = state

        # Handle state-specific notifications and actions
        if state == "recording" and self.last_state != "recording":
            # Recording started - show notification and start animation
            if not self.recording_start_notified:
                self.recording_start_notified = True
                self._show_recording_started_notification()
            self._start_animation()
            # Show the recording overlay
            if self.recording_overlay:
                self.root.after(0, self.recording_overlay.show_recording)

        elif state == "transcribing" and self.last_state != "transcribing":
            # Transcription started
            self.recording_start_notified = False
            self._stop_animation()
            self.root.after(0, self._show_progress_popup)
            # Hide the recording overlay
            if self.recording_overlay:
                self.root.after(0, self.recording_overlay.hide_transcribing)

        elif state == "idle":
            # Back to idle - stop animation and hide progress popup
            self.recording_start_notified = False
            self._stop_animation()
            self.root.after(0, self._hide_progress_popup)
            # Ensure overlay is hidden
            if self.recording_overlay:
                self.root.after(0, self.recording_overlay.hide_transcribing)

        self.update_icon(state)
        self.update_tooltip()

    def _show_recording_started_notification(self):
        """Show notification when recording starts."""
        show_toast(
            message="Recording started...\nPress the hotkey again to stop.",
            title="Recording",
            duration=2000,
            icon="info"
        )

    def _start_animation(self):
        """Start the pulsing animation for recording state."""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(
                target=self._animation_loop,
                daemon=True
            )
            self.animation_thread.start()

    def _stop_animation(self):
        """Stop the pulsing animation."""
        self.animation_running = False
        self.pulse_value = 0.0

    def _animation_loop(self):
        """Animation loop for pulsing recording indicator."""
        while self.animation_running:
            # Update pulse value (0 to 1 and back)
            self.pulse_value = (math.sin(time.time() * 3) + 1) / 2  # 3 rad/sec pulse rate

            # Update icon with pulse effect
            if self.icon:
                try:
                    self.root.after(0, lambda: self._update_icon_with_pulse())
                except:
                    pass

            time.sleep(0.05)  # 20 FPS animation

    def _update_icon_with_pulse(self):
        """Update icon with current pulse value."""
        if self.icon and self.current_state == "recording":
            self.icon.icon = self.tray_icon_generator.create(
                "recording",
                self.privacy_mode,
                self.pulse_value
            )

    def update_tooltip(self):
        """Update the tooltip with current status and model info."""
        if not self.icon:
            return

        status_text = {
            "idle": "Idle",
            "recording": "Recording...",
            "transcribing": "Processing..."
        }.get(self.current_state, "Unknown")

        # Get model info
        model_name = getattr(self.settings, 'model_name', 'Unknown') if self.settings else 'Unknown'

        # Build tooltip
        if self.privacy_mode:
            tooltip = f"Faster Whisper Hotkey\n{status_text} | Model: {model_name} | 🔒 Privacy Mode"
        else:
            tooltip = f"Faster Whisper Hotkey\n{status_text} | Model: {model_name}"

        try:
            self.icon.title = tooltip
        except:
            pass  # pystray may not support dynamic tooltip updates on all platforms

    def on_transcription_start(self, audio_duration: float):
        """Callback when transcription processing starts."""
        import time
        self.transcription_start_time = time.time()
        self.current_audio_duration = audio_duration
        # Update progress popup with audio duration
        if self.progress_popup:
            self.progress_popup.audio_duration = audio_duration

    def on_transcription(self, text: str):
        """Callback when transcription is complete."""
        self.history_panel.add_transcription(text)

        # Show completion toast
        if text.strip():
            self._show_completion_toast(text)

    def on_audio_level(self, level: float):
        """Callback when audio level changes during recording.

        Args:
            level: Audio level from 0.0 (silent) to 1.0 (max)
        """
        # Update the recording overlay with the new audio level
        if self.recording_overlay:
            self.root.after(0, lambda: self.recording_overlay.update_audio_level(level))

    def _show_progress_popup(self):
        """Show the progress popup during transcription."""
        if self.progress_popup is None:
            self.progress_popup = ProgressPopup(
                self.root,
                self.current_audio_duration
            )

        message = "Processing audio..."
        if self.current_audio_duration:
            message = f"Processing audio ({self.current_audio_duration:.1f}s)..."

        self.progress_popup.show(message)

    def _hide_progress_popup(self):
        """Hide the progress popup."""
        if self.progress_popup:
            self.progress_popup.hide()

    def _show_completion_toast(self, text: str):
        """Show a toast notification when transcription completes."""
        # Truncate text for display
        preview = text[:50] + "..." if len(text) > 50 else text
        show_toast(
            message=f"Transcription complete:\n{preview}",
            title="Success",
            duration=3000,
            icon="success"
        )

    def update_icon(self, state: str):
        """Update the tray icon for the given state."""
        if self.icon:
            self.icon.icon = self.tray_icon_generator.create(state, self.privacy_mode)

    def update_menu(self):
        """Update the tray menu."""
        if self.icon:
            self.icon.menu = self.create_menu()

    def show_settings(self, icon=None, item=None):
        """Show the settings window."""
        self.root.after(0, self._create_settings_window)

    def show_shortcuts(self, icon=None, item=None):
        """Show the shortcuts management panel."""
        self.root.after(0, self._show_shortcuts_panel)

    def show_text_processing(self, icon=None, item=None):
        """Show the text processing settings panel."""
        self.root.after(0, self._show_text_processing_panel)

    def show_dictionary(self, icon=None, item=None):
        """Show the dictionary management panel."""
        self.root.after(0, self._show_dictionary_panel)

    def show_snippets(self, icon=None, item=None):
        """Show the snippets management panel."""
        self.root.after(0, self._show_snippets_panel)

    def _show_shortcuts_panel(self):
        """Show the shortcuts management panel (must run in main thread)."""
        if self.shortcuts_panel and hasattr(self.shortcuts_panel, 'window') and self.shortcuts_panel.window and self.shortcuts_panel.window.winfo_exists():
            self.shortcuts_panel.window.lift()
            self.shortcuts_panel.window.focus_force()
            return

        self.shortcuts_panel = show_shortcuts_panel(
            self.root,
            on_change=self._on_shortcuts_changed
        )

    def _on_shortcuts_changed(self):
        """Callback when shortcuts are changed."""
        # Reload shortcuts in the integrator
        if self.shortcuts_integrator:
            self.shortcuts_integrator.reload_shortcuts()
            # Restart keyboard listener to pick up new shortcuts
            if self.is_running:
                self.shortcuts_integrator.stop_keyboard_listener()
                self.shortcuts_integrator.start_keyboard_listener()
        logger.info("Shortcuts configuration changed")

    def _show_text_processing_panel(self):
        """Show the text processing settings panel (must run in main thread)."""
        self.settings = load_settings()  # Refresh settings

        self.text_processing_panel = show_text_processing_panel(
            self.root,
            self.settings,
            on_save=self._on_text_processing_changed
        )

    def _on_text_processing_changed(self, text_processing_config):
        """Callback when text processing settings are changed."""
        logger.info("Text processing configuration changed")
        # Reload the text processor in the transcriber
        if self.transcriber:
            self.transcriber.reload_text_processor()

    def _show_dictionary_panel(self):
        """Show the dictionary management panel (must run in main thread)."""
        if self.dictionary_panel and hasattr(self.dictionary_panel, 'window') and self.dictionary_panel.window and self.dictionary_panel.window.winfo_exists():
            self.dictionary_panel.window.lift()
            self.dictionary_panel.window.focus_force()
            return

        self.dictionary_panel = show_dictionary_panel(
            self.root,
            on_close=self._on_dictionary_closed
        )

    def _on_dictionary_closed(self):
        """Callback when dictionary panel is closed."""
        # Reload the dictionary in the text processor
        if self.transcriber:
            self.transcriber.reload_text_processor()

    def _show_snippets_panel(self):
        """Show the snippets management panel (must run in main thread)."""
        from .snippets_panel import show_snippets_panel

        if self.snippets_panel and hasattr(self.snippets_panel, 'window') and self.snippets_panel.window and self.snippets_panel.window.winfo_exists():
            self.snippets_panel.window.lift()
            self.snippets_panel.window.focus_force()
            return

        self.snippets_panel = show_snippets_panel(
            self.root,
            on_close=self._on_snippets_closed
        )

    def _on_snippets_closed(self):
        """Callback when snippets panel is closed."""
        # Reload snippets manager
        from .snippets_manager import get_snippets_manager
        get_snippets_manager().reload()
        logger.info("Snippets configuration reloaded")

    def _create_settings_window(self):
        """Create and show the settings window (must run in main thread)."""
        # Check if settings panel already exists and show it
        if self.settings_window:
            self.settings_window.show()
            return

        # Create the new settings panel with callbacks
        self.settings_window = SettingsPanel(
            parent=self.root,
            on_settings_changed=self._on_settings_changed,
            on_restart_required=self._on_settings_restart_required,
            on_theme_changed=self._on_theme_changed
        )
        self.settings_window.show()

    def _on_settings_changed(self):
        """Called when settings are changed in the settings panel."""
        # Reload settings
        self.settings = load_settings()
        self.privacy_mode = self.settings.privacy_mode

        # Update history panel
        self.history_panel.update_privacy_mode(self.privacy_mode)

        # Update icon
        self.update_icon(self.current_state)

        logger.info("Settings updated")

    def _on_settings_restart_required(self):
        """Called when settings change requires transcriber restart."""
        # Show toast notification about restart
        show_toast(
            self.root,
            "Settings Changed",
            "Restart transcriber for changes to take effect",
            duration=5000
        )


    def show_history(self, icon=None, item=None):
        """Show the history panel."""
        self.root.after(0, self.history_panel.show)

    def show_tutorial(self, icon=None, item=None):
        """Show the interactive tutorial on demand."""
        self.root.after(0, self._show_onboarding)

    def _show_onboarding(self):
        """Show the onboarding tutorial (must run in main thread)."""
        from .onboarding import OnboardingOverlay

        # Don't show if already visible
        if self.onboarding and self.onboarding.window and self.onboarding.window.winfo_exists():
            self.onboarding.window.lift()
            self.onboarding.window.focus_force()
            return

        self.onboarding = OnboardingOverlay(
            self.root,
            self,
            on_complete=self._onboarding_complete
        )
        self.onboarding.show()

    def _onboarding_complete(self, skipped: bool = False):
        """Callback when onboarding is completed or skipped."""
        import json

        # Load current settings as dict
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        # Mark onboarding as completed
        data["onboarding_completed"] = True

        # Save
        save_settings(data)
        self.settings = load_settings()

        logger.info(f"Onboarding tutorial {'skipped' if skipped else 'completed'}")

    def _check_onboarding_needed(self):
        """Check if onboarding is needed and show it if so."""
        onboarding_completed = getattr(self.settings, 'onboarding_completed', False) if self.settings else False

        if not onboarding_completed:
            # Small delay to let the app initialize fully
            self.root.after(1500, self._show_onboarding)

    def exit_app(self, icon=None, item=None):
        """Exit the application."""
        self.stop_transcriber()
        self.history_panel.close()
        if self.icon:
            self.icon.stop()
        self.root.quit()

    def run(self):
        """Run the application."""
        # Create initial icon
        icon_image = self.tray_icon_generator.create("idle")

        # Set initial tooltip
        model_name = getattr(self.settings, 'model_name', 'Unknown') if self.settings else 'Unknown'
        initial_tooltip = f"Faster Whisper Hotkey\nIdle | Model: {model_name}"
        if self.privacy_mode:
            initial_tooltip += " | 🔒 Privacy Mode"

        self.icon = pystray.Icon(
            "faster-whisper-hotkey",
            icon_image,
            initial_tooltip,
            menu=self.create_menu(),
            on_click=self._on_icon_click
        )

        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()

        logger.info("Faster Whisper Hotkey GUI started")
        logger.info("Right-click the tray icon for options")
        logger.info("Left-click the tray icon for quick actions")

        # Check if onboarding is needed for first-time users
        self._check_onboarding_needed()

        # Run tkinter mainloop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

    def _on_icon_click(self, icon, button, time):
        """Handle single-click on tray icon for quick access actions.

        Left click: Toggle recording (if running) or show status
        Right click: Show menu (handled by pystray)
        """
        if button == pystray.MouseButton.LEFT:
            # Single left click - quick action based on current state
            if self.is_running:
                if self.current_state == "idle":
                    # Currently idle, show toast indicating ready
                    show_toast(
                        message=f"Ready to record.\nPress {self.settings.hotkey.upper() if self.settings else 'HOTKEY'} to start.",
                        title="Status",
                        duration=2000,
                        icon="info"
                    )
                elif self.current_state == "recording":
                    # Currently recording, show info
                    show_toast(
                        message="Recording in progress.\nRelease hotkey to stop.",
                        title="Recording",
                        duration=1500,
                        icon="info"
                    )
                elif self.current_state == "transcribing":
                    # Currently transcribing
                    show_toast(
                        message="Processing transcription...",
                        title="Processing",
                        duration=1500,
                        icon="info"
                    )
            else:
                # Not running, offer to start
                show_toast(
                    message="Transcriber is stopped.\nUse the menu to start it.",
                    title="Stopped",
                    duration=2000,
                    icon="warning"
                )


def main():
    """Entry point for GUI mode."""
    app = WhisperHotkeyGUI()
    app.run()


if __name__ == "__main__":
    main()
