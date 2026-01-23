"""
Transcription panel view for the Flet GUI.

This module provides the main transcription interface with push-to-talk
button, audio level indicator, and transcription display.
"""

import logging
from typing import Callable, Optional

import flet as ft

from ..app_state import AppState, RecordingState

logger = logging.getLogger(__name__)


class TranscriptionPanel:
    """
    Main transcription panel with recording controls and display.

    This panel provides:
    - Large, prominent "Push to Talk" button with visual feedback
    - Live audio level indicator (visualizer bar)
    - Status text showing current state (Ready, Recording, Transcribing, Error)
    - Real-time transcription result display area
    - "Copy to Clipboard" and "Paste" buttons for the latest transcription

    Attributes
    ----------
    app_state
        Shared application state.
    on_copy
        Callback when copy button is clicked.
    on_paste
        Callback when paste button is clicked.
    """

    def __init__(
        self,
        app_state: AppState,
        on_copy: Optional[Callable[[], None]] = None,
        on_paste: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the transcription panel.

        Parameters
        ----------
        app_state
            Shared application state.
        on_copy
            Callback when copy to clipboard is requested.
        on_paste
            Callback when paste to active window is requested.
        """
        self.app_state = app_state
        self._on_copy = on_copy
        self._on_paste = on_paste

        # UI components
        self._audio_level_bar: Optional[ft.ProgressBar] = None
        self._transcription_display: Optional[ft.TextField] = None
        self._record_button: Optional[ft.ElevatedButton] = None
        self._status_text: Optional[ft.Text] = None
        self._status_indicator: Optional[ft.Container] = None

    def build(self) -> ft.Container:
        """
        Build the transcription panel UI.

        Returns
        -------
        ft.Container
            The transcription panel container.
        """
        # Audio level indicator
        self._audio_level_bar = ft.ProgressBar(
            width=400,
            height=4,
            bgcolor=ft.colors.OUTLINE_VARIANT,
            color=ft.colors.PRIMARY,
            value=0.0,
            border_radius=2,
        )

        # Status indicator and text
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

        # Transcription display
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

        # Recording button with pulsing animation capability
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
                padding=ft.padding.symmetric(horizontal=32, vertical=20),
            ),
            width=200,
            height=60,
        )

        # Build the panel layout
        panel = ft.Container(
            content=ft.Column(
                [
                    # Status row
                    ft.Row(
                        [self._status_indicator, self._status_text],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    # Audio level section
                    ft.Column(
                        [
                            ft.Text(
                                "Audio Level",
                                size=12,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(
                                content=self._audio_level_bar,
                                padding=ft.padding.only(bottom=4),
                            ),
                        ],
                        spacing=4,
                    ),
                    # Transcription display section
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
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.icons.COPY,
                                        tooltip="Copy to clipboard",
                                        on_click=self._on_copy_click,
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.CONTENT_PASTE,
                                        tooltip="Paste to active window",
                                        on_click=self._on_paste_click,
                                    ),
                                ],
                            ),
                            self._transcription_display,
                        ],
                        spacing=8,
                        expand=True,
                    ),
                    # Recording button centered
                    ft.Column(
                        [self._record_button],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=16,
                expand=True,
            ),
            padding=ft.padding.all(20),
            expand=True,
        )

        return panel

    def _on_copy_click(self, e):
        """Handle copy button click."""
        if self._on_copy:
            self._on_copy()

    def _on_paste_click(self, e):
        """Handle paste button click."""
        if self._on_paste:
            self._on_paste()

    # Update methods for state changes
    def update_state(self, state: RecordingState):
        """
        Update the UI to reflect the current recording state.

        Parameters
        ----------
        state
            The current recording state.
        """
        if not self._status_text or not self._status_indicator or not self._record_button:
            return

        # Update status text
        status_messages = {
            RecordingState.IDLE: "Ready",
            RecordingState.RECORDING: "Recording...",
            RecordingState.TRANSCRIBING: "Transcribing...",
            RecordingState.ERROR: "Error",
        }
        self._status_text.text = status_messages.get(state, "Unknown")

        # Update status indicator color
        color_map = {
            RecordingState.IDLE: ft.colors.GREEN,
            RecordingState.RECORDING: ft.colors.RED,
            RecordingState.TRANSCRIBING: ft.colors.AMBER,
            RecordingState.ERROR: ft.colors.RED,
        }
        self._status_indicator.bgcolor = color_map.get(state, ft.colors.GREY)

        # Update button appearance
        if state == RecordingState.RECORDING:
            self._record_button.content.controls[0].icon = ft.icons.STOP
            self._record_button.content.controls[1].text = "Stop Recording"
            self._record_button.style.bgcolor = ft.colors.ERROR
        else:
            self._record_button.content.controls[0].icon = ft.icons.MIC
            self._record_button.content.controls[1].text = "Push to Talk"
            self._record_button.style.bgcolor = ft.colors.PRIMARY

    def update_transcription(self, text: str):
        """
        Update the transcription display with new text.

        Parameters
        ----------
        text
            The transcribed text to display.
        """
        if self._transcription_display:
            self._transcription_display.value = text

    def update_audio_level(self, level: float):
        """
        Update the audio level indicator.

        Parameters
        ----------
        level
            Audio level from 0.0 to 1.0.
        """
        if self._audio_level_bar:
            self._audio_level_bar.value = level

    def get_transcription_text(self) -> str:
        """
        Get the current transcription text.

        Returns
        -------
        str
            The current text in the transcription display.
        """
        if self._transcription_display:
            return self._transcription_display.value or ""
        return ""

    # Public properties for accessing UI components
    @property
    def record_button(self) -> Optional[ft.ElevatedButton]:
        """Get the record button for event binding."""
        return self._record_button

    @property
    def transcription_display(self) -> Optional[ft.TextField]:
        """Get the transcription display field."""
        return self._transcription_display

    @property
    def audio_level_bar(self) -> Optional[ft.ProgressBar]:
        """Get the audio level bar."""
        return self._audio_level_bar
