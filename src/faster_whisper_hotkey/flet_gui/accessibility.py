"""
Accessibility features for faster-whisper-hotkey Flet GUI.

This module provides comprehensive accessibility support including:
- High contrast mode for better visibility
- Font size scaling for improved readability
- Keyboard navigation support with focus indicators
- Screen reader announcements for state changes
- WCAG AA/AAA compliant color contrast

Classes
-------
AccessibilityManager
    Manages accessibility settings and features.

FontSize
    Font size scaling options.

ContrastMode
    Contrast mode options.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List

import flet as ft

from .theme import get_theme_manager, ColorPalette

logger = logging.getLogger(__name__)


class FontSize(Enum):
    """Font size scaling options."""
    SMALL = 0.85  # 12px base
    NORMAL = 1.0  # 14px base
    LARGE = 1.15  # 16px base
    EXTRA_LARGE = 1.3  # 18px base


class ContrastMode(Enum):
    """Contrast mode options."""
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    EXTRA_HIGH_CONTRAST = "extra_high_contrast"


@dataclass
class FocusStyle:
    """
    Focus indicator style for keyboard navigation.

    Attributes
    ----------
    width
        Border width in pixels.
    color
        Focus border color.
    dash_pattern
        Optional dash pattern for dotted line.
    """
    width: float = 3.0
    color: str = "#2196F3"
    dash_pattern: Optional[List[float]] = None

    def to_border(self) -> ft.BorderSide:
        """Convert to Flet BorderSide."""
        return ft.BorderSide(
            width=self.width,
            color=self.color,
        )


@dataclass
class AccessibilitySettings:
    """
    Accessibility settings for the application.

    Attributes
    ----------
    font_size_scale
        Font size scaling multiplier.
    contrast_mode
        Current contrast mode.
    enable_high_contrast
        Whether high contrast mode is enabled.
    enable_screen_reader
        Whether screen reader announcements are enabled.
    enable_focus_indicators
        Whether focus indicators are shown.
    reduce_motion
        Whether to reduce animations.
    extended_timeout
        Whether to extend timeouts for slower interactions.
    """
    font_size_scale: float = 1.0
    contrast_mode: ContrastMode = ContrastMode.NORMAL
    enable_high_contrast: bool = False
    enable_screen_reader: bool = True
    enable_focus_indicators: bool = True
    reduce_motion: bool = False
    extended_timeout: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "font_size_scale": self.font_size_scale,
            "contrast_mode": self.contrast_mode.value,
            "enable_high_contrast": self.enable_high_contrast,
            "enable_screen_reader": self.enable_screen_reader,
            "enable_focus_indicators": self.enable_focus_indicators,
            "reduce_motion": self.reduce_motion,
            "extended_timeout": self.extended_timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccessibilitySettings":
        """Create from dictionary."""
        contrast_mode = data.get("contrast_mode", "normal")
        try:
            contrast_mode = ContrastMode(contrast_mode)
        except ValueError:
            contrast_mode = ContrastMode.NORMAL

        return cls(
            font_size_scale=data.get("font_size_scale", 1.0),
            contrast_mode=contrast_mode,
            enable_high_contrast=data.get("enable_high_contrast", False),
            enable_screen_reader=data.get("enable_screen_reader", True),
            enable_focus_indicators=data.get("enable_focus_indicators", True),
            reduce_motion=data.get("reduce_motion", False),
            extended_timeout=data.get("extended_timeout", False),
        )


# High contrast color palettes (WCAG AAA compliant)
# These provide at least 7:1 contrast ratio for normal text
HIGH_CONTRAST_PALETTE = ColorPalette(
    # Use pure black/white for maximum contrast
    primary="#0000FF",  # Pure blue on white = 7.0:1
    primary_container="#FFFFFF",
    on_primary="#FFFFFF",
    secondary="#000000",
    secondary_container="#FFFFFF",
    on_secondary="#FFFFFF",
    background="#FFFFFF",
    surface="#FFFFFF",
    surface_variant="#F0F0F0",
    surface_container="#E8E8E8",
    surface_container_low="#FAFAFA",
    surface_container_lowest="#FFFFFF",
    on_background="#000000",  # Pure black
    on_surface="#000000",
    on_surface_variant="#1A1A1A",
    outline="#000000",
    outline_variant="#404040",
    error="#CC0000",  # Darker red for better contrast
    error_container="#FFCCCC",
    on_error="#FFFFFF",
    success="#006600",  # Darker green
    success_container="#CCFFCC",
    on_success="#FFFFFF",
    warning="#B26B00",  # Darker orange/brown
    warning_container="#FFE6CC",
    on_warning="#FFFFFF",
    info="#0055AA",  # Darker blue
    info_container="#CCE5FF",
    on_info="#FFFFFF",
    recording="#CC0000",
    transcribing="#B26B00",
)

# Extra high contrast palette (black on white, white on black)
EXTRA_HIGH_CONTRAST_PALETTE = ColorPalette(
    primary="#FFFFFF",
    primary_container="#000000",
    on_primary="#000000",
    secondary="#FFFFFF",
    secondary_container="#000000",
    on_secondary="#000000",
    background="#000000",
    surface="#000000",
    surface_variant="#1A1A1A",
    surface_container="#0D0D0D",
    surface_container_low="#050505",
    surface_container_lowest="#000000",
    on_background="#FFFFFF",  # Pure white
    on_surface="#FFFFFF",
    on_surface_variant="#E5E5E5",
    outline="#FFFFFF",
    outline_variant="#B3B3B3",
    error="#FF0000",  # Bright red
    error_container="#000000",
    on_error="#FFFFFF",
    success="#00FF00",  # Bright green
    success_container="#000000",
    on_success="#000000",
    warning="#FFFF00",  # Bright yellow
    warning_container="#000000",
    on_warning="#000000",
    info="#00FFFF",  # Bright cyan
    info_container="#000000",
    on_info="#000000",
    recording="#FF0000",
    transcribing="#FFFF00",
)


def check_contrast_ratio(foreground: str, background: str) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Parameters
    ----------
    foreground
        Hex color code for foreground text.
    background
        Hex color code for background.

    Returns
    -------
    float
        Contrast ratio (1.0 to 21.0).
    """
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex to RGB."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def luminance(rgb: tuple) -> float:
        """Calculate relative luminance."""
        r, g, b = (x / 255.0 for x in rgb)

        # Linearize
        def linearize(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r = linearize(r)
        g = linearize(g)
        b = linearize(b)

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    fg_rgb = hex_to_rgb(foreground)
    bg_rgb = hex_to_rgb(background)

    fg_lum = luminance(fg_rgb)
    bg_lum = luminance(bg_rgb)

    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)

    return (lighter + 0.05) / (darker + 0.05)


def is_wcag_aa_compliant(foreground: str, background: str, large_text: bool = False) -> bool:
    """
    Check if color contrast meets WCAG AA standard.

    Parameters
    ----------
    foreground
        Hex color code for foreground text.
    background
        Hex color code for background.
    large_text
        Whether text is large (18pt+ or 14pt bold+).

    Returns
    -------
    bool
        True if AA compliant (4.5:1 for normal, 3:1 for large).
    """
    ratio = check_contrast_ratio(foreground, background)
    return ratio >= 3.0 if large_text else ratio >= 4.5


def is_wcag_aaa_compliant(foreground: str, background: str, large_text: bool = False) -> bool:
    """
    Check if color contrast meets WCAG AAA standard.

    Parameters
    ----------
    foreground
        Hex color code for foreground text.
    background
        Hex color code for background.
    large_text
        Whether text is large (18pt+ or 14pt bold+).

    Returns
    -------
    bool
        True if AAA compliant (7:1 for normal, 4.5:1 for large).
    """
    ratio = check_contrast_ratio(foreground, background)
    return ratio >= 4.5 if large_text else ratio >= 7.0


class AccessibilityManager:
    """
    Manages accessibility features and settings.

    This class handles:
    - High contrast mode switching
    - Font size scaling
    - Focus indicator styling
    - Screen reader announcements
    - Reduced motion preferences

    Attributes
    ----------
    settings
        Current accessibility settings.
    config_path
        Path to accessibility config file.
    """

    CONFIG_DIR = Path.home() / ".faster-whisper-hotkey"
    CONFIG_FILE = CONFIG_DIR / "accessibility.json"

    def __init__(self):
        """Initialize the accessibility manager."""
        self._settings = self._load_settings()
        self._theme_manager = get_theme_manager()
        self._announcement_queue: List[str] = []
        self._listeners: List[Callable[[str], None]] = []

    def _load_settings(self) -> AccessibilitySettings:
        """Load accessibility settings from disk."""
        try:
            if self.CONFIG_FILE.exists():
                data = json.loads(self.CONFIG_FILE.read_text())
                return AccessibilitySettings.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load accessibility settings: {e}")
        return AccessibilitySettings()

    def _save_settings(self):
        """Save accessibility settings to disk."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self.CONFIG_FILE.write_text(
                json.dumps(self._settings.to_dict(), indent=2)
            )
        except Exception as e:
            logger.warning(f"Failed to save accessibility settings: {e}")

    @property
    def settings(self) -> AccessibilitySettings:
        """Get current accessibility settings."""
        return self._settings

    def set_font_size(self, size: FontSize):
        """
        Set font size scaling.

        Parameters
        ----------
        size
            Font size to apply.
        """
        self._settings.font_size_scale = size.value
        self._save_settings()
        self._notify_listeners("font_size_changed")

    def set_high_contrast(self, enabled: bool, mode: ContrastMode = ContrastMode.HIGH_CONTRAST):
        """
        Enable or disable high contrast mode.

        Parameters
        ----------
        enabled
            Whether to enable high contrast.
        mode
            Contrast mode to use.
        """
        self._settings.enable_high_contrast = enabled
        self._settings.contrast_mode = mode
        self._save_settings()
        self._notify_listeners("contrast_changed")

    def set_reduce_motion(self, enabled: bool):
        """
        Enable or disable reduced motion.

        Parameters
        ----------
        enabled
            Whether to reduce animations.
        """
        self._settings.reduce_motion = enabled
        self._save_settings()
        self._notify_listeners("motion_changed")

    def get_font_size(self, base_size: float) -> float:
        """
        Get scaled font size.

        Parameters
        ----------
        base_size
            Base font size in pixels.

        Returns
        -------
        float
            Scaled font size.
        """
        return base_size * self._settings.font_size_scale

    def get_focus_style(self) -> FocusStyle:
        """
        Get focus indicator style.

        Returns
        -------
        FocusStyle
            Current focus style configuration.
        """
        if not self._settings.enable_focus_indicators:
            return FocusStyle(width=0, color="transparent")

        # Use yellow in high contrast for better visibility
        if self._settings.enable_high_contrast:
            return FocusStyle(
                width=4.0,
                color="#FFFF00" if self._settings.contrast_mode == ContrastMode.EXTRA_HIGH_CONTRAST else "#000000",
            )

        return FocusStyle(
            width=3.0,
            color="#2196F3",
        )

    def get_adapted_colors(self) -> ColorPalette:
        """
        Get color palette adapted for current accessibility settings.

        Returns
        -------
        ColorPalette
            Adapted color palette.
        """
        if not self._settings.enable_high_contrast:
            return self._theme_manager.colors

        if self._settings.contrast_mode == ContrastMode.EXTRA_HIGH_CONTRAST:
            return EXTRA_HIGH_CONTRAST_PALETTE

        return HIGH_CONTRAST_PALETTE

    def announce(self, message: str, priority: str = "medium"):
        """
        Queue a screen reader announcement.

        Parameters
        ----------
        message
            Message to announce.
        priority
            Priority level ("low", "medium", "high").
        """
        if not self._settings.enable_screen_reader:
            return

        if priority == "high":
            self._announcement_queue.insert(0, message)
        else:
            self._announcement_queue.append(message)

        # Notify listeners
        for listener in self._listeners:
            try:
                listener(message)
            except Exception as e:
                logger.warning(f"Announcement listener error: {e}")

    def get_pending_announcements(self) -> List[str]:
        """
        Get and clear pending announcements.

        Returns
        -------
        List[str]
            Pending announcement messages.
        """
        announcements = self._announcement_queue.copy()
        self._announcement_queue.clear()
        return announcements

    def subscribe_to_announcements(self, callback: Callable[[str], None]) -> Callable:
        """
        Subscribe to screen reader announcements.

        Parameters
        ----------
        callback
            Function to call with announcement message.

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

    def _notify_listeners(self, event: str):
        """Notify listeners of accessibility setting changes."""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.warning(f"Accessibility change listener error: {e}")

    def apply_accessibility_to_control(self, control: ft.Control):
        """
        Apply accessibility settings to a Flet control.

        Parameters
        ----------
        control
            Flet control to enhance.
        """
        # Apply focus style
        if self._settings.enable_focus_indicators and hasattr(control, 'border'):
            focus_style = self.get_focus_style()
            if focus_style.width > 0:
                control.border = ft.Border.all(
                    focus_style.width,
                    focus_style.color,
                )

        # Apply font size scaling to text controls
        if hasattr(control, 'size') and isinstance(getattr(control, 'size', None), (int, float)):
            control.size = self.get_font_size(control.size)

        # Add tooltip for icon-only buttons
        if isinstance(control, ft.IconButton) and not control.tooltip:
            control.tooltip = "Button"  # Default tooltip

    def create_accessible_button(
        self,
        text: str,
        on_click,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        **kwargs
    ) -> ft.ElevatedButton:
        """
        Create an accessible button with proper labels and focus.

        Parameters
        ----------
        text
            Button text.
        on_click
            Click handler.
        icon
            Optional icon.
        tooltip
            Tooltip text (defaults to button text).
        **kwargs
            Additional button properties.

        Returns
        -------
        ft.ElevatedButton
            Accessible button control.
        """
        focus_style = self.get_focus_style()

        return ft.ElevatedButton(
            text=text,
            icon=icon,
            tooltip=tooltip or text,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(
                    width=focus_style.width,
                    color=focus_style.color,
                ) if focus_style.width > 0 else None,
            ),
            **kwargs
        )

    def create_accessible_text(
        self,
        text: str,
        size: float = 14,
        **kwargs
    ) -> ft.Text:
        """
        Create accessible text with proper sizing.

        Parameters
        ----------
        text
            Text content.
        size
            Base font size.
        **kwargs
            Additional text properties.

        Returns
        -------
        ft.Text
            Accessible text control.
        """
        return ft.Text(
            text,
            size=self.get_font_size(size),
            **kwargs
        )

    def validate_contrast(self, foreground: str, background: str) -> Dict[str, bool]:
        """
        Validate color contrast against WCAG standards.

        Parameters
        ----------
        foreground
            Foreground hex color.
        background
            Background hex color.

        Returns
        -------
        Dict[str, bool]
            Dictionary with 'aa' and 'aaa' compliance status.
        """
        return {
            "aa_normal": is_wcag_aa_compliant(foreground, background, large_text=False),
            "aa_large": is_wcag_aa_compliant(foreground, background, large_text=True),
            "aaa_normal": is_wcag_aaa_compliant(foreground, background, large_text=False),
            "aaa_large": is_wcag_aaa_compliant(foreground, background, large_text=True),
            "contrast_ratio": check_contrast_ratio(foreground, background),
        }


# Global accessibility manager instance
_accessibility_manager: Optional[AccessibilityManager] = None


def get_accessibility_manager() -> AccessibilityManager:
    """
    Get the global accessibility manager instance.

    Returns
    -------
    AccessibilityManager
        The global accessibility manager.
    """
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager


def announce_for_accessibility(message: str, priority: str = "medium"):
    """
    Convenience function to make accessibility announcements.

    Parameters
    ----------
    message
        Message to announce.
    priority
        Priority level.
    """
    get_accessibility_manager().announce(message, priority)


def get_accessible_font_size(base_size: float) -> float:
    """
    Get font size scaled for accessibility.

    Parameters
    ----------
    base_size
        Base font size.

    Returns
    -------
    float
        Scaled font size.
    """
    return get_accessibility_manager().get_font_size(base_size)


def is_high_contrast() -> bool:
    """
    Check if high contrast mode is enabled.

    Returns
    -------
    bool
        True if high contrast is enabled.
    """
    return get_accessibility_manager().settings.enable_high_contrast


def is_reduce_motion() -> bool:
    """
    Check if reduced motion is enabled.

    Returns
    -------
    bool
        True if motion should be reduced.
    """
    return get_accessibility_manager().settings.reduce_motion
