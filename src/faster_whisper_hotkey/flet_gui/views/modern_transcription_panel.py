"""
Modern transcription panel view for the Flet GUI.

This module provides a redesigned, modern transcription interface with:
- Large, centered transcription result display
- Floating action button for push-to-talk
- Recent transcriptions as quick-access cards
- Recording time elapsed counter
- Keyboard shortcut hints
- Enhanced visual feedback for recording state
"""

import logging
import time
from datetime import datetime
from typing import Callable, Optional, List

import flet as ft

from ..app_state import AppState, RecordingState
from ..history_manager import HistoryManager, HistoryItem
from ..theme import get_theme_manager, SPACING, BORDER_RADIUS
from ..components import Card, Button, ButtonVariant, StatusBadge, StatusType

logger = logging.getLogger(__name__)


class RecentTranscriptionCard(Card):
    """
    A card displaying a recent transcription for quick access.

    Parameters
    ----------
    item
        The history item to display.
    on_click
        Callback when the card is clicked.
    max_length
        Maximum text length to display.
    **kwargs
        Additional Card properties.
    """

    def __init__(
        self,
        item: HistoryItem,
        on_click: Optional[Callable] = None,
        max_length: int = 80,
        **kwargs,
    ):
        """
        Initialize the RecentTranscriptionCard.

        Parameters
        ----------
        item
            The history item to display.
        on_click
            Click callback.
        max_length
            Maximum text length.
        **kwargs
            Additional properties.
        """
        theme = get_theme_manager()

        # Format timestamp
        try:
            dt = datetime.fromisoformat(item.timestamp)
            time_str = self._format_relative_time(dt)
        except (ValueError, TypeError):
            time_str = "Unknown"

        # Truncate text
        text = item.text
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Build content
        content = ft.Column(
            [
                # Header with time
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.HISTORY,
                            size=14,
                            color=theme.colors.on_surface_variant,
                        ),
                        ft.Text(
                            time_str,
                            size=11,
                            color=theme.colors.on_surface_variant,
                        ),
                        ft.Container(expand=True),
                    ],
                    spacing=4,
                ),
                # Text content
                ft.Text(
                    text,
                    size=13,
                    color=theme.colors.on_surface,
                    max_lines=3,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=SPACING.xs,
            tight=True,
        )

        # Remove None from controls
        controls = [c for c in content.controls if c is not None]
        content.controls = controls

        super().__init__(
            content=content,
            variant="outlined",
            padding=SPACING.sm,
            on_click=on_click,
            **kwargs,
        )

        self._item = item

    def _format_relative_time(self, dt: datetime) -> str:
        """Format a relative time string (e.g., "2m ago", "1h ago")."""
        now = datetime.now()
        delta = now - dt

        seconds = delta.total_seconds()

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        else:
            days = int(seconds / 86400)
            return f"{days}d ago"

    @property
    def item(self) -> HistoryItem:
        """Get the history item."""
        return self._item


class ShortcutHint(ft.Container):
    """
    A keyboard shortcut hint badge.

    Parameters
    ----------
    key
        The key combination (e.g., "PAUSE", "Ctrl+H").
    description
        Optional description text.
    icon
        Optional icon to display.
    **kwargs
        Additional Container properties.
    """

    def __init__(
        self,
        key: str,
        description: str = "",
        icon: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the ShortcutHint.

        Parameters
        ----------
        key
            The key combination.
        description
            Optional description.
        icon
            Optional icon.
        **kwargs
            Additional properties.
        """
        theme = get_theme_manager()

        # Build content
        controls = []

        if icon:
            controls.append(
                ft.Icon(
                    icon,
                    size=14,
                    color=theme.colors.on_surface_variant,
                )
            )

        # Key badge
        controls.append(
            ft.Container(
                content=ft.Text(
                    key,
                    size=11,
                    weight=ft.FontWeight.MEDIUM,
                    color=theme.colors.on_surface,
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor=theme.colors.surface_container_low,
                border_radius=4,
                border=ft.border.all(1, theme.colors.outline_variant),
            )
        )

        if description:
            controls.append(
                ft.Text(
                    description,
                    size=11,
                    color=theme.colors.on_surface_variant,
                )
            )

        content = ft.Row(
            controls,
            spacing=SPACING.xs,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        super().__init__(
            content=content,
            **kwargs,
        )


class ModernTranscriptionPanel:
    """
    Modern transcription panel with enhanced UI.

    This panel provides:
    - Large, prominent "Push to Talk" button with visual feedback
    - Live audio level indicator (visualizer bar)
    - Status text showing current state (Ready, Recording, Transcribing, Error)
    - Real-time transcription result display area
    - Recording timer showing elapsed time
    - Recent transcriptions as quick-access cards
    - Keyboard shortcut hints
    - Copy to clipboard and paste buttons

    Attributes
    ----------
    app_state
        Shared application state.
    history_manager
        History manager for recent transcriptions.
    on_copy
        Callback when copy button is clicked.
    on_paste
        Callback when paste button is clicked.
    on_recent_click
        Callback when a recent transcription card is clicked.
    """

    def __init__(
        self,
        app_state: AppState,
        history_manager: HistoryManager,
        on_copy: Optional[Callable] = None,
        on_paste: Optional[Callable] = None,
        on_recent_click: Optional[Callable[[HistoryItem], None]] = None,
    ):
        """
        Initialize the modern transcription panel.

        Parameters
        ----------
        app_state
            Shared application state.
        history_manager
            History manager for recent transcriptions.
        on_copy
            Callback when copy to clipboard is requested.
        on_paste
            Callback when paste to active window is requested.
        on_recent_click
            Callback when a recent transcription is clicked.
        """
        self.app_state = app_state
        self.history_manager = history_manager
        self._on_copy = on_copy
        self._on_paste = on_paste
        self._on_recent_click = on_recent_click

        # UI components
        self._audio_level_bar: Optional[ft.ProgressBar] = None
        self._transcription_display: Optional[ft.TextField] = None
        self._record_button: Optional[ft.Container] = None
        self._record_icon: Optional[ft.Icon] = None
        self._record_text: Optional[ft.Text] = None
        self._status_badge: Optional[ft.Container] = None
        self._status_text: Optional[ft.Text] = None
        self._recording_timer: Optional[ft.Text] = None
        self._pulse_ring: Optional[ft.Container] = None
        self._recent_cards_container: Optional[ft.Column] = None
        self._shortcut_hints: Optional[ft.Row] = None

        # Recording state
        self._recording_start_time: Optional[float] = None
        self._timer_running: bool = False

    def build(self) -> ft.Container:
        """
        Build the modern transcription panel UI.

        Returns
        -------
        ft.Container
            The transcription panel container.
        """
        theme = get_theme_manager()

        # Build the main layout
        main_content = ft.Column(
            [
                # Status and timer row
                self._build_status_row(),
                # Recording button with pulse effect
                self._build_record_button_area(),
                # Transcription display
                self._build_transcription_display(),
                # Action buttons
                self._build_action_buttons(),
                # Recent transcriptions
                self._build_recent_transcriptions(),
                # Shortcut hints
                self._build_shortcut_hints(),
            ],
            spacing=SPACING.md,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=main_content,
            padding=ft.padding.symmetric(horizontal=SPACING.lg, vertical=SPACING.md),
            expand=True,
        )

    def _build_status_row(self) -> ft.Row:
        """Build the status row with badge and timer."""
        theme = get_theme_manager()

        # Status badge
        self._status_text = ft.Text(
            "Ready",
            size=13,
            weight=ft.FontWeight.MEDIUM,
            color=theme.colors.on_surface,
        )
        self._status_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=theme.colors.success,
                    ),
                    self._status_text,
                ],
                spacing=6,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=theme.colors.success_container,
            border_radius=16,
        )

        # Recording timer (hidden initially)
        self._recording_timer = ft.Text(
            "0:00",
            size=13,
            color=theme.colors.on_surface_variant,
            visible=False,
            width=60,
            text_align=ft.TextAlign.RIGHT,
        )

        return ft.Row(
            [
                self._status_badge,
                ft.Container(expand=True),
                self._recording_timer,
            ],
            width=400,
        )

    def _build_record_button_area(self) -> ft.Container:
        """Build the floating record button with pulse effect."""
        theme = get_theme_manager()

        # Pulse ring for recording state
        self._pulse_ring = ft.Container(
            width=90,
            height=90,
            border_radius=45,
            border=ft.border.all(3, theme.colors.recording),
            bgcolor=ft.colors.TRANSPARENT,
            opacity=0,
            animate_opacity=ft.Animation(
                duration=800,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        # Record button content
        self._record_icon = ft.Icon(
            ft.icons.MIC,
            size=32,
            color=theme.colors.on_primary,
        )
        self._record_text = ft.Text(
            "Push to Talk",
            size=14,
            weight=ft.FontWeight.MEDIUM,
            color=theme.colors.on_primary,
        )
        button_content = ft.Column(
            [
                self._record_icon,
                self._record_text,
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Record button (stacked with pulse ring)
        self._record_button = ft.Container(
            content=ft.Stack(
                [
                    self._pulse_ring,
                    ft.Container(
                        content=button_content,
                        width=80,
                        height=80,
                        border_radius=40,
                        bgcolor=theme.colors.primary,
                        alignment=ft.alignment.center,
                    ),
                ],
                width=90,
                height=90,
                alignment=ft.alignment.center,
            ),
            width=90,
            height=90,
            bgcolor=theme.colors.primary,
            border_radius=45,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                blur_radius=20,
                spread_radius=0,
                color=ft.colors.with_opacity(0.3, theme.colors.primary),
                offset=ft.Offset(0, 4),
            ),
            animate=ft.Animation(
                duration=200,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_click=self._on_record_click,
        )

        # Set cursor
        self._record_button.cursor = ft.MouseCursor.CLICKER
        self._record_button.content.cursor = ft.MouseCursor.CLICKER

        # Audio level bar below button
        self._audio_level_bar = ft.ProgressBar(
            width=200,
            height=4,
            bgcolor=theme.colors.surface_container_low,
            color=theme.colors.primary,
            value=0.0,
            border_radius=2,
        )

        return ft.Container(
            content=ft.Column(
                [
                    self._record_button,
                    ft.Container(
                        content=self._audio_level_bar,
                        padding=ft.padding.only(top=SPACING.sm),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=SPACING.sm),
        )

    def _build_transcription_display(self) -> ft.Container:
        """Build the transcription display area."""
        theme = get_theme_manager()

        self._transcription_display = ft.TextField(
            value="",
            multiline=True,
            min_lines=6,
            max_lines=10,
            read_only=True,
            hint_text="Your transcription will appear here...",
            border_color=theme.colors.outline_variant,
            border_radius=theme.radius.lg,
            bgcolor=theme.colors.surface_container_low,
            text_style=ft.TextStyle(
                size=14,
                color=theme.colors.on_surface,
            ),
            content_padding=ft.padding.all(SPACING.md),
            width=400,
        )

        return ft.Container(
            content=self._transcription_display,
            width=400,
        )

    def _build_action_buttons(self) -> ft.Row:
        """Build the action buttons row."""
        theme = get_theme_manager()

        copy_button = ft.IconButton(
            icon=ft.icons.COPY,
            icon_size=20,
            tooltip="Copy to clipboard",
            on_click=self._on_copy_click,
            style=ft.ButtonStyle(
                bgcolor=theme.colors.surface_container_low,
                icon_color=theme.colors.on_surface,
            ),
        )

        paste_button = ft.IconButton(
            icon=ft.icons.CONTENT_PASTE,
            icon_size=20,
            tooltip="Paste to active window",
            on_click=self._on_paste_click,
            style=ft.ButtonStyle(
                bgcolor=theme.colors.surface_container_low,
                icon_color=theme.colors.on_surface,
            ),
        )

        return ft.Row(
            [copy_button, paste_button],
            spacing=SPACING.sm,
        )

    def _build_recent_transcriptions(self) -> ft.Container:
        """Build the recent transcriptions section."""
        theme = get_theme_manager()

        # Section header
        header = ft.Row(
            [
                ft.Text(
                    "Recent",
                    size=13,
                    weight=ft.FontWeight.MEDIUM,
                    color=theme.colors.on_surface_variant,
                ),
                ft.Container(expand=True),
            ],
        )

        # Recent cards container
        self._recent_cards_container = ft.Column(
            [],
            spacing=SPACING.xs,
        )

        return ft.Container(
            content=ft.Column(
                [
                    header,
                    self._recent_cards_container,
                ],
                spacing=SPACING.xs,
            ),
            width=400,
            padding=ft.padding.only(top=SPACING.sm),
        )

    def _build_shortcut_hints(self) -> ft.Container:
        """Build the keyboard shortcut hints row."""
        theme = get_theme_manager()

        hints = [
            ShortcutHint(
                self.app_state.hotkey.upper(),
                icon=ft.icons.KEYBOARD,
            ),
        ]

        # Add history hotkey hint
        if hasattr(self.app_state, 'history_hotkey'):
            hints.append(
                ShortcutHint(
                    self.app_state.history_hotkey.upper(),
                    icon=ft.icons.HISTORY,
                )
            )

        self._shortcut_hints = ft.Row(
            hints,
            spacing=SPACING.sm,
        )

        return ft.Container(
            content=self._shortcut_hints,
            padding=ft.padding.only(top=SPACING.sm),
        )

    def _on_record_click(self, e):
        """Handle record button click."""
        # This will be handled by the parent app
        pass

    def _on_copy_click(self, e):
        """Handle copy button click."""
        if self._on_copy:
            self._on_copy()

    def _on_paste_click(self, e):
        """Handle paste button click."""
        if self._on_paste:
            self._on_paste()

    def _on_recent_card_click(self, item: HistoryItem):
        """Handle recent transcription card click."""
        if self._on_recent_click:
            self._on_recent_click(item)

    # Update methods for state changes
    def update_state(self, state: RecordingState):
        """
        Update the UI to reflect the current recording state.

        Parameters
        ----------
        state
            The current recording state.
        """
        theme = get_theme_manager()
        if not self._status_text or not self._record_button or not self._record_icon:
            return

        # Update status badge
        status_messages = {
            RecordingState.IDLE: ("Ready", theme.colors.success, theme.colors.success_container),
            RecordingState.RECORDING: ("Recording", theme.colors.recording, theme.colors.error_container),
            RecordingState.TRANSCRIBING: ("Transcribing", theme.colors.transcribing, theme.colors.warning_container),
            RecordingState.ERROR: ("Error", theme.colors.error, theme.colors.error_container),
        }

        message, color, bg_color = status_messages.get(
            state,
            status_messages[RecordingState.IDLE]
        )

        self._status_text.text = message
        self._status_badge.bgcolor = bg_color

        # Update pulse ring visibility
        if state == RecordingState.RECORDING:
            self._pulse_ring.opacity = 0.5
            self._recording_timer.visible = True
            self._start_recording_timer()
        else:
            self._pulse_ring.opacity = 0
            self._recording_timer.visible = False
            self._stop_recording_timer()

        # Update button appearance
        if state == RecordingState.RECORDING:
            self._record_button.bgcolor = theme.colors.recording
            self._record_icon.icon = ft.icons.STOP
            self._record_text.text = "Stop"
        else:
            self._record_button.bgcolor = theme.colors.primary
            self._record_icon.icon = ft.icons.MIC
            self._record_text.text = "Push to Talk"

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

    def refresh_recent_transcriptions(self):
        """Refresh the recent transcriptions cards."""
        if not self._recent_cards_container:
            return

        # Get recent items (up to 3)
        items = self.history_manager.get_all(limit=3, descending=True)

        # Clear existing cards
        self._recent_cards_container.controls.clear()

        # Add new cards
        for item in items:
            card = RecentTranscriptionCard(
                item=item,
                on_click=lambda e, i=item: self._on_recent_card_click(i),
            )
            self._recent_cards_container.controls.append(card)

        # Show empty message if no items
        if not items:
            theme = get_theme_manager()
            self._recent_cards_container.controls.append(
                ft.Text(
                    "No recent transcriptions",
                    size=12,
                    color=theme.colors.on_surface_variant,
                    italic=True,
                )
            )

    def _start_recording_timer(self):
        """Start the recording timer."""
        if self._timer_running:
            return

        self._timer_running = True
        self._recording_start_time = time.time()
        self._update_timer()

    def _stop_recording_timer(self):
        """Stop the recording timer."""
        self._timer_running = False
        if self._recording_timer:
            self._recording_timer.text = "0:00"

    def _update_timer(self):
        """Update the timer display."""
        if not self._timer_running or not self._recording_start_time:
            return

        if self._recording_timer and self._recording_timer.page:
            elapsed = time.time() - self._recording_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self._recording_timer.text = f"{minutes}:{seconds:02d}"
            self._recording_timer.update()

            # Schedule next update
            if self._timer_running:
                self._recording_timer.page.run_thread(
                    self._update_timer,
                    delay=100
                )

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
    def record_button(self) -> Optional[ft.Container]:
        """Get the record button container for event binding."""
        return self._record_button

    @property
    def transcription_display(self) -> Optional[ft.TextField]:
        """Get the transcription display field."""
        return self._transcription_display

    @property
    def audio_level_bar(self) -> Optional[ft.ProgressBar]:
        """Get the audio level bar."""
        return self._audio_level_bar
