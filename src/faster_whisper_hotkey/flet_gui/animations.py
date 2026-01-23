"""
Animations and micro-interactions for the Flet GUI.

This module provides reusable animations and interactive effects for
enhancing the user experience with visual feedback.

Classes
-------
PulseAnimation
    Pulsing glow effect for recording state.
FadeInAnimation
    Fade-in animation for new content.
SlideAnimation
    Slide transition animation.
LoadingIndicator
    Animated loading spinner.
ButtonPressAnimation
    Button press feedback animation.
TransitionType
    Types of slide transitions.
"""

import logging
from enum import Enum
from typing import Optional, Callable

import flet as ft

from .theme import get_theme_manager, ANIMATION_DURATION

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Types of slide/fade transitions."""

    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN_LEFT = "slide_in_left"
    SLIDE_IN_RIGHT = "slide_in_right"
    SLIDE_IN_UP = "slide_in_up"
    SLIDE_IN_DOWN = "slide_in_down"
    SLIDE_OUT_LEFT = "slide_out_left"
    SLIDE_OUT_RIGHT = "slide_out_right"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"


class PulseAnimation(ft.Container):
    """
    A pulsing glow animation for recording state.

    Creates a glowing ring that pulses outward to indicate active
    recording state.

    Parameters
    ----------
    size
        Size of the pulse indicator.
    color
        Color of the pulse. None uses theme recording color.
    speed
        Animation speed in milliseconds.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> pulse = PulseAnimation(size=20)
    >>> pulse.start()
    >>> pulse.stop()
    """

    def __init__(
        self,
        size: float = 16,
        color: Optional[str] = None,
        speed: int = 1000,
        **kwargs,
    ):
        """
        Initialize the PulseAnimation.

        Parameters
        ----------
        size
            Size of the indicator.
        color
            Pulse color.
        speed
            Animation speed in ms.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._size = size
        self._base_color = color or self._theme.colors.recording
        self._speed = speed
        self._is_pulsing = False
        self._pulse_step = 0

        # Core indicator
        self._core = ft.Container(
            width=size,
            height=size,
            border_radius=size / 2,
            bgcolor=self._base_color,
        )

        # Pulse ring
        self._ring = ft.Container(
            width=size,
            height=size,
            border_radius=size / 2,
            border=ft.border.all(2, self._base_color),
            bgcolor=ft.colors.TRANSPARENT,
            opacity=0,
            animate=ft.Animation(
                duration=speed,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        super().__init__(
            content=ft.Stack([self._ring, self._core], width=size, height=size),
            width=size,
            height=size,
            **kwargs,
        )

    def start(self):
        """Start the pulsing animation."""
        self._is_pulsing = True
        self._animate_pulse()

    def stop(self):
        """Stop the pulsing animation."""
        self._is_pulsing = False
        self._ring.opacity = 0
        self._ring.width = self._size
        self._ring.height = self._size
        self._ring.update()

    def _animate_pulse(self):
        """Animate one pulse cycle."""
        if not self._is_pulsing:
            return

        # Expand and fade in
        self._ring.opacity = 0.5
        self._ring.width = self._size * 2
        self._ring.height = self._size * 2
        self._ring.update()

        # Schedule fade out
        def fade_out():
            if not self._is_pulsing:
                return
            self._ring.opacity = 0
            self._ring.update()

            # Schedule next pulse
            if self._is_pulsing and self.page:
                self.page.run_thread(self._animate_pulse, delay=self._speed)

        if self.page:
            self.page.run_thread(fade_out, delay=self._speed // 2)

    def set_color(self, color: str):
        """
        Set the pulse color.

        Parameters
        ----------
        color
            New pulse color.
        """
        self._base_color = color
        self._core.bgcolor = color
        self._ring.border = ft.border.all(2, color)


class FadeInAnimation(ft.Container):
    """
    A container with fade-in animation for content.

    Content fades in smoothly when the container is first displayed.

    Parameters
    ----------
    content
        The content to display.
    duration
        Fade duration in milliseconds.
    delay
        Delay before starting fade in milliseconds.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> fade = FadeInAnimation(ft.Text("Hello"))
    >>> # Content fades in when added to page
    """

    def __init__(
        self,
        content: ft.Control,
        duration: int = 300,
        delay: int = 0,
        **kwargs,
    ):
        """
        Initialize the FadeInAnimation.

        Parameters
        ----------
        content
            The content to display.
        duration
            Fade duration in ms.
        delay
            Delay before fade in ms.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._content = content
        self._duration = duration
        self._delay = delay

        super().__init__(
            content=content,
            opacity=0,
            animate=ft.Animation(
                duration=duration,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            **kwargs,
        )

        # Schedule fade in
        self._schedule_fade_in()

    def _schedule_fade_in(self):
        """Schedule the fade-in animation."""
        def do_fade():
            self.opacity = 1
            if self.page:
                self.update()

        if self.page:
            self.page.run_thread(do_fade, delay=self._delay)

    def reset(self):
        """Reset to invisible state for re-animation."""
        self.opacity = 0
        self.update()
        self._schedule_fade_in()


class SlideAnimation(ft.Container):
    """
    A container with slide transition animation.

    Content slides in from the specified direction when displayed.

    Parameters
    ----------
    content
        The content to display.
    transition
        Type of slide transition.
    duration
        Animation duration in milliseconds.
    offset
        Slide offset in pixels. None uses content size.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> slide = SlideAnimation(ft.Text("Hello"), TransitionType.SLIDE_IN_LEFT)
    >>> # Content slides in from left
    """

    def __init__(
        self,
        content: ft.Control,
        transition: TransitionType = TransitionType.SLIDE_IN_LEFT,
        duration: int = 300,
        offset: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize the SlideAnimation.

        Parameters
        ----------
        content
            The content to display.
        transition
            Type of transition.
        duration
            Animation duration in ms.
        offset
            Slide offset in pixels.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._content = content
        self._transition = transition
        self._duration = duration
        self._offset = offset

        # Determine initial offset
        initial_offset = self._get_initial_offset()

        super().__init__(
            content=content,
            offset=ft.transform.Offset(initial_offset[0], initial_offset[1]),
            opacity=0,
            animate_offset=ft.Animation(
                duration=duration,
                curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            ),
            animate_opacity=ft.Animation(
                duration=duration,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            **kwargs,
        )

        # Schedule slide in
        self._schedule_slide_in()

    def _get_initial_offset(self) -> tuple:
        """Get the initial offset based on transition type."""
        offset = self._offset or 100

        offset_map = {
            TransitionType.SLIDE_IN_LEFT: (-1, 0),  # From left
            TransitionType.SLIDE_IN_RIGHT: (1, 0),  # From right
            TransitionType.SLIDE_IN_UP: (0, -1),  # From top
            TransitionType.SLIDE_IN_DOWN: (0, 1),  # From bottom
            TransitionType.SLIDE_OUT_LEFT: (1, 0),
            TransitionType.SLIDE_OUT_RIGHT: (-1, 0),
            TransitionType.FADE_IN: (0, 0),
            TransitionType.FADE_OUT: (0, 0),
            TransitionType.SCALE_IN: (0, 0),
            TransitionType.SCALE_OUT: (0, 0),
        }

        factor = offset_map.get(self._transition, (0, 0))
        return (factor[0] / offset, factor[1] / offset) if offset else factor

    def _schedule_slide_in(self):
        """Schedule the slide-in animation."""
        def do_slide():
            self.offset = ft.transform.Offset(0, 0)
            self.opacity = 1
            if self.page:
                self.update()

        if self.page:
            self.page.run_thread(do_slide, delay=10)


class LoadingIndicator(ft.Container):
    """
    An animated loading spinner.

    Displays a circular progress indicator with optional label.

    Parameters
    ----------
    size
        Size of the spinner.
    color
        Spinner color. None uses theme primary.
    label
        Optional text label below spinner.
    **kwargs
        Additional Container properties.

    Examples
    --------
    >>> loader = LoadingIndicator(size=32, label="Loading...")
    >>> loader.set_label("Processing...")
    """

    def __init__(
        self,
        size: float = 24,
        color: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the LoadingIndicator.

        Parameters
        ----------
        size
            Size of the spinner.
        color
            Spinner color.
        label
            Optional label text.
        **kwargs
            Additional properties.
        """
        self._theme = get_theme_manager()
        self._size = size
        self._color = color or self._theme.colors.primary

        # Create progress ring
        self._spinner = ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=3,
            stroke_align=ft.StrokeAlign.INSIDE,
            color=self._color,
        )

        # Build content
        if label:
            content = ft.Column(
                [
                    self._spinner,
                    ft.Text(
                        label,
                        size=12,
                        color=self._theme.colors.on_surface_variant,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            )
        else:
            content = self._spinner

        super().__init__(
            content=content,
            **kwargs,
        )

    def set_label(self, label: str):
        """
        Update the label text.

        Parameters
        ----------
        label
            New label text.
        """
        if isinstance(self.content, ft.Column) and len(self.content.controls) > 1:
            self.content.controls[1].text = label
            self.content.controls[1].update()

    def set_color(self, color: str):
        """
        Set the spinner color.

        Parameters
        ----------
        color
            New spinner color.
        """
        self._spinner.color = color
        self._color = color


class ButtonPressAnimation:
    """
    Mixin class for adding press feedback to buttons.

    Provides scale animation on button press for visual feedback.

    Examples
    --------
    >>> class MyButton(ButtonPressAnimation, ft.ElevatedButton):
    ...     pass
    """

    def __init__(self, *args, **kwargs):
        """Initialize with press animation setup."""
        super().__init__(*args, **kwargs)
        self._original_scale = 1.0
        self._setup_press_animation()

    def _setup_press_animation(self):
        """Setup press animation handlers."""
        # This would be connected to button events
        # Implementation depends on Flet's event system
        pass

    def _on_press_down(self):
        """Handle press down - scale down."""
        self.scale = 0.95
        if hasattr(self, 'update'):
            self.update()

    def _on_press_up(self):
        """Handle press up - restore scale."""
        self.scale = self._original_scale
        if hasattr(self, 'update'):
            self.update()


def apply_transition(
    control: ft.Control,
    transition: TransitionType,
    duration: int = 300,
) -> ft.Control:
    """
    Apply a transition animation to a control.

    Parameters
    ----------
    control
        The control to animate.
    transition
        Type of transition to apply.
    duration
        Animation duration in milliseconds.

    Returns
    -------
    ft.Control
        The control with animation applied.

    Examples
    --------
    >>> text = ft.Text("Hello")
    >>> text = apply_transition(text, TransitionType.FADE_IN)
    """
    theme = get_theme_manager()

    control.opacity = 0 if transition in (TransitionType.FADE_IN, TransitionType.SCALE_IN) else 1

    control.animate_opacity = ft.Animation(
        duration=duration,
        curve=ft.AnimationCurve.EASE_OUT,
    )

    if transition in (TransitionType.SLIDE_IN_LEFT, TransitionType.SLIDE_OUT_RIGHT):
        control.offset = ft.transform.Offset(-1, 0)
        control.animate_offset = ft.Animation(
            duration=duration,
            curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        )
    elif transition in (TransitionType.SLIDE_IN_RIGHT, TransitionType.SLIDE_OUT_LEFT):
        control.offset = ft.transform.Offset(1, 0)
        control.animate_offset = ft.Animation(
            duration=duration,
            curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        )

    # Schedule animation trigger
    def do_transition():
        control.opacity = 1
        control.offset = ft.transform.Offset(0, 0)
        if control.page:
            control.update()

    if control.page:
        control.page.run_thread(do_transition, delay=10)

    return control


def create_hover_effect(
    control: ft.Control,
    hover_color: Optional[str] = None,
    scale: float = 1.02,
) -> ft.Control:
    """
    Add hover effect to a control.

    Parameters
    ----------
    control
        The control to add hover effect to.
    hover_color
        Background color on hover.
    scale
        Scale factor on hover.

    Returns
    -------
    ft.Control
        The control with hover effect.

    Examples
    --------
    >>> card = Card(content=ft.Text("Hello"))
    >>> card = create_hover_effect(card, scale=1.05)
    """
    theme = get_theme_manager()

    control.animate = ft.Animation(
        duration=theme.duration.fast,
        curve=ft.AnimationCurve.EASE_OUT,
    )

    # Note: Flet doesn't have direct hover events
    # This is a placeholder for future implementation
    # when Flet adds hover event support

    return control
