"""
Main Flet application for faster-whisper-hotkey.

This module provides the main Flet application window and UI layout.
It integrates the transcription service, settings service, and hotkey manager
into a cohesive application with a modern Windows-first interface.

Classes
-------
FletApp
    Main Flet application class.
"""

import logging
import threading
import time
from typing import Optional

import flet as ft

from ..settings import load_settings
from .app_state import AppState, RecordingState
from .settings_service import SettingsService
from .transcription_service import TranscriptionService
from .hotkey_manager import HotkeyManager

logger = logging.getLogger(__name__)


class FletApp:
    """
    Main Flet application for faster-whisper-hotkey.

    This application provides:
    - A main window with header, content area, and controls
    - Push-to-talk transcription functionality
    - Real-time audio level visualization
    - Settings management interface
    - System tray integration (minimize to tray)
    - Hotkey detection in background

    Attributes
    ----------
    page
        The Flet page/control for the main window.
    app_state
        Shared application state.
    settings_service
        Settings management service.
    transcription_service
        Transcription service wrapper.
    hotkey_manager
        Hotkey detection manager.
    """

    def __init__(self):
        """Initialize the Flet application."""
        self.page: Optional[ft.Page] = None
        self.app_state = AppState()
        self.settings_service = SettingsService()
        self.transcription_service: Optional[TranscriptionService] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self._is_shutting_down = False

        # UI references
        self._status_indicator: Optional[ft.Container] = None
        self._status_text: Optional[ft.Text] = None
        self._transcription_display: Optional[ft.TextField] = None
        self._audio_level_bar: Optional[ft.ProgressBar] = None
        self._record_button: Optional[ft.ElevatedButton] = None
        self._hotkey_display: Optional[ft.Text] = None

    def build(self, page: ft.Page):
        """
        Build the main Flet application UI.

        Parameters
        ----------
        page
            The Flet page to build the UI on.
        """
        self.page = page
        page.title = "faster-whisper-hotkey"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.window_width = 500
        page.window_height = 700
        page.window_min_width = 400
        page.window_min_height = 500
        page.padding = 0
        page.bgcolor = ft.colors.SURFACE_CONTAINER_LOWEST if hasattr(ft.colors, 'SURFACE_CONTAINER_LOWEST') else ft.colors.GREY_50

        # Handle window events
        page.window_prevent_close = True
        page.on_window_event = self._on_window_event

        # Build the main UI
        page.add(self._build_header())
        page.add(self._build_main_content())
        page.add(self._build_controls())

        # Initialize services after UI is built
        self._initialize_services()

        # Start the event processing timer
        self._start_event_processing()

    def _build_header(self) -> ft.Container:
        """Build the header section with title and status."""
        self._status_indicator = ft.Container(
            width=12,
            height=12,
            border_radius=6,
            bgcolor=ft.colors.GREEN,
        )

        self._status_text = ft.Text(
            "Ready",
            color=ft.colors.ON_SURFACE,
            size=14,
        )

        self._hotkey_display = ft.Text(
            f"Hotkey: {self.app_state.hotkey.upper()}",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "faster-whisper-hotkey",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.PRIMARY,
                            ),
                            ft.Row(
                                [self._status_indicator, self._status_text],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            self._hotkey_display,
                            ft.Text(
                                "v0.4.3",
                                size=10,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAlignment.END,
                        spacing=4,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return header

    def _build_main_content(self) -> ft.Container:
        """Build the main content area with transcription display."""
        self._audio_level_bar = ft.ProgressBar(
            width=400,
            height=4,
            bgcolor=ft.colors.OUTLINE_VARIANT,
            color=ft.colors.PRIMARY,
            value=0.0,
            border_radius=2,
        )

        self._transcription_display = ft.TextField(
            value="",
            multiline=True,
            min_lines=8,
            max_lines=12,
            read_only=True,
            hint_text="Your transcription will appear here...",
            border_color=ft.colors.OUTLINE,
            border_radius=8,
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
            text_style=ft.TextStyle(
                size=14,
                color=ft.colors.ON_SURFACE,
            ),
        )

        content = ft.Container(
            content=ft.Column(
                [
                    # Audio level indicator
                    ft.Column(
                        [
                            ft.Text(
                                "Audio Level",
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(
                                content=self._audio_level_bar,
                                padding=ft.padding.only(bottom=8),
                            ),
                        ],
                        spacing=4,
                    ),
                    # Transcription display
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "Transcription",
                                        size=14,
                                        weight=ft.FontWeight.MEDIUM,
                                        color=ft.colors.ON_SURFACE,
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.COPY,
                                        tooltip="Copy to clipboard",
                                        on_click=self._copy_transcription,
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CONTENT_PASTE,
                                        tooltip="Paste to active window",
                                        on_click=self._paste_transcription,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            self._transcription_display,
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ],
                spacing=16,
                expand=True,
            ),
            padding=ft.padding.all(20),
            expand=True,
        )

        return content

    def _build_controls(self) -> ft.Container:
        """Build the bottom control panel."""
        self._record_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.MIC, size=20),
                    ft.Text("Push to Talk", size=14),
                ],
                spacing=8,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.colors.PRIMARY,
                color=ft.colors.ON_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.padding.symmetric(horizontal=24, vertical=16),
            ),
            on_click=self._on_record_button_click,
        )

        settings_button = ft.IconButton(
            icon=ft.icons.SETTINGS,
            tooltip="Settings",
            icon_size=24,
            on_click=self._open_settings,
        )

        minimize_button = ft.IconButton(
            icon=ft.icons.MINIMIZE,
            tooltip="Minimize to tray",
            icon_size=24,
            on_click=self._minimize_to_tray,
        )

        controls = ft.Container(
            content=ft.Row(
                [
                    self._record_button,
                    ft.Container(expand=True),
                    settings_button,
                    minimize_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _initialize_services(self):
        """Initialize the background services."""
        # Load settings
        settings = self.settings_service.load()
        if settings:
            self.app_state.update_from_settings(settings)
            self._hotkey_display.text = f"Hotkey: {settings.hotkey.upper()}"
        else:
            # Use defaults
            self._show_error("Failed to load settings. Using defaults.")

        # Initialize transcription service
        self.transcription_service = TranscriptionService(settings or self._create_default_settings())

        # Register callbacks
        self.transcription_service.on("state_change", self._on_state_change)
        self.transcription_service.on("transcription", self._on_transcription)
        self.transcription_service.on("transcription_start", self._on_transcription_start)
        self.transcription_service.on("audio_level", self._on_audio_level)
        self.transcription_service.on("error", self._on_error)

        # Initialize the transcriber
        if not self.transcription_service.initialize():
            self._show_error("Failed to initialize transcription service")

        # Initialize hotkey manager
        hotkey = self.app_state.hotkey
        self.hotkey_manager = HotkeyManager(hotkey)
        self.hotkey_manager.on("hotkey_press", self._on_hotkey_press)
        self.hotkey_manager.on("hotkey_release", self._on_hotkey_release)
        self.hotkey_manager.start()

    def _create_default_settings(self):
        """Create default settings when loading fails."""
        from ..settings import Settings
        return Settings(
            device_name="default",
            model_type="whisper",
            model_name="large-v3",
            compute_type="float16",
            device="cpu",
            language="en",
            hotkey="pause",
        )

    def _start_event_processing(self):
        """Start the event processing timer."""
        def process_events():
            if self._is_shutting_down:
                return

            # Process transcription events
            if self.transcription_service:
                self.transcription_service.process_events()

            # Process hotkey events
            if self.hotkey_manager:
                events = self.hotkey_manager.process_events()
                for event in events:
                    if event.action == "press":
                        self._handle_hotkey_press()
                    elif event.action == "release":
                        self._handle_hotkey_release()

            # Schedule next processing
            if self.page and not self._is_shutting_down:
                self.page.update()
                self.page.run_thread(process_events, delay=50)

        self.page.run_thread(process_events, delay=50)

    # Event handlers
    def _on_window_event(self, e):
        """Handle window events."""
        if e.data == "close":
            self._minimize_to_tray(None)

    def _on_record_button_click(self, e):
        """Handle record button click."""
        if self.app_state.recording_state == RecordingState.RECORDING:
            self.transcription_service.stop_recording()
        elif self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()

    def _on_hotkey_press(self, event):
        """Handle hotkey press from hotkey manager."""
        if self.app_state.activation_mode == "toggle":
            self._handle_hotkey_press()
        else:
            # Hold mode - handled in release
            pass

    def _on_hotkey_release(self, event):
        """Handle hotkey release from hotkey manager."""
        if self.app_state.activation_mode == "hold":
            self._handle_hotkey_release()

    def _handle_hotkey_press(self):
        """Handle hotkey press action."""
        if self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()
        elif self.app_state.activation_mode == "toggle":
            self.transcription_service.stop_recording()

    def _handle_hotkey_release(self):
        """Handle hotkey release action (hold mode)."""
        if self.app_state.recording_state == RecordingState.RECORDING:
            self.transcription_service.stop_recording()

    def _on_state_change(self, state: str):
        """Handle transcription state changes."""
        state_enum = RecordingState(state.lower()) if state.lower() in [s.value for s in RecordingState] else RecordingState.IDLE
        self.app_state.recording_state = state_enum

        # Update UI
        if self._status_text:
            self._status_text.text = state.capitalize()

        if self._status_indicator:
            color_map = {
                RecordingState.IDLE: ft.colors.GREEN,
                RecordingState.RECORDING: ft.colors.RED,
                RecordingState.TRANSCRIBING: ft.colors.AMBER,
                RecordingState.ERROR: ft.colors.RED,
            }
            self._status_indicator.bgcolor = color_map.get(state_enum, ft.colors.GREY)

        if self._record_button:
            if state_enum == RecordingState.RECORDING:
                self._record_button.content.controls[0].icon = ft.icons.STOP
                self._record_button.content.controls[1].text = "Stop Recording"
                self._record_button.style.bgcolor = ft.colors.ERROR
            else:
                self._record_button.content.controls[0].icon = ft.icons.MIC
                self._record_button.content.controls[1].text = "Push to Talk"
                self._record_button.style.bgcolor = ft.colors.PRIMARY

    def _on_transcription(self, text: str):
        """Handle completed transcription."""
        self.app_state.latest_transcription = text
        if self._transcription_display:
            self._transcription_display.value = text

    def _on_transcription_start(self, duration: float):
        """Handle transcription start."""
        self.app_state.recording_state = RecordingState.TRANSCRIBING
        if self._status_text:
            self._status_text.text = f"Transcribing ({duration:.1f}s)"

    def _on_audio_level(self, level: float):
        """Handle audio level updates."""
        self.app_state.audio_level = level
        if self._audio_level_bar:
            self._audio_level_bar.value = level

    def _on_error(self, error: str):
        """Handle transcription errors."""
        logger.error(f"Transcription error: {error}")
        self._show_error(error)

    def _copy_transcription(self, e):
        """Copy transcription to clipboard."""
        if self._transcription_display and self._transcription_display.value:
            self.page.set_clipboard(self._transcription_display.value)
            self._show_snackbar("Copied to clipboard")

    def _paste_transcription(self, e):
        """Paste transcription to active window (placeholder)."""
        if self._transcription_display and self._transcription_display.value:
            self._show_snackbar("Paste functionality - to be implemented")

    def _open_settings(self, e):
        """Open settings dialog (placeholder)."""
        self._show_snackbar("Settings dialog - to be implemented")

    def _minimize_to_tray(self, e):
        """Minimize window to tray."""
        if self.page:
            self.page.window_visible = False
            self.page.window_prevent_close = True
            self.app_state.window_visible = False

    def restore_from_tray(self):
        """Restore window from tray."""
        if self.page:
            self.page.window_visible = True
            self.page.window_prevent_close = True
            self.app_state.window_visible = True

    def _show_error(self, message: str):
        """Show an error message."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message, color=ft.colors.ERROR),
                    bgcolor=ft.colors.ERROR_CONTAINER,
                )
            )

    def _show_snackbar(self, message: str):
        """Show a snackbar message."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=2000,
                )
            )

    def shutdown(self):
        """Shutdown the application and cleanup resources."""
        self._is_shutting_down = True

        if self.transcription_service:
            self.transcription_service.shutdown()

        if self.hotkey_manager:
            self.hotkey_manager.stop()

        logger.info("FletApp shutdown complete")
