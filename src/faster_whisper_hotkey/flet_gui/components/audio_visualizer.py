"""
Audio visualizer component for displaying audio levels.

The AudioVisualizer component provides an animated audio level bar
with peak hold and smoothing for real-time audio feedback.

Classes
-------
AudioVisualizer
    An animated audio level indicator bar.
"""

from typing import Optional

import flet as ft

from ..theme import get_theme_manager, SPACING, BORDER_RADIUS, ANIMATION_DURATION


class AudioVisualizer(ft.Container):
    """
    An animated audio level indicator bar.

    The AudioVisualizer displays current audio level with optional
    peak indicator and smooth transitions.

    Parameters
    ----------
    width
        Width of the visualizer bar.
    height
        Height/thickness of the bar.
    show_peak
        Whether to show peak hold indicator.
    color
        Bar color. None uses theme primary.
    background_color
        Background/trough color. None uses theme outline_variant.
    show_label
        Whether to show level percentage label.
    rounded
        Whether to use rounded corners.
    vertical
        Whether to display vertically (not yet implemented).
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> viz = AudioVisualizer(width=300)
    >>> viz.set_level(0.5)  # 50%
    >>> viz = AudioVisualizer(width=200, show_peak=True)
    """

    def __init__(
        self,
        width: float = 300,
        height: float = 6,
        show_peak: bool = True,
        color: Optional[str] = None,
        background_color: Optional[str] = None,
        show_label: bool = False,
        rounded: bool = True,
        vertical: bool = False,
        **kwargs,
    ):
        """
        Initialize the AudioVisualizer component.

        Parameters
        ----------
        width
            Width of the visualizer.
        height
            Height of the bar.
        show_peak
            Whether to show peak indicator.
        color
            Bar color.
        background_color
            Background color.
        show_label
            Whether to show label.
        rounded
            Whether to round corners.
        vertical
            Whether vertical (not yet implemented).
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._width = width
        self._height = height
        self._show_peak = show_peak
        self._color_override = color
        self._bg_color_override = background_color
        self._show_label = show_label
        self._rounded = rounded

        # Current state
        self._current_level = 0.0
        self._peak_level = 0.0
        self._peak_timer = 0

        # Get colors
        self._bar_color = color or self._theme.colors.primary
        self._bg_color = background_color or self._theme.colors.outline_variant

        # Create background track
        self._track = ft.Container(
            width=width,
            height=height,
            bgcolor=self._bg_color,
            border_radius=(height / 2) if rounded else BORDER_RADIUS.sm,
        )

        # Create level bar
        self._level_bar = ft.Container(
            width=0,
            height=height,
            bgcolor=self._bar_color,
            border_radius=(height / 2) if rounded else BORDER_RADIUS.sm,
            animate=ft.Animation(
                duration=50,  # Fast for smooth audio
                curve=ft.AnimationCurve.LINEAR,
            ),
        )

        # Create peak indicator
        self._peak = ft.Container(
            width=2,
            height=height,
            bgcolor=self._theme.colors.error,
            left=0,
            visible=show_peak,
            animate=ft.Animation(
                duration=100,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        # Create label
        self._label = ft.Text(
            "0%",
            size=10,
            color=self._theme.colors.on_surface_variant,
            visible=show_label,
        )

        # Build the visualizer stack
        if vertical:
            # Vertical layout (not yet fully implemented)
            content = ft.Column([])
        else:
            # Horizontal layout
            if show_label:
                content = ft.Row(
                    [
                        self._label,
                        ft.Stack(
                            [self._track, self._level_bar, self._peak],
                            width=width,
                            height=height,
                        ),
                    ],
                    spacing=SPACING.sm,
                )
            else:
                content = ft.Stack(
                    [self._track, self._level_bar, self._peak],
                    width=width,
                    height=height,
                )

        super().__init__(
            content=content,
            **kwargs,
        )

    def set_level(self, level: float):
        """
        Set the current audio level.

        Parameters
        ----------
        level
            Audio level from 0.0 to 1.0.
        """
        # Clamp level
        level = max(0.0, min(1.0, level))

        self._current_level = level

        # Update level bar width
        self._level_bar.width = self._width * level

        # Update peak
        if level > self._peak_level:
            self._peak_level = level
            self._peak_timer = 30  # Peak hold frames
        elif self._peak_timer > 0:
            self._peak_timer -= 1
        else:
            # Decay peak
            self._peak_level = max(self._peak_level * 0.95, level)

        # Update peak position
        if self._show_peak:
            self._peak.left = self._width * self._peak_level - 1

        # Update label
        if self._show_label:
            self._label.text = f"{int(level * 100)}%"

        # Update color based on level (clip warning)
        if level > 0.9:
            self._level_bar.bgcolor = self._theme.colors.error
        elif level > 0.7:
            self._level_bar.bgcolor = self._theme.colors.warning
        else:
            self._level_bar.bgcolor = self._color_override or self._theme.colors.primary

        self.update()

    def reset(self):
        """Reset the visualizer to zero level."""
        self._current_level = 0.0
        self._peak_level = 0.0
        self._peak_timer = 0
        self._level_bar.width = 0
        if self._show_peak:
            self._peak.left = 0
        if self._show_label:
            self._label.text = "0%"
        self._level_bar.bgcolor = self._color_override or self._theme.colors.primary
        self.update()

    def set_color(self, color: str):
        """
        Set the bar color.

        Parameters
        ----------
        color
            New bar color.
        """
        self._color_override = color
        if self._current_level <= 0.7:
            self._level_bar.bgcolor = color

    @property
    def level(self) -> float:
        """Get the current level."""
        return self._current_level

    @property
    def peak(self) -> float:
        """Get the current peak level."""
        return self._peak_level
