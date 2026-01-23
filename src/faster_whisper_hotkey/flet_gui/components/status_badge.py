"""
Status badge component for displaying status indicators.

The StatusBadge component provides a compact status indicator with
color-coded states and optional text labels.

Classes
-------
StatusBadge
    A compact status indicator with color and label.
StatusType
    Predefined status types with associated colors.
"""

from enum import Enum
from typing import Optional

import flet as ft

from ..theme import get_theme_manager, SPACING, BORDER_RADIUS


class StatusType(Enum):
    """Predefined status types with colors."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    IDLE = "idle"
    DISABLED = "disabled"


class StatusBadge(ft.Container):
    """
    A compact status indicator with color and optional label.

    The StatusBadge displays a colored dot with optional text to
    indicate status (recording, transcribing, success, error, etc.).

    Parameters
    ----------
    status_type
        The status type determining color.
    label
        Optional text label.
    size
        Size of the status indicator dot.
    show_label
        Whether to show the text label.
    animate
        Whether to animate color changes.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> badge = StatusBadge(StatusType.RECORDING, label="Recording")
    >>> badge = StatusBadge(StatusType.SUCCESS, label="Saved")
    >>> badge = StatusBadge(StatusType.ERROR)
    """

    # Color mapping for status types
    STATUS_COLORS = {
        StatusType.SUCCESS: "success",
        StatusType.WARNING: "warning",
        StatusType.ERROR: "error",
        StatusType.INFO: "info",
        StatusType.RECORDING: "recording",
        StatusType.TRANSCRIBING: "transcribing",
        StatusType.IDLE: "primary",
        StatusType.DISABLED: "on_surface_variant",
    }

    def __init__(
        self,
        status_type: StatusType = StatusType.IDLE,
        label: Optional[str] = None,
        size: float = 8,
        show_label: bool = True,
        animate: bool = True,
        **kwargs,
    ):
        """
        Initialize the StatusBadge component.

        Parameters
        ----------
        status_type
            The status type.
        label
            Optional text label.
        size
            Size of the indicator dot.
        show_label
            Whether to show the label.
        animate
            Whether to animate changes.
        **kwargs
            Additional Container properties.
        """
        self._theme = get_theme_manager()
        self._status_type = status_type
        self._size = size
        self._show_label = show_label
        self._base_label = label

        # Get color for status type
        color = self._get_color_for_type(status_type)

        # Create indicator dot
        self._indicator = ft.Container(
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=color,
        )

        # Create label text
        self._label_text = ft.Text(
            label or status_type.value.capitalize(),
            size=12,
            color=color,
            weight=ft.FontWeight.MEDIUM,
            visible=show_label and label is not None,
        )

        # Build content row
        content = ft.Row(
            [self._indicator, self._label_text],
            spacing=SPACING.sm if show_label else 0,
            alignment=ft.MainAxisAlignment.START,
        )

        # Setup animation
        animation = None
        if animate:
            animation = ft.Animation(
                duration=self._theme.duration.fast,
                curve=ft.AnimationCurve.EASE_OUT,
            )

        super().__init__(
            content=content,
            animate=animation,
            **kwargs,
        )

    def _get_color_for_type(self, status_type: StatusType) -> str:
        """Get the color for a status type."""
        color_attr = self.STATUS_COLORS.get(status_type, "primary")
        return getattr(self._theme.colors, color_attr, self._theme.colors.primary)

    def set_status(self, status_type: StatusType, label: Optional[str] = None):
        """
        Update the status type and optional label.

        Parameters
        ----------
        status_type
            New status type.
        label
            New label text. None keeps current label or uses status type name.
        """
        self._status_type = status_type

        # Update indicator color
        self._indicator.bgcolor = self._get_color_for_type(status_type)

        # Update label
        if label is not None:
            self._base_label = label

        self._label_text.text = self._base_label or status_type.value.capitalize()
        self._label_text.color = self._get_color_for_type(status_type)
        self._label_text.visible = self._show_label

        self.update()

    def set_label(self, label: str):
        """
        Update the label text.

        Parameters
        ----------
        label
            New label text.
        """
        self._base_label = label
        self._label_text.text = label
        self._label_text.visible = self._show_label
        self._label_text.update()

    def set_pulse(self, pulsing: bool):
        """
        Enable or disable pulsing animation for the indicator.

        Parameters
        ----------
        pulsing
            Whether to pulse the indicator.
        """
        if pulsing:
            self._indicator.animate=ft.Animation(
                duration=500,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            )
            # Note: True pulsing animation requires periodic updates
            # This sets up the animation property
        else:
            self._indicator.animate = None
        self._indicator.update()

    @property
    def status_type(self) -> StatusType:
        """Get the current status type."""
        return self._status_type

    @property
    def indicator(self) -> ft.Container:
        """Get the indicator dot."""
        return self._indicator

    @property
    def label(self) -> ft.Text:
        """Get the label text control."""
        return self._label_text
