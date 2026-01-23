"""
Modern transcription panel view for the Flet GUI.

This module provides a redesigned, modern transcription interface with:
- Large, centered transcription result display
- Floating action button for push-to-talk
- Recent transcriptions as quick-access cards
- Recording time elapsed counter
- Keyboard shortcut hints
- Enhanced visual feedback for recording state
- Responsive design for different screen sizes
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
from ..responsive import ResponsiveManager, ResponsiveState, Breakpoint, SizeMode

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
    compact
        Whether to use compact layout.
    **kwargs
        Additional Card properties.
    """

    def __init__(
        self,
        item: HistoryItem,
        on_click: Optional[Callable] = None,
        max_length: int = 80,
        compact: bool = False,
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
        compact
            Whether to use compact layout.
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
        # Adjust max length for compact mode
        effective_max_length = max_length // 2 if compact else max_length
        if len(text) > effective_max_length:
            text = text[:effective_max_length] + "..."

        # Adjust sizes for compact mode
        icon_size = 12 if compact else 14
        time_size = 10 if compact else 11
        text_size = 12 if compact else 13
        max_lines = 2 if compact else 3
        padding = SPACING.xs if compact else SPACING.sm

        # Build content
        content = ft.Column(
            [
                # Header with time
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.HISTORY,
                            size=icon_size,
                            color=theme.colors.on_surface_variant,
                        ),
                        ft.Text(
                            time_str,
                            size=time_size,
                            color=theme.colors.on_surface_variant,
                        ),
                        ft.Container(expand=True),
                    ],
                    spacing=4 if not compact else 2,
                ),
                # Text content
                ft.Text(
                    text,
                    size=text_size,
                    color=theme.colors.on_surface,
                    max_lines=max_lines,
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
            padding=padding,
            on_click=on_click,
            **kwargs,
        )

        self._item = item
        self._compact = compact

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
    Modern transcription panel with enhanced UI and responsive design.

    This panel provides:
    - Large, prominent "Push to Talk" button with visual feedback
    - Live audio level indicator (visualizer bar)
    - Status text showing current state (Ready, Recording, Transcribing, Error)
    - Real-time transcription result display area
    - Recording timer showing elapsed time
    - Recent transcriptions as quick-access cards
    - Keyboard shortcut hints
    - Copy to clipboard and paste buttons
    - Responsive layout that adapts to window size

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
        responsive_manager: Optional[ResponsiveManager] = None,
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
        responsive_manager
            Optional responsive manager for adaptive layouts.
        """
        self.app_state = app_state
        self.history_manager = history_manager
        self._on_copy = on_copy
        self._on_paste = on_paste
        self._on_recent_click = on_recent_click

        # Responsive manager
        self._responsive_manager = responsive_manager
        self._is_compact = False
        self._current_width = 400

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

        # Unsubscribe function for responsive changes
        self._responsive_unsubscribe: Optional[Callable] = None

    def set_responsive_manager(self, manager: ResponsiveManager):
        """
        Set the responsive manager and subscribe to changes.

        Parameters
        ----------
        manager
            The responsive manager instance.
        """
        self._responsive_manager = manager
        self._is_compact = manager.state.is_compact
        self._current_width = manager.state.window_width

        # Subscribe to responsive changes
        def on_responsive_change(state: ResponsiveState):
            old_compact = self._is_compact
            old_width = self._current_width
            self._is_compact = state.is_compact
            self._current_width = state.window_width

            # Rebuild if compact mode changed or width changed significantly
            if old_compact != self._is_compact or abs(old_width - state.window_width) > 100:
                self._refresh_layout()

        self._responsive_unsubscribe = manager.subscribe(on_responsive_change)

    def _refresh_layout(self):
        """Refresh the layout based on current responsive state."""
        # Update transcription display width
        if self._transcription_display:
            self._transcription_display.width = self._get_content_width()

        # Update status row width
        if self._status_badge and self._status_badge.parent:
            # Find the status row and update its width
            pass

        # Update recent cards
        self.refresh_recent_transcriptions()

    def _get_content_width(self) -> int:
        """Get the responsive content width."""
        if not self._responsive_manager:
            return 400

        if self._is_compact:
            # For compact/small screens, use percentage-based width
            base = int(self._current_width * 0.9)
            return max(280, min(base, 350))
        return 400

    def _get_spacing(self) -> float:
        """Get responsive spacing."""
        if self._is_compact:
            return SPACING.sm
        return SPACING.md

    def _get_padding(self) -> float:
        """Get responsive padding."""
        if self._is_compact:
            return SPACING.md
        return SPACING.lg

    def _get_visible_recent_count(self) -> int:
        """Get number of recent items to show based on screen size."""
        if not self._responsive_manager:
            return 3
        return self._responsive_manager.get_visible_recent_count()

    def build(self) -> ft.Container:
        """
        Build the modern transcription panel UI.

        Returns
        -------
        ft.Container
            The transcription panel container.
        """
        theme = get_theme_manager()

        # Get responsive spacing and padding
        spacing = self._get_spacing()
        padding = self._get_padding()

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
            spacing=spacing,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=main_content,
            padding=ft.padding.symmetric(horizontal=padding, vertical=SPACING.md),
            expand=True,
        )

    def _build_status_row(self) -> ft.Row:
        """Build the status row with badge and timer."""
        theme = get_theme_manager()

        # Responsive sizes
        status_size = 12 if self._is_compact else 13
        timer_size = 12 if self._is_compact else 13
        indicator_size = 6 if self._is_compact else 8
        badge_padding_h = 10 if self._is_compact else 12
        badge_padding_v = 4 if self._is_compact else 6
        row_width = self._get_content_width()

        # Status badge
        self._status_text = ft.Text(
            "Ready",
            size=status_size,
            weight=ft.FontWeight.MEDIUM,
            color=theme.colors.on_surface,
        )
        self._status_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=indicator_size,
                        height=indicator_size,
                        border_radius=indicator_size // 2,
                        bgcolor=theme.colors.success,
                    ),
                    self._status_text,
                ],
                spacing=6 if not self._is_compact else 4,
            ),
            padding=ft.padding.symmetric(horizontal=badge_padding_h, vertical=badge_padding_v),
            bgcolor=theme.colors.success_container,
            border_radius=16,
        )

        # Recording timer (hidden initially)
        self._recording_timer = ft.Text(
            "0:00",
            size=timer_size,
            color=theme.colors.on_surface_variant,
            visible=False,
            width=50 if self._is_compact else 60,
            text_align=ft.TextAlign.RIGHT,
        )

        return ft.Row(
            [
                self._status_badge,
                ft.Container(expand=True),
                self._recording_timer,
            ],
            width=row_width,
        )

    def _build_record_button_area(self) -> ft.Container:
        """Build the floating record button with pulse effect."""
        theme = get_theme_manager()

        # Responsive button sizes
        btn_size = 70 if self._is_compact else 80
        ring_size = 78 if self._is_compact else 90
        icon_size = 28 if self._is_compact else 32
        text_size = 12 if self._is_compact else 14
        bar_width = 180 if self._is_compact else 200

        # Pulse ring for recording state
        self._pulse_ring = ft.Container(
            width=ring_size,
            height=ring_size,
            border_radius=ring_size // 2,
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
            size=icon_size,
            color=theme.colors.on_primary,
        )
        self._record_text = ft.Text(
            "Push to Talk" if not self._is_compact else "Talk",
            size=text_size,
            weight=ft.FontWeight.MEDIUM,
            color=theme.colors.on_primary,
        )
        button_content = ft.Column(
            [
                self._record_icon,
                self._record_text,
            ],
            spacing=4 if not self._is_compact else 2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Record button (stacked with pulse ring)
        self._record_button = ft.Container(
            content=ft.Stack(
                [
                    self._pulse_ring,
                    ft.Container(
                        content=button_content,
                        width=btn_size,
                        height=btn_size,
                        border_radius=btn_size // 2,
                        bgcolor=theme.colors.primary,
                        alignment=ft.alignment.center,
                    ),
                ],
                width=ring_size,
                height=ring_size,
                alignment=ft.alignment.center,
            ),
            width=ring_size,
            height=ring_size,
            bgcolor=theme.colors.primary,
            border_radius=ring_size // 2,
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
            width=bar_width,
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
                        padding=ft.padding.only(top=SPACING.sm if not self._is_compact else SPACING.xs),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=SPACING.xs if self._is_compact else SPACING.sm),
        )

    def _build_transcription_display(self) -> ft.Container:
        """Build the transcription display area."""
        theme = get_theme_manager()

        # Responsive dimensions
        content_width = self._get_content_width()
        font_size = 13 if self._is_compact else 14
        padding = SPACING.sm if self._is_compact else SPACING.md

        # Get max lines from responsive manager or use default
        if self._responsive_manager:
            max_lines = self._responsive_manager.get_transcription_max_lines()
            min_lines = max(3, max_lines - 3)
        else:
            min_lines = 6
            max_lines = 10

        self._transcription_display = ft.TextField(
            value="",
            multiline=True,
            min_lines=min_lines,
            max_lines=max_lines,
            read_only=True,
            hint_text="Your transcription will appear here...",
            border_color=theme.colors.outline_variant,
            border_radius=theme.radius.lg,
            bgcolor=theme.colors.surface_container_low,
            text_style=ft.TextStyle(
                size=font_size,
                color=theme.colors.on_surface,
            ),
            content_padding=ft.padding.all(padding),
            width=content_width,
        )

        return ft.Container(
            content=self._transcription_display,
            width=content_width,
        )

    def _build_action_buttons(self) -> ft.Row:
        """Build the action buttons row."""
        theme = get_theme_manager()

        icon_size = 18 if self._is_compact else 20

        copy_button = ft.IconButton(
            icon=ft.icons.COPY,
            icon_size=icon_size,
            tooltip="Copy to clipboard",
            on_click=self._on_copy_click,
            style=ft.ButtonStyle(
                bgcolor=theme.colors.surface_container_low,
                icon_color=theme.colors.on_surface,
            ),
        )

        paste_button = ft.IconButton(
            icon=ft.icons.CONTENT_PASTE,
            icon_size=icon_size,
            tooltip="Paste to active window",
            on_click=self._on_paste_click,
            style=ft.ButtonStyle(
                bgcolor=theme.colors.surface_container_low,
                icon_color=theme.colors.on_surface,
            ),
        )

        return ft.Row(
            [copy_button, paste_button],
            spacing=SPACING.xs if self._is_compact else SPACING.sm,
        )

    def _build_recent_transcriptions(self) -> ft.Container:
        """Build the recent transcriptions section."""
        theme = get_theme_manager()

        content_width = self._get_content_width()
        header_size = 12 if self._is_compact else 13

        # Section header
        header = ft.Row(
            [
                ft.Text(
                    "Recent",
                    size=header_size,
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
            width=content_width,
            padding=ft.padding.only(top=SPACING.xs if self._is_compact else SPACING.sm),
        )

    def _build_shortcut_hints(self) -> ft.Container:
        """Build the keyboard shortcut hints row."""
        theme = get_theme_manager()

        # In compact mode, only show the main hotkey
        hints = [
            ShortcutHint(
                self.app_state.hotkey.upper(),
                icon=ft.icons.KEYBOARD,
            ),
        ]

        # Add history hotkey hint only in non-compact mode
        if hasattr(self.app_state, 'history_hotkey') and not self._is_compact:
            hints.append(
                ShortcutHint(
                    self.app_state.history_hotkey.upper(),
                    icon=ft.icons.HISTORY,
                )
            )

        self._shortcut_hints = ft.Row(
            hints,
            spacing=SPACING.xs if self._is_compact else SPACING.sm,
        )

        return ft.Container(
            content=self._shortcut_hints,
            padding=ft.padding.only(top=SPACING.xs if self._is_compact else SPACING.sm),
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

        # Get responsive item count
        limit = self._get_visible_recent_count()

        # Get recent items
        items = self.history_manager.get_all(limit=limit, descending=True)

        # Clear existing cards
        self._recent_cards_container.controls.clear()

        # Add new cards with compact mode flag
        for item in items:
            card = RecentTranscriptionCard(
                item=item,
                on_click=lambda e, i=item: self._on_recent_card_click(i),
                compact=self._is_compact,
            )
            self._recent_cards_container.controls.append(card)

        # Show empty message if no items
        if not items:
            theme = get_theme_manager()
            font_size = 11 if self._is_compact else 12
            self._recent_cards_container.controls.append(
                ft.Text(
                    "No recent transcriptions" if not self._is_compact else "No recent",
                    size=font_size,
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
