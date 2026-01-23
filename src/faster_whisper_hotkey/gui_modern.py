"""
Modern system tray GUI for faster-whisper-hotkey.

This module provides the main modern graphical user interface through a
system tray icon. It integrates:
- Modern theme system with light/dark mode
- Modern history panel
- Modern settings window
- Improved iconography
- Tabbed interface for settings

Classes
-------
ModernTrayIcon
    System tray icon with modern design and status indication.

ModernWhisperHotkeyGUI
    Main modern GUI application with system tray integration.

Functions
---------
main
    Entry point for modern GUI mode.

Notes
-----
The tray icon displays different colors based on state: green (idle),
red (recording), orange (transcribing), and shows a privacy shield
when privacy mode is enabled.
"""

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from typing import Optional

# Handle pystray import
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Required packages not installed: {e}")
    print("Run: pip install pystray Pillow")
    sys.exit(1)

from .settings import load_settings, save_settings, Settings, SETTINGS_FILE
from .history_panel_modern import ModernHistoryPanel
from .hotkey_dialog import show_hotkey_dialog
from .theme import ThemeManager
from .icons import IconFactory
from .settings_modern import show_modern_settings
from .streaming_preview import StreamingPreviewWindow

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ModernTrayIcon:
    """Modern system tray icon with status indication."""

    # Colors for different states (Material Design shades)
    COLORS = {
        "idle": "#4CAF50",       # Green 500
        "recording": "#F44336",  # Red 500
        "transcribing": "#FF9800",  # Orange 500
    }

    def __init__(self, size: int = 64):
        """Initialize tray icon generator.

        Args:
            size: Icon size in pixels
        """
        self.size = size

    def create(self, state: str = "idle", privacy_mode: bool = False,
               theme_mode: str = "light") -> Image.Image:
        """Create an icon image for the given state.

        Args:
            state: Current state - "idle", "recording", "transcribing"
            privacy_mode: Whether privacy mode is active
            theme_mode: Theme mode - "light" or "dark"

        Returns:
            PIL Image for the tray icon
        """
        color = self.COLORS.get(state, self.COLORS["idle"])

        # Create image with transparent background
        image = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw circle with modern subtle shadow
        margin = 6
        circle_size = self.size - margin * 2

        # Shadow offset
        shadow_offset = 2
        draw.ellipse(
            [margin + shadow_offset, margin + shadow_offset,
             self.size - margin + shadow_offset, self.size - margin + shadow_offset],
            fill=(0, 0, 0, 30),
            outline=None
        )

        # Main circle
        draw.ellipse(
            [margin, margin, self.size - margin, self.size - margin],
            fill=color,
            outline=(255, 255, 255, 200),
            width=3
        )

        # Draw modern microphone icon
        center = self.size // 2
        mic_width = self.size // 5
        mic_height = self.size // 2.8

        # Mic body (rounded rect)
        body_x = center - mic_width // 2
        body_y = center - mic_height // 2 - 2
        body_r = mic_width // 2

        # Draw rounded rectangle for mic body
        self._draw_rounded_rect(
            draw,
            [body_x, body_y, body_x + mic_width, body_y + mic_height],
            radius=body_r,
            fill=(255, 255, 255, 255)
        )

        # Mic stand
        stand_width = mic_width * 1.6
        stand_x = center - stand_width // 2
        stand_y = body_y + mic_height - 2

        # Curved stand
        draw.arc(
            [stand_x, stand_y, stand_x + stand_width, stand_y + mic_height // 2],
            start=0, end=180,
            fill=(255, 255, 255, 255),
            width=3
        )

        # Vertical line
        draw.line(
            [center, stand_y + mic_height // 4, center, stand_y + mic_height // 2 + 4],
            fill=(255, 255, 255, 255),
            width=3
        )

        # Draw privacy shield overlay if privacy mode is active
        if privacy_mode:
            self._draw_privacy_shield(draw)

        return image

    def _draw_rounded_rect(self, draw, bounds, radius, fill=None, outline=None):
        """Draw a rounded rectangle."""
        x1, y1, x2, y2 = bounds
        if fill:
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
            draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
            draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
            draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
            draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

    def _draw_privacy_shield(self, draw):
        """Draw privacy shield overlay."""
        shield_size = self.size // 4
        shield_x = self.size - shield_size - 4
        shield_y = 4

        # Shield background with gradient effect
        shield_color = (33, 150, 243, 255)  # Blue 500

        # Shield polygon
        points = [
            (shield_x, shield_y),
            (shield_x + shield_size, shield_y),
            (shield_x + shield_size, shield_y + shield_size - 3),
            (shield_x + shield_size // 2, shield_y + shield_size),
            (shield_x, shield_y + shield_size - 3),
        ]
        draw.polygon(points, fill=shield_color, outline=(255, 255, 255, 200), width=2)

        # Lock symbol
        lock_center_x = shield_x + shield_size // 2
        lock_center_y = shield_y + shield_size // 2
        lock_width = shield_size // 3.5

        # Lock body
        self._draw_rounded_rect(
            draw,
            [lock_center_x - lock_width // 2, lock_center_y,
             lock_center_x + lock_width // 2, lock_center_y + lock_width // 1.5],
            radius=2,
            fill=(255, 255, 255, 255)
        )

        # Lock shackle
        shackle_height = lock_width
        draw.arc(
            [lock_center_x - lock_width // 2.5, lock_center_y - shackle_height // 2,
             lock_center_x + lock_width // 2.5, lock_center_y + lock_width // 4],
            start=0, end=180,
            fill=(255, 255, 255, 255),
            width=2
        )


class ModernWhisperHotkeyGUI:
    """Main modern GUI application with system tray.

    Features:
    - Modern theme system with light/dark mode toggle
    - Redesigned settings window with tabs
    - Modern history panel
    - Improved tray icon with privacy shield
    - Smooth animations and transitions
    """

    def __init__(self):
        """Initialize the modern GUI."""
        self.settings = load_settings()
        self.transcriber = None
        self.transcriber_thread = None
        self.is_running = False
        self.current_state = "idle"
        self.privacy_mode = getattr(self.settings, 'privacy_mode', False) if self.settings else False

        # Create tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()

        # Initialize theme manager
        theme_mode = getattr(self.settings, 'theme_mode', 'light') if self.settings else 'light'
        self.theme_manager = ThemeManager(self.root)
        self.theme_manager.set_mode(theme_mode)

        # Icon factory
        self.icon_factory = IconFactory(self.theme_manager)

        # Create tray icon generator
        self.tray_icon_generator = ModernTrayIcon()
        self.icon = None

        # Modern history panel
        history_max = self.settings.history_max_items if self.settings else 50
        self.history_panel = ModernHistoryPanel(
            self.theme_manager,
            max_items=history_max,
            on_close=self._on_history_close
        )
        self.history_panel.update_privacy_mode(self.privacy_mode)

        # Settings window reference
        self.settings_window = None

        # Shortcuts panel reference
        self.shortcuts_panel = None

        # App rules panel reference
        self.app_rules_panel = None

        # Analytics panel reference
        self.analytics_panel = None

        # Onboarding overlay reference
        self.onboarding = None

        # Streaming preview window
        self.streaming_preview = None

    def create_menu(self):
        """Create the modern tray menu."""
        # Status item (non-clickable)
        status_text = "Status: Running" if self.is_running else "Status: Stopped"

        menu_items = [
            pystray.MenuItem(status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start" if not self.is_running else "Stop",
                self.toggle_transcriber
            ),
            pystray.MenuItem("Settings...", self.show_settings),
            pystray.MenuItem("App Rules...", self.show_app_rules),
            pystray.MenuItem("Shortcuts...", self.show_shortcuts),
            pystray.MenuItem("History", self.show_history),
            pystray.MenuItem("Usage Statistics...", self.show_analytics),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"Theme: {self.theme_manager.current_mode.title()}",
                self.toggle_theme
            ),
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
            from .transcriber import MicrophoneTranscriber

            self.transcriber = MicrophoneTranscriber(
                self.settings,
                on_state_change=self.on_state_change,
                on_transcription=self.on_transcription,
                on_streaming_update=self.on_streaming_update
            )

            self.is_running = True
            self.update_icon("idle")
            self.update_menu()

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

        self.update_icon("idle")
        self.update_menu()
        logger.info("Transcriber stopped")

    def on_state_change(self, state: str):
        """Callback when transcriber state changes."""
        self.current_state = state
        self.update_icon(state)

        # Handle streaming preview window
        if self.settings and getattr(self.settings, 'enable_streaming', False):
            if state == "recording":
                # Show streaming preview window when recording starts
                self.root.after(0, self._show_streaming_preview)
            elif state == "idle":
                # Hide streaming preview window when done
                self.root.after(0, self._hide_streaming_preview)

    def on_transcription(self, text: str):
        """Callback when transcription is complete."""
        self.history_panel.add_transcription(text)

    def _show_streaming_preview(self):
        """Show the streaming preview window."""
        if self.streaming_preview is None:
            self.streaming_preview = StreamingPreviewWindow(
                self.theme_manager,
                confidence_threshold=getattr(self.settings, 'confidence_threshold', 0.5),
                on_close=self._on_streaming_preview_close
            )
        self.streaming_preview.show()

    def _hide_streaming_preview(self):
        """Hide the streaming preview window."""
        if self.streaming_preview:
            self.streaming_preview.hide()
            self.streaming_preview = None

    def _on_streaming_preview_close(self):
        """Callback when streaming preview window is closed."""
        self.streaming_preview = None

    def on_streaming_update(self, text: str, confidence: float, is_final: bool):
        """Callback for streaming transcription updates."""
        if self.streaming_preview:
            self.root.after(0, lambda: self.streaming_preview.update_text(text, confidence, is_final))

    def update_icon(self, state: str):
        """Update the tray icon for the given state."""
        if self.icon:
            self.icon.icon = self.tray_icon_generator.create(
                state,
                self.privacy_mode,
                self.theme_manager.current_mode
            )

    def update_menu(self):
        """Update the tray menu."""
        if self.icon:
            self.icon.menu = self.create_menu()

    def toggle_theme(self, icon=None, item=None):
        """Toggle between light and dark theme."""
        new_mode = self.theme_manager.toggle_mode()

        # Save theme preference
        try:
            import json
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
        data["theme_mode"] = new_mode
        save_settings(data)
        self.settings = load_settings()

        # Update icon
        self.update_icon(self.current_state)
        self.update_menu()

        logger.info(f"Theme changed to {new_mode}")

    def show_settings(self, icon=None, item=None):
        """Show the modern settings window."""
        self.root.after(0, self._show_settings_window)

    def _show_settings_window(self):
        """Show the settings window (must run in main thread)."""
        if self.settings_window and hasattr(self.settings_window, 'window') and \
                self.settings_window.window and self.settings_window.window.winfo_exists():
            self.settings_window.window.lift()
            self.settings_window.window.focus_force()
            return

        from .settings_modern import ModernSettingsWindow

        self.settings_window = ModernSettingsWindow(
            self.root,
            self.theme_manager,
            self.settings,
            on_hotkey_change=self._configure_hotkey,
            on_settings_change=self._on_settings_changed
        )
        self.settings_window.show()

    def _on_settings_changed(self):
        """Callback when settings are changed."""
        logger.info("Settings changed")

    def _configure_hotkey(self):
        """Open hotkey configuration dialog."""
        current_hotkey = self.settings.hotkey if self.settings else "pause"
        current_mode = self.settings.activation_mode if self.settings else "hold"

        new_hotkey, new_mode = show_hotkey_dialog(
            self.root,
            current_hotkey,
            current_mode
        )

        if new_hotkey or new_mode:
            try:
                import json
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
            except:
                data = {}

            if new_hotkey:
                data["hotkey"] = new_hotkey
            if new_mode:
                data["activation_mode"] = new_mode

            save_settings(data)
            self.settings = load_settings()

            # Refresh settings window
            if self.settings_window and hasattr(self.settings_window, 'window') and \
                    self.settings_window.window and self.settings_window.window.winfo_exists():
                self.settings_window.window.destroy()
                self._show_settings_window()

            messagebox.showinfo(
                "Settings Updated",
                "Hotkey settings updated. Stop and restart the transcriber for changes to take effect."
            )

    def show_shortcuts(self, icon=None, item=None):
        """Show the shortcuts management panel."""
        self.root.after(0, self._show_shortcuts_panel)

    def _show_shortcuts_panel(self):
        """Show the shortcuts panel (must run in main thread)."""
        from .shortcuts_panel import show_shortcuts_panel

        if self.shortcuts_panel and hasattr(self.shortcuts_panel, 'window') and \
                self.shortcuts_panel.window and self.shortcuts_panel.window.winfo_exists():
            self.shortcuts_panel.window.lift()
            self.shortcuts_panel.window.focus_force()
            return

        self.shortcuts_panel = show_shortcuts_panel(
            self.root,
            on_change=self._on_shortcuts_changed
        )

    def _on_shortcuts_changed(self):
        """Callback when shortcuts are changed."""
        logger.info("Shortcuts configuration changed")

    def show_app_rules(self, icon=None, item=None):
        """Show the app rules management panel."""
        self.root.after(0, self._show_app_rules_panel)

    def _show_app_rules_panel(self):
        """Show the app rules panel (must run in main thread)."""
        from .app_rules_panel import show_app_rules_panel

        if not hasattr(self, 'app_rules_panel') or \
           (self.app_rules_panel and hasattr(self.app_rules_panel, 'window') and
            self.app_rules_panel.window and self.app_rules_panel.window.winfo_exists()):
            if hasattr(self, 'app_rules_panel') and self.app_rules_panel:
                self.app_rules_panel.window.lift()
                self.app_rules_panel.window.focus_force()
            return

        self.app_rules_panel = show_app_rules_panel(
            self.root,
            self.theme_manager,
            on_change=self._on_app_rules_changed
        )

    def _on_app_rules_changed(self):
        """Callback when app rules are changed."""
        logger.info("App rules configuration changed")

    def show_history(self, icon=None, item=None):
        """Show the modern history panel."""
        self.root.after(0, self.history_panel.show)

    def _on_history_close(self):
        """Callback when history panel is closed."""
        pass

    def show_analytics(self, icon=None, item=None):
        """Show the usage statistics/analytics dashboard."""
        self.root.after(0, self._show_analytics_panel)

    def _show_analytics_panel(self):
        """Show the analytics panel (must run in main thread)."""
        from .analytics_panel import show_analytics_panel

        if self.analytics_panel and hasattr(self.analytics_panel, 'window') and \
           self.analytics_panel.window and self.analytics_panel.window.winfo_exists():
            self.analytics_panel.window.lift()
            self.analytics_panel.window.focus_force()
            return

        self.analytics_panel = show_analytics_panel(
            self.root,
            self.theme_manager,
            on_close=self._on_analytics_close
        )

    def _on_analytics_close(self):
        """Callback when analytics panel is closed."""
        pass

    def show_tutorial(self, icon=None, item=None):
        """Show the interactive tutorial on demand."""
        self.root.after(0, self._show_onboarding)

    def _show_onboarding(self):
        """Show the onboarding tutorial (must run in main thread)."""
        from .onboarding import OnboardingOverlay

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

        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data["onboarding_completed"] = True
        save_settings(data)
        self.settings = load_settings()

        logger.info(f"Onboarding tutorial {'skipped' if skipped else 'completed'}")

    def _check_onboarding_needed(self):
        """Check if onboarding is needed and show it if so."""
        onboarding_completed = getattr(self.settings, 'onboarding_completed', False) if self.settings else False

        if not onboarding_completed:
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
        icon_image = self.tray_icon_generator.create(
            "idle",
            self.privacy_mode,
            self.theme_manager.current_mode
        )

        self.icon = pystray.Icon(
            "faster-whisper-hotkey",
            icon_image,
            "Faster Whisper Hotkey",
            menu=self.create_menu()
        )

        # Run icon in separate thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()

        logger.info("Faster Whisper Hotkey Modern GUI started")
        logger.info("Right-click the tray icon for options")

        # Check if onboarding is needed
        self._check_onboarding_needed()

        # Run tkinter mainloop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()


def main():
    """Entry point for modern GUI mode."""
    app = ModernWhisperHotkeyGUI()
    app.run()


if __name__ == "__main__":
    main()
