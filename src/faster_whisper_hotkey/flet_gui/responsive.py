"""
Responsive design system for faster-whisper-hotkey Flet GUI.

This module provides a comprehensive responsive design system with:
- Breakpoint-based layout adjustments
- Compact mode for small screens
- Dynamic sizing and spacing based on window size
- Window resize handling
- Fullscreen mode support

Classes
-------
Breakpoint
    Enum for responsive breakpoints.
ResponsiveManager
    Manages responsive state and notifies listeners.
SizeMode
    Enum for size modes (compact, normal, spacious).
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Dict, Any, Tuple

import flet as ft

from .theme import get_theme_manager, SPACING

logger = logging.getLogger(__name__)


class Breakpoint(Enum):
    """
    Responsive breakpoints based on window width.

    Attributes
    ----------
    XS
        Extra small (320px+).
    SM
        Small (480px+).
    MD
        Medium (768px+).
    LG
        Large (1024px+).
    XL
        Extra large (1280px+).
    XXL
        Extra extra large (1536px+).
    """

    XS = 320
    SM = 480
    MD = 768
    LG = 1024
    XL = 1280
    XXL = 1536

    @classmethod
    def from_width(cls, width: int) -> "Breakpoint":
        """
        Get the breakpoint for a given window width.

        Parameters
        ----------
        width
            Window width in pixels.

        Returns
        -------
        Breakpoint
            The appropriate breakpoint.
        """
        if width >= cls.XXL.value:
            return cls.XXL
        elif width >= cls.XL.value:
            return cls.XL
        elif width >= cls.LG.value:
            return cls.LG
        elif width >= cls.MD.value:
            return cls.MD
        elif width >= cls.SM.value:
            return cls.SM
        else:
            return cls.XS


class SizeMode(Enum):
    """
    Size mode for UI scaling.

    Attributes
    ----------
    COMPACT
        Compact mode for small screens (85% size).
    NORMAL
        Normal mode (100% size).
    SPACIOUS
        Spacious mode for large screens (110% size).
    """

    COMPACT = "compact"
    NORMAL = "normal"
    SPACIOUS = "spacious"

    @classmethod
    def from_breakpoint(cls, bp: Breakpoint) -> "SizeMode":
        """
        Get the size mode for a given breakpoint.

        Parameters
        ----------
        bp
            The breakpoint.

        Returns
        -------
        SizeMode
            The appropriate size mode.
        """
        if bp in (Breakpoint.XS, Breakpoint.SM):
            return cls.COMPACT
        elif bp in (Breakpoint.XL, Breakpoint.XXL):
            return cls.SPACIOUS
        else:
            return cls.NORMAL

    def get_scale(self) -> float:
        """
        Get the scaling factor for this size mode.

        Returns
        -------
        float
            Scaling factor (0.85 to 1.1).
        """
        scales = {
            SizeMode.COMPACT: 0.85,
            SizeMode.NORMAL: 1.0,
            SizeMode.SPACIOUS: 1.1,
        }
        return scales.get(self, 1.0)


@dataclass
class ResponsiveState:
    """
    Current responsive state.

    Attributes
    ----------
    window_width
        Current window width in pixels.
    window_height
        Current window height in pixels.
    breakpoint
        Current breakpoint.
    size_mode
        Current size mode.
    is_compact
        Whether compact mode is active.
    is_fullscreen
        Whether fullscreen mode is active.
    """

    window_width: int = 1024
    window_height: int = 768
    breakpoint: Breakpoint = Breakpoint.LG
    size_mode: SizeMode = SizeMode.NORMAL
    is_compact: bool = False
    is_fullscreen: bool = False


class ResponsiveManager:
    """
    Manages responsive design state and notifications.

    This class handles:
    - Tracking window size changes
    - Determining current breakpoint and size mode
    - Notifying listeners of responsive changes
    - Providing responsive utility methods

    Attributes
    ----------
    state
        Current responsive state.
    _listeners
        Callbacks for responsive state changes.
    """

    # Minimum supported resolution
    MIN_WIDTH = 360
    MIN_HEIGHT = 500

    # Recommended minimum resolution
    RECOMMENDED_MIN_WIDTH = 400
    RECOMMENDED_MIN_HEIGHT = 600

    def __init__(self):
        """Initialize the responsive manager."""
        self.state = ResponsiveState()
        self._listeners: list = []
        self._page: Optional[ft.Page] = None
        self._manual_compact_override: Optional[bool] = None
        self._manual_scale_override: Optional[float] = None

    def attach_to_page(self, page: ft.Page):
        """
        Attach the responsive manager to a Flet page.

        Sets up window resize listeners.

        Parameters
        ----------
        page
            The Flet page to attach to.
        """
        self._page = page

        # Initial state from page
        if page.window_width and page.window_height:
            self._update_from_page()

        # Set up resize handler
        def on_resize(e):
            self._update_from_page()
            self._notify_listeners()

        page.on_resize = on_resize

    def _update_from_page(self):
        """Update state from current page dimensions."""
        if not self._page:
            return

        self.state.window_width = self._page.window_width or 1024
        self.state.window_height = self._page.window_height or 768

        # Update breakpoint
        self.state.breakpoint = Breakpoint.from_width(self.state.window_width)

        # Update size mode (unless manual override)
        if self._manual_compact_override is not None:
            self.state.is_compact = self._manual_compact_override
            self.state.size_mode = SizeMode.COMPACT if self._manual_compact_override else SizeMode.NORMAL
        else:
            self.state.size_mode = SizeMode.from_breakpoint(self.state.breakpoint)
            self.state.is_compact = self.state.size_mode == SizeMode.COMPACT

        # Check fullscreen
        self.state.is_fullscreen = self._page.fullscreen if hasattr(self._page, 'fullscreen') else False

    def subscribe(self, callback: Callable[[ResponsiveState], None]) -> Callable:
        """
        Subscribe to responsive state changes.

        Parameters
        ----------
        callback
            Function to call when state changes.

        Returns
        -------
        Callable
            Unsubscribe function.
        """
        self._listeners.append(callback)

        def unsubscribe():
            if callback in self._listeners:
                self._listeners.remove(callback)

        return unsubscribe

    def _notify_listeners(self):
        """Notify all listeners of state changes."""
        for callback in self._listeners:
            try:
                callback(self.state)
            except Exception as e:
                logger.warning(f"Responsive change callback error: {e}")

    def set_compact_mode(self, compact: bool, manual: bool = True):
        """
        Set compact mode.

        Parameters
        ----------
        compact
            Whether to enable compact mode.
        manual
            Whether this is a manual override (True) or automatic (False).
            Manual overrides persist across window resizes.
        """
        if manual:
            self._manual_compact_override = compact

        self.state.is_compact = compact
        self.state.size_mode = SizeMode.COMPACT if compact else SizeMode.NORMAL
        self._notify_listeners()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if not self._page:
            return

        self.state.is_fullscreen = not self.state.is_fullscreen
        self._page.fullscreen = self.state.is_fullscreen
        self._page.update()

    def get_scale(self) -> float:
        """
        Get the current scaling factor.

        Returns
        -------
        float
            Scaling factor based on size mode.
        """
        if self._manual_scale_override is not None:
            return self._manual_scale_override
        return self.state.size_mode.get_scale()

    def set_scale(self, scale: float):
        """
        Set a manual scaling override.

        Parameters
        ----------
        scale
            Scaling factor (e.g., 0.85 for compact, 1.0 for normal).
        """
        self._manual_scale_override = scale

    def reset_scale(self):
        """Reset manual scaling override to automatic."""
        self._manual_scale_override = None

    # Responsive utility methods
    def get_width(self, base_width: float) -> float:
        """
        Get a responsive width based on current scale.

        Parameters
        ----------
        base_width
            Base width in pixels.

        Returns
        -------
        float
            Scaled width.
        """
        return base_width * self.get_scale()

    def get_height(self, base_height: float) -> float:
        """
        Get a responsive height based on current scale.

        Parameters
        ----------
        base_height
            Base height in pixels.

        Returns
        -------
        float
            Scaled height.
        """
        return base_height * self.get_scale()

    def get_spacing(self, base_spacing: float) -> float:
        """
        Get responsive spacing based on current scale.

        Parameters
        ----------
        base_spacing
            Base spacing in pixels.

        Returns
        -------
        float
            Scaled spacing.
        """
        return base_spacing * self.get_scale()

    def get_font_size(self, base_size: float) -> float:
        """
        Get responsive font size based on current scale.

        Parameters
        ----------
        base_size
            Base font size in pixels.

        Returns
        -------
        float
            Scaled font size.
        """
        return base_size * self.get_scale()

    def should_show_element(self, min_breakpoint: Breakpoint) -> bool:
        """
        Determine if an element should be shown based on breakpoint.

        Parameters
        ----------
        min_breakpoint
            Minimum breakpoint required for visibility.

        Returns
        -------
        bool
            True if the element should be visible.
        """
        return self.state.window_width >= min_breakpoint.value

    def is_small_screen(self) -> bool:
        """
        Check if current screen is small (below MD breakpoint).

        Returns
        -------
        bool
            True if screen is small.
        """
        return self.state.window_width < Breakpoint.MD.value

    def is_medium_screen(self) -> bool:
        """
        Check if current screen is medium (MD to LG breakpoint).

        Returns
        -------
        bool
            True if screen is medium.
        """
        return Breakpoint.MD.value <= self.state.window_width < Breakpoint.XL.value

    def is_large_screen(self) -> bool:
        """
        Check if current screen is large (XL breakpoint and above).

        Returns
        -------
        bool
            True if screen is large.
        """
        return self.state.window_width >= Breakpoint.XL.value

    def get_content_padding(self) -> float:
        """
        Get responsive content padding.

        Returns
        -------
        float
            Padding value in pixels.
        """
        if self.state.is_compact:
            return SPACING.sm
        return SPACING.md

    def get_card_padding(self) -> float:
        """
        Get responsive card padding.

        Returns
        -------
        float
            Padding value in pixels.
        """
        if self.state.is_compact:
            return SPACING.sm
        return SPACING.md

    def get_button_height(self) -> float:
        """
        Get responsive button height.

        Returns
        -------
        float
            Button height in pixels.
        """
        if self.state.is_compact:
            return 36
        return 40

    def get_input_height(self) -> float:
        """
        Get responsive input field height.

        Returns
        -------
        float
            Input height in pixels.
        """
        if self.state.is_compact:
            return 36
        return 40

    def get_icon_size(self, base_size: int = 24) -> int:
        """
        Get responsive icon size.

        Parameters
        ----------
        base_size
            Base icon size.

        Returns
        -------
        int
            Scaled icon size.
        """
        scaled = base_size * self.get_scale()
        return max(16, int(scaled))

    def adjust_for_width(self, narrow: Any, medium: Any, wide: Any) -> Any:
        """
        Return a value based on current width category.

        Parameters
        ----------
        narrow
            Value for small screens.
        medium
            Value for medium screens.
        wide
            Value for large screens.

        Returns
        -------
        Any
            The appropriate value for current screen size.
        """
        if self.is_small_screen():
            return narrow
        elif self.is_medium_screen():
            return medium
        else:
            return wide

    def get_visible_recent_count(self) -> int:
        """
        Get number of recent transcriptions to show based on screen size.

        Returns
        -------
        int
            Number of recent items to display.
        """
        if self.is_small_screen():
            return 2
        elif self.is_medium_screen():
            return 3
        else:
            return 3

    def get_transcription_max_lines(self) -> int:
        """
        Get max lines for transcription display based on screen height.

        Returns
        -------
        int
            Maximum lines to display.
        """
        if self.state.window_height < 600:
            return 4
        elif self.state.window_height < 800:
            return 6
        else:
            return 10

    def supports_two_column_layout(self) -> bool:
        """
        Check if screen supports two-column layout.

        Returns
        -------
        bool
            True if two-column layout is suitable.
        """
        return not self.is_small_screen()

    def get_sidebar_width(self) -> float:
        """
        Get appropriate sidebar width.

        Returns
        -------
        float
            Sidebar width in pixels.
        """
        if self.is_small_screen():
            return 160
        return 180

    def supports_fullscreen(self) -> bool:
        """
        Check if platform supports fullscreen mode.

        Returns
        -------
        bool
            True if fullscreen is supported.
        """
        # Flet supports fullscreen on most platforms
        return True


# Global responsive manager instance
_responsive_manager: Optional[ResponsiveManager] = None


def get_responsive_manager() -> ResponsiveManager:
    """
    Get the global responsive manager instance.

    Returns
    -------
    ResponsiveManager
        The global responsive manager.
    """
    global _responsive_manager
    if _responsive_manager is None:
        _responsive_manager = ResponsiveManager()
    return _responsive_manager


def is_compact_mode() -> bool:
    """
    Check if compact mode is currently active.

    Returns
    -------
    bool
        True if compact mode is active.
    """
    return get_responsive_manager().state.is_compact


def get_current_breakpoint() -> Breakpoint:
    """
    Get the current breakpoint.

    Returns
    -------
    Breakpoint
        The current breakpoint.
    """
    return get_responsive_manager().state.breakpoint


def get_responsive_scale() -> float:
    """
    Get the current responsive scaling factor.

    Returns
    -------
    float
        The current scaling factor.
    """
    return get_responsive_manager().get_scale()


# Responsive decorator for UI builders
def responsive_width(base_width: float) -> float:
    """
    Get responsive width for a base width.

    Parameters
    ----------
    base_width
        Base width in pixels.

    Returns
    -------
    float
        Scaled width.
    """
    return get_responsive_manager().get_width(base_width)


def responsive_spacing(base_spacing: float) -> float:
    """
    Get responsive spacing for a base spacing.

    Parameters
    ----------
    base_spacing
        Base spacing in pixels.

    Returns
    -------
    float
        Scaled spacing.
    """
    return get_responsive_manager().get_spacing(base_spacing)
