"""
Modern theme system for faster-whisper-hotkey Flet GUI.

This module provides a comprehensive theme system with:
- Light and dark theme color palettes
- Typography scale
- Spacing and sizing tokens
- Elevation/shadow system
- Theme persistence
- System theme detection
- Accessibility integration (high contrast, font scaling)

Classes
-------
Theme
    Main theme class with color palettes and design tokens.
ThemeManager
    Manages theme switching, persistence, and system theme detection.
ThemeMode
    Enum for theme modes (light, dark, system).
"""

import logging
import os
import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from .accessibility import AccessibilityManager

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Theme mode options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ColorPalette:
    """
    Color palette for a theme.

    Attributes
    ----------
    primary
        Main brand color.
    primary_container
        Container/background for primary elements.
    on_primary
        Text/icon color on primary background.
    secondary
        Secondary accent color.
    secondary_container
        Container/background for secondary elements.
    on_secondary
        Text/icon color on secondary background.
    background
        Main background color.
    surface
        Surface color for cards and elevated elements.
    surface_variant
        Variant surface color.
    surface_container
        Container surface color.
    surface_container_low
        Low elevation container surface.
    surface_container_lowest
        Lowest elevation container surface.
    on_background
        Text/icon color on background.
    on_surface
        Text/icon color on surface.
    on_surface_variant
        Variant text/icon color.
    outline
        Border and divider color.
    outline_variant
        Variant border color.
    error
        Error color.
    error_container
        Container for error elements.
    on_error
        Text/icon color on error background.
    success
        Success color.
    success_container
        Container for success elements.
    on_success
        Text/icon color on success background.
    warning
        Warning color.
    warning_container
        Container for warning elements.
    on_warning
        Text/icon color on warning background.
    info
        Info color.
    info_container
        Container for info elements.
    on_info
        Text/icon color on info background.
    recording
        Recording state color.
    transcribing
        Transcribing state color.
    """

    # Primary colors
    primary: str = "#1976D2"
    primary_container: str = "#BBDEFB"
    on_primary: str = "#FFFFFF"

    # Secondary colors
    secondary: str = "#03A9F4"
    secondary_container: str = "#B3E5FC"
    on_secondary: str = "#FFFFFF"

    # Background colors
    background: str = "#FAFAFA"
    surface: str = "#FFFFFF"
    surface_variant: str = "#F5F5F5"
    surface_container: str = "#F0F0F0"
    surface_container_low: str = "#FAFAFA"
    surface_container_lowest: str = "#FFFFFF"

    # On colors (text/icons)
    on_background: str = "#1C1B1F"
    on_surface: str = "#1C1B1F"
    on_surface_variant: str = "#49454F"

    # Outline colors
    outline: str = "#79747E"
    outline_variant: str = "#CAC4D0"

    # Status colors
    error: str = "#BA1A1A"
    error_container: str = "#FFDAD6"
    on_error: str = "#FFFFFF"

    success: str = "#00C853"
    success_container: str = "#B9F6CA"
    on_success: str = "#FFFFFF"

    warning: str = "#FF6D00"
    warning_container: str = "#FFE0B2"
    on_warning: str = "#FFFFFF"

    info: str = "#0091EA"
    info_container: str = "#B3E5FC"
    on_info: str = "#FFFFFF"

    # State colors
    recording: str = "#F44336"
    transcribing: str = "#FF9800"

    def to_flet_colors(self) -> Dict[str, Any]:
        """Convert palette to Flet color dict."""
        return {
            "primary": self.primary,
            "primary_container": self.primary_container,
            "on_primary": self.on_primary,
            "secondary": self.secondary,
            "secondary_container": self.secondary_container,
            "on_secondary": self.on_secondary,
            "background": self.background,
            "surface": self.surface,
            "surface_variant": self.surface_variant,
            "surface_container": self.surface_container,
            "surface_container_low": self.surface_container_low,
            "surface_container_lowest": self.surface_container_lowest,
            "on_background": self.on_background,
            "on_surface": self.on_surface,
            "on_surface_variant": self.on_surface_variant,
            "outline": self.outline,
            "outline_variant": self.outline_variant,
            "error": self.error,
            "error_container": self.error_container,
            "on_error": self.on_error,
        }


# Light theme palette
LIGHT_PALETTE = ColorPalette(
    primary="#1976D2",
    primary_container="#D3E3FD",
    on_primary="#FFFFFF",
    secondary="#03A9F4",
    secondary_container="#B3E5FC",
    on_secondary="#FFFFFF",
    background="#FDFBFF",
    surface="#FDFBFF",
    surface_variant="#E1E2EC",
    surface_container="#E1E2EC",
    surface_container_low="#F5F5F5",
    surface_container_lowest="#FFFFFF",
    on_background="#1B1B1F",
    on_surface="#1B1B1F",
    on_surface_variant="#44474E",
    outline="#74777F",
    outline_variant="#C4C6CF",
    error="#BA1A1A",
    error_container="#FFDAD6",
    on_error="#FFFFFF",
    success="#00C853",
    success_container="#B9F6CA",
    on_success="#FFFFFF",
    warning="#FF6D00",
    warning_container="#FFE0B2",
    on_warning="#FFFFFF",
    info="#0091EA",
    info_container="#B3E5FC",
    on_info="#FFFFFF",
    recording="#DC362E",
    transcribing="#FF9800",
)

# Dark theme palette
DARK_PALETTE = ColorPalette(
    primary="#9ECAFF",
    primary_container="#00497D",
    on_primary="#003258",
    secondary="#54B3F7",
    secondary_container="#004A6E",
    on_secondary="#002F45",
    background="#1B1B1F",
    surface="#1B1B1F",
    surface_variant="#2E3038",
    surface_container="#2E3038",
    surface_container_low="#201F24",
    surface_container_lowest="#151518",
    on_background="#E3E2E6",
    on_surface="#E3E2E6",
    on_surface_variant="#C4C7CF",
    outline="#8E9199",
    outline_variant="#44474E",
    error="#FFB4AB",
    error_container="#93000A",
    on_error="#690005",
    success="#00E676",
    success_container="#003314",
    on_success="#00220B",
    warning="#FFAB40",
    warning_container="#662C00",
    on_warning="#331C00",
    info="#40C4FF",
    info_container="#004258",
    on_info="#001F29",
    recording="#FF8A80",
    transcribing="#FFB74D",
)


@dataclass
class TypographyScale:
    """
    Typography scale for consistent text sizing.

    Attributes
    ----------
    display_large
        Largest display text.
    display_medium
        Medium display text.
    display_small
        Small display text.
    headline_large
        Large headline.
    headline_medium
        Medium headline.
    headline_small
        Small headline.
    title_large
        Large title.
    title_medium
        Medium title.
    title_small
        Small title.
    body_large
        Large body text.
    body_medium
        Medium body text (default body).
    body_small
        Small body text.
    label_large
        Large label.
    label_medium
        Medium label.
    label_small
        Small label.
    code
        Monospace code font.
    """

    display_large: int = 57
    display_medium: int = 45
    display_small: int = 36
    headline_large: int = 32
    headline_medium: int = 28
    headline_small: int = 24
    title_large: int = 22
    title_medium: int = 16
    title_small: int = 14
    body_large: int = 16
    body_medium: int = 14
    body_small: int = 12
    label_large: int = 14
    label_medium: int = 12
    label_small: int = 11
    code: int = 13


TYPOGRAPHY = TypographyScale()


@dataclass
class SpacingTokens:
    """
    Spacing tokens for consistent layout.

    Attributes
    ----------
    none
        No spacing.
    xs
        Extra small spacing (4px).
    sm
        Small spacing (8px).
    md
        Medium spacing (16px).
    lg
        Large spacing (24px).
    xl
        Extra large spacing (32px).
    xxl
        Extra extra large spacing (48px).
    """

    none: float = 0
    xs: float = 4
    sm: float = 8
    md: float = 16
    lg: float = 24
    xl: float = 32
    xxl: float = 48


SPACING = SpacingTokens()


@dataclass
class BorderRadiusTokens:
    """
    Border radius tokens for consistent corner rounding.

    Attributes
    ----------
    none
        No border radius.
    sm
        Small radius (4px).
    md
        Medium radius (8px).
    lg
        Large radius (12px).
    xl
        Extra large radius (16px).
    full
        Fully rounded (pill shape).
    """

    none: float = 0
    sm: float = 4
    md: float = 8
    lg: float = 12
    xl: float = 16
    xxl: float = 24
    full: float = 100


BORDER_RADIUS = BorderRadiusTokens()


@dataclass
class ElevationTokens:
    """
    Elevation/shadow tokens for depth.

    Attributes
    ----------
    level0
        No elevation (flat).
    level1
        Level 1 elevation (subtle).
    level2
        Level 2 elevation (moderate).
    level3
        Level 3 elevation (high).
    level4
        Level 4 elevation (highest).
    """

    level0: tuple = ()
    level1: tuple = (0, 1, 3, 0, "#000000", 0.12), (0, 1, 2, 0, "#000000", 0.24)
    level2: tuple = (0, 3, 6, 0, "#000000", 0.16), (0, 2, 4, 0, "#000000", 0.23)
    level3: tuple = (0, 10, 20, 0, "#000000", 0.19), (0, 6, 6, 0, "#000000", 0.23)
    level4: tuple = (0, 15, 25, 0, "#000000", 0.30), (0, 6, 10, 0, "#000000", 0.22)


ELEVATION = ElevationTokens()


@dataclass
class AnimationDuration:
    """
    Animation duration tokens.

    Attributes
    ----------
    fast
        Fast animation (150ms).
    normal
        Normal animation (250ms).
    slow
        Slow animation (350ms).
    """

    fast: int = 150
    normal: int = 250
    slow: int = 350


ANIMATION_DURATION = AnimationDuration()


@dataclass
class Theme:
    """
    Complete theme definition.

    Attributes
    ----------
    name
        Theme name ('light' or 'dark').
    palette
        Color palette for this theme.
    typography
        Typography scale.
    spacing
        Spacing tokens.
    border_radius
        Border radius tokens.
    elevation
        Elevation/shadow tokens.
    animation_duration
        Animation duration tokens.
    """

    name: str
    palette: ColorPalette
    typography: TypographyScale = field(default_factory=TypographyScale)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    border_radius: BorderRadiusTokens = field(default_factory=BorderRadiusTokens)
    elevation: ElevationTokens = field(default_factory=ElevationTokens)
    animation_duration: AnimationDuration = field(default_factory=AnimationDuration)

    def to_flet_theme(self) -> ft.Theme:
        """Convert to Flet Theme object."""
        palette = self.palette

        # Map colors to Flet theme
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=palette.primary,
                primary_container=palette.primary_container,
                on_primary=palette.on_primary,
                secondary=palette.secondary,
                secondary_container=palette.secondary_container,
                on_secondary=palette.on_secondary,
                background=palette.background,
                surface=palette.surface,
                surface_variant=palette.surface_variant,
                on_background=palette.on_background,
                on_surface=palette.on_surface,
                on_surface_variant=palette.on_surface_variant,
                outline=palette.outline,
                outline_variant=palette.outline_variant,
                error=palette.error,
                error_container=palette.error_container,
                on_error=palette.on_error,
            ),
            visual_density=ft.ThemeVisualDensity.COMPACT,
        )


# Predefined themes
LIGHT_THEME = Theme(name="light", palette=LIGHT_PALETTE)
DARK_THEME = Theme(name="dark", palette=DARK_PALETTE)


class ThemeManager:
    """
    Manages theme switching, persistence, and system theme detection.

    This class handles:
    - Switching between light, dark, and system themes
    - Persisting theme preference to disk
    - Detecting system theme on Windows
    - Providing theme callbacks for UI updates

    Attributes
    ----------
    config_path
        Path to theme configuration file.
    _current_mode
        Current theme mode preference.
    _is_dark
        Whether dark mode is currently active.
    _listeners
        Callbacks for theme change events.
    """

    CONFIG_DIR = Path.home() / ".faster-whisper-hotkey"
    CONFIG_FILE = CONFIG_DIR / "theme.json"

    def __init__(self):
        """Initialize the theme manager."""
        self._current_mode: ThemeMode = ThemeMode.SYSTEM
        self._is_dark: bool = False
        self._listeners: list = []

        # Load saved preference
        self._load_preference()

        # Determine initial theme
        self._update_current_theme()

    def _load_preference(self):
        """Load theme preference from disk."""
        try:
            if self.CONFIG_FILE.exists():
                import json
                data = json.loads(self.CONFIG_FILE.read_text())
                mode_str = data.get("mode", "system")
                self._current_mode = ThemeMode(mode_str)
        except Exception as e:
            logger.warning(f"Failed to load theme preference: {e}")
            self._current_mode = ThemeMode.SYSTEM

    def _save_preference(self):
        """Save theme preference to disk."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            import json
            self.CONFIG_FILE.write_text(
                json.dumps({"mode": self._current_mode.value})
            )
        except Exception as e:
            logger.warning(f"Failed to save theme preference: {e}")

    def _update_current_theme(self):
        """Update current theme based on mode and system settings."""
        if self._current_mode == ThemeMode.DARK:
            self._is_dark = True
        elif self._current_mode == ThemeMode.LIGHT:
            self._is_dark = False
        else:
            # System mode - detect from OS
            self._is_dark = self._detect_system_theme()

    def _detect_system_theme(self) -> bool:
        """
        Detect system theme preference.

        Returns
        -------
        bool
            True if dark mode is enabled, False otherwise.
        """
        try:
            if platform.system() == "Windows":
                # Check Windows registry for dark mode setting
                try:
                    import winreg
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    ) as key:
                        # AppsUseLightTheme: 0 = dark, 1 = light
                        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                        return value == 0
                except (OSError, FileNotFoundError):
                    pass
        except Exception as e:
            logger.debug(f"System theme detection failed: {e}")

        # Default to light mode
        return False

    def get_current_theme(self) -> Theme:
        """
        Get the current active theme.

        Returns
        -------
        Theme
            The currently active theme (LIGHT_THEME or DARK_THEME).
        """
        return DARK_THEME if self._is_dark else LIGHT_THEME

    def get_theme_mode(self) -> ThemeMode:
        """
        Get the current theme mode.

        Returns
        -------
        ThemeMode
            The current theme mode (LIGHT, DARK, or SYSTEM).
        """
        return self._current_mode

    def set_theme_mode(self, mode: ThemeMode):
        """
        Set the theme mode.

        Parameters
        ----------
        mode
            The theme mode to set (LIGHT, DARK, or SYSTEM).
        """
        if self._current_mode != mode:
            self._current_mode = mode
            self._update_current_theme()
            self._save_preference()
            self._notify_listeners()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self._is_dark:
            self.set_theme_mode(ThemeMode.LIGHT)
        else:
            self.set_theme_mode(ThemeMode.DARK)

    def is_dark(self) -> bool:
        """
        Check if dark theme is currently active.

        Returns
        -------
        bool
            True if dark theme is active.
        """
        return self._is_dark

    def subscribe(self, callback):
        """
        Subscribe to theme change events.

        Parameters
        ----------
        callback
            Function to call when theme changes.

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
        """Notify all listeners of theme change."""
        theme = self.get_current_theme()
        for callback in self._listeners:
            try:
                callback(theme)
            except Exception as e:
                logger.warning(f"Theme change callback error: {e}")

    def apply_to_page(self, page: ft.Page):
        """
        Apply the current theme to a Flet page.

        Parameters
        ----------
        page
            The Flet page to apply the theme to.
        """
        theme = self.get_current_theme()

        # Apply the Flet theme
        page.theme = theme.to_flet_theme()

        # Set theme mode
        if self._is_dark:
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT

        # Set page background color
        page.bgcolor = theme.palette.surface_container_lowest

    # Accessibility manager reference
    _accessibility_manager: Optional["AccessibilityManager"] = None

    def set_accessibility_manager(self, manager: "AccessibilityManager"):
        """
        Set the accessibility manager for adaptive theming.

        Parameters
        ----------
        manager
            The accessibility manager instance.
        """
        self._accessibility_manager = manager

    # Convenience methods for accessing theme values
    @property
    def colors(self) -> ColorPalette:
        """Get the current color palette, adapted for accessibility."""
        base_palette = self.get_current_theme().palette

        # Apply accessibility adaptations
        if self._accessibility_manager:
            adapted = self._accessibility_manager.get_adapted_colors()
            if adapted is not base_palette:
                return adapted

        return base_palette

    @property
    def type(self) -> TypographyScale:
        """Get the typography scale."""
        return TYPOGRAPHY

    @property
    def space(self) -> SpacingTokens:
        """Get the spacing tokens."""
        return SPACING

    @property
    def radius(self) -> BorderRadiusTokens:
        """Get the border radius tokens."""
        return BORDER_RADIUS

    @property
    def elevation(self) -> ElevationTokens:
        """Get the elevation tokens."""
        return ELEVATION

    @property
    def duration(self) -> AnimationDuration:
        """Get the animation duration tokens, adapted for reduced motion."""
        base_duration = ANIMATION_DURATION

        # Apply reduced motion if enabled
        if self._accessibility_manager and self._accessibility_manager.settings.reduce_motion:
            return AnimationDuration(fast=0, normal=0, slow=0)

        return base_duration

    def get_font_size(self, base_size: float) -> float:
        """
        Get font size scaled for accessibility.

        Parameters
        ----------
        base_size
            Base font size in pixels.

        Returns
        -------
        float
            Scaled font size.
        """
        if self._accessibility_manager:
            return self._accessibility_manager.get_font_size(base_size)
        return base_size


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """
    Get the global theme manager instance.

    Returns
    -------
    ThemeManager
        The global theme manager.
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_current_theme() -> Theme:
    """
    Get the current active theme.

    Returns
    -------
    Theme
        The currently active theme.
    """
    return get_theme_manager().get_current_theme()


def is_dark_mode() -> bool:
    """
    Check if dark mode is currently active.

    Returns
    -------
    bool
        True if dark theme is active.
    """
    return get_theme_manager().is_dark()
