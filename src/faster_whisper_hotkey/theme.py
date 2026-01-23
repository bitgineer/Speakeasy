"""
Modern theme system for faster-whisper-hotkey GUI.

This module provides a comprehensive theming system with:
- 8px grid-based spacing system
- Modern color palettes (light/dark mode support)
- Consistent typography scale
- Rounded corners and shadows
- Pre-configured styles for all ttk widgets
- System-aware theme detection (Windows/macOS/Linux)
- Theme persistence with configurable storage location

Classes
-------
Theme
    Main theme configuration class with all design tokens.

ModernStyle
    Configured ttk.Style with modern styling applied.

ThemeManager
    Manager for applying and switching themes at runtime with system detection.

Notes
-----
The theme uses an 8px grid system for all spacing and sizing.
Colors follow Material Design 3 guidelines with custom accent colors.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Literal, Optional
import platform
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass


class Theme:
    """Modern theme configuration with 8px grid system.

    Design tokens following modern UI/UX principles:
    - 8px grid for all spacing and sizing
    - Rounded corners (8px cards, 4px buttons)
    - Subtle shadows for depth
    - Consistent typography scale
    """

    # Spacing scale (8px grid)
    SPACING = {
        "xs": 4,      # 0.5x
        "sm": 8,      # 1x
        "md": 16,     # 2x
        "lg": 24,     # 3x
        "xl": 32,     # 4x
        "xxl": 48,    # 6x
    }

    # Border radius
    RADIUS = {
        "sm": 4,      # Buttons, small elements
        "md": 8,      # Cards, panels
        "lg": 12,     # Large containers
        "xl": 16,     # Modal dialogs
        "round": 50,  # Pill-shaped elements
    }

    # Typography scale (type ramp)
    FONT_SIZES = {
        "xs": 10,
        "sm": 11,
        "base": 12,
        "md": 13,
        "lg": 14,
        "xl": 16,
        "2xl": 18,
        "3xl": 24,
        "4xl": 32,
    }

    # Font families by platform
    if platform.system() == "Windows":
        FONT_FAMILY = "Segoe UI"
        FONT_FAMILY_MONO = "Consolas"
    elif platform.system() == "Darwin":  # macOS
        FONT_FAMILY = "SF Pro Text"
        FONT_FAMILY_MONO = "SF Mono"
    else:  # Linux and others
        FONT_FAMILY = "system-ui"
        FONT_FAMILY_MONO = "monospace"

    # Light mode colors
    LIGHT = {
        # Primary colors
        "primary": "#2196F3",           # Blue 500
        "primary_hover": "#1976D2",     # Blue 700
        "primary_light": "#E3F2FD",     # Blue 50

        # Secondary colors
        "secondary": "#607D8B",         # Blue Grey 500
        "secondary_hover": "#455A64",   # Blue Grey 700

        # Success colors
        "success": "#4CAF50",           # Green 500
        "success_bg": "#E8F5E9",        # Green 50

        # Warning colors
        "warning": "#FF9800",           # Orange 500
        "warning_bg": "#FFF3E0",        # Orange 50

        # Error colors
        "error": "#F44336",             # Red 500
        "error_bg": "#FFEBEE",          # Red 50

        # Neutral colors (grayscale)
        "bg_main": "#FFFFFF",           # Main background
        "bg_card": "#FAFAFA",           # Card/surface background
        "bg_hover": "#F5F5F5",          # Hover background
        "bg_active": "#EEEEEE",         # Active/pressed background

        "fg_primary": "#212121",        # Primary text
        "fg_secondary": "#757575",      # Secondary text
        "fg_disabled": "#BDBDBD",       # Disabled text
        "fg_hint": "#9E9E9E",           # Hint/placeholder text

        # Border colors
        "border": "#E0E0E0",            # Default border
        "border_focus": "#2196F3",      # Focus border
        "border_hover": "#BDBDBD",      # Hover border

        # Shadow colors (with alpha for platform compatibility)
        "shadow_light": "#E0E0E0",
        "shadow_medium": "#BDBDBD",
    }

    # Dark mode colors
    DARK = {
        # Primary colors
        "primary": "#64B5F6",           # Blue 400 (lighter for dark mode)
        "primary_hover": "#42A5F5",     # Blue 400
        "primary_light": "#1A2332",     # Dark blue tint

        # Secondary colors
        "secondary": "#90A4AE",         # Blue Grey 400
        "secondary_hover": "#B0BEC5",   # Blue Grey 300

        # Success colors
        "success": "#66BB6A",           # Green 400
        "success_bg": "#1B3320",        # Dark green tint

        # Warning colors
        "warning": "#FFB74D",           # Orange 400
        "warning_bg": "#33251A",        # Dark orange tint

        # Error colors
        "error": "#EF5350",             # Red 400
        "error_bg": "#331A1A",          # Dark red tint

        # Neutral colors
        "bg_main": "#1E1E1E",           # Main background (VS Code style)
        "bg_card": "#252526",           # Card/surface background
        "bg_hover": "#2D2D2D",          # Hover background
        "bg_active": "#37373D",         # Active/pressed background

        "fg_primary": "#E0E0E0",        # Primary text
        "fg_secondary": "#A0A0A0",      # Secondary text
        "fg_disabled": "#555555",       # Disabled text
        "fg_hint": "#707070",           # Hint/placeholder text

        # Border colors
        "border": "#3D3D3D",            # Default border
        "border_focus": "#64B5F6",      # Focus border
        "border_hover": "#555555",      # Hover border

        # Shadow colors
        "shadow_light": "#000000",
        "shadow_medium": "#000000",
    }

    def __init__(self, mode: Literal["light", "dark"] = "light"):
        """Initialize theme with specified mode.

        Args:
            mode: Color mode - "light" or "dark"
        """
        self.mode = mode
        self._colors = self.DARK if mode == "dark" else self.LIGHT

    @property
    def colors(self) -> Dict[str, str]:
        """Get current color palette."""
        return self._colors

    def get_color(self, key: str) -> str:
        """Get a color value by key."""
        return self._colors.get(key, self._colors.get(key, "#000000"))

    def get_spacing(self, size: str) -> int:
        """Get spacing value by size name."""
        return self.SPACING.get(size, self.SPACING["sm"])

    def get_radius(self, size: str) -> int:
        """Get border radius by size name."""
        return self.RADIUS.get(size, self.RADIUS["sm"])

    def get_font(self, size: str = "base", bold: bool = False, italic: bool = False) -> tuple:
        """Get font tuple for ttk widgets.

        Args:
            size: Font size name from FONT_SIZES
            bold: Whether font should be bold
            italic: Whether font should be italic

        Returns:
            Tuple of (family, size, modifiers)
        """
        font_size = self.FONT_SIZES.get(size, self.FONT_SIZES["base"])
        modifiers = []
        if bold:
            modifiers.append("bold")
        if italic:
            modifiers.append("italic")
        style = " ".join(modifiers) if modifiers else "normal"
        return (self.FONT_FAMILY, font_size, style)

    def get_mono_font(self, size: str = "base") -> tuple:
        """Get monospace font tuple."""
        font_size = self.FONT_SIZES.get(size, self.FONT_SIZES["base"])
        return (self.FONT_FAMILY_MONO, font_size, "normal")

    def toggle_mode(self) -> str:
        """Toggle between light and dark mode."""
        self.mode = "dark" if self.mode == "light" else "light"
        self._colors = self.DARK if self.mode == "dark" else self.LIGHT
        return self.mode


class ModernStyle:
    """Configured ttk.Style with modern theme applied.

    Applies custom styling to all ttk widgets including:
    - Frame, LabelFrame (cards with radius)
    - Label (with variants: title, subtitle, body, hint)
    - Button (with variants: primary, secondary, danger)
    - Entry (with focus states)
    - Checkbutton, Radiobutton
    - Combobox, Spinbox
    - Notebook (tabs)
    - Treeview (lists/tables)
    - Progressbar
    - Scrollbar
    """

    # Style type names for widget variants
    VARIANT_PRIMARY = "primary"
    VARIANT_SECONDARY = "secondary"
    VARIANT_DANGER = "danger"
    VARIANT_SUCCESS = "success"
    VARIANT_CARD = "card"
    VARIANT_TITLE = "title"
    VARIANT_SUBTITLE = "subtitle"
    VARIANT_BODY = "body"
    VARIANT_HINT = "hint"
    VARIANT_MONO = "mono"

    def __init__(self, theme: Optional[Theme] = None):
        """Initialize modern style.

        Args:
            theme: Theme instance to use. Creates default light theme if None.
        """
        self.theme = theme or Theme(mode="light")
        self.style = ttk.Style()

        # Use modern theme as base (works on all platforms)
        self.style.theme_use("clam")

        # Apply all widget styles
        self._configure_layouts()
        self._configure_colors()
        self._configure_widgets()

    def _configure_layouts(self):
        """Configure base layout settings."""
        # Default padding for all widgets
        self.style.configure(".", padding=1)

    def _configure_colors(self):
        """Configure theme colors."""
        c = self.theme.colors

        # Map colors to ttk elements
        self.style.map(
            "TButton",
            foreground=[("pressed", c["fg_primary"]),
                       ("active", c["fg_primary"]),
                       ("disabled", c["fg_disabled"])],
            background=[("pressed", c["bg_active"]),
                       ("active", c["bg_hover"]),
                       ("disabled", c["bg_card"])],
            bordercolor=[("focus", c["border_focus"])],
        )

        self.style.map(
            "TEntry",
            foreground=[("disabled", c["fg_disabled"])],
            fieldbackground=[("disabled", c["bg_card"])],
            bordercolor=[("focus", c["border_focus"])],
        )

        self.style.map(
            "TCombobox",
            foreground=[("disabled", c["fg_disabled"])],
            fieldbackground=[("disabled", c["bg_card"])],
        )

        self.style.map(
            "TNotebook",
            background=[("active", c["bg_card"])],
        )

        self.style.map(
            "TNotebook.Tab",
            padding=[("selected", [self.theme.get_spacing("sm"), self.theme.get_spacing("sm"),
                                    self.theme.get_spacing("sm"), self.theme.get_spacing("sm")])],
            expand=[("selected", [1, 1, 1, 0])],
        )

        self.style.map(
            "Treeview",
            foreground=[("selected", c["fg_primary"])],
            background=[("selected", c["primary_light"])],
        )

        self.style.map(
            "Treeview",
            foreground=[("selected", c["fg_primary"])],
            background=[("selected", c["primary_light"])],
        )

    def _configure_widgets(self):
        """Configure individual widget styles."""
        c = self.theme.colors
        sm = self.theme.get_spacing("sm")
        md = self.theme.get_spacing("md")
        radius_sm = self.theme.get_radius("sm")
        radius_md = self.theme.get_radius("md")

        # Frame (container/card)
        self.style.configure(
            "TFrame",
            background=c["bg_main"],
            borderwidth=0,
            relief="flat",
        )

        # Card variant (with border and background)
        self.style.configure(
            f"{self.VARIANT_CARD}.TFrame",
            background=c["bg_card"],
            relief="flat",
            borderwidth=1,
        )

        # LabelFrame (grouped sections)
        self.style.configure(
            "TLabelframe",
            background=c["bg_card"],
            bordercolor=c["border"],
            borderwidth=1,
            relief="flat",
        )
        self.style.configure(
            "TLabelframe.Label",
            background=c["bg_card"],
            foreground=c["fg_secondary"],
            font=self.theme.get_font("sm", bold=True),
        )

        # Label (default)
        self.style.configure(
            "TLabel",
            background=c["bg_main"],
            foreground=c["fg_primary"],
            font=self.theme.get_font("base"),
        )

        # Label variants
        self.style.configure(
            f"{self.VARIANT_TITLE}.TLabel",
            font=self.theme.get_font("2xl", bold=True),
            foreground=c["fg_primary"],
        )

        self.style.configure(
            f"{self.VARIANT_SUBTITLE}.TLabel",
            font=self.theme.get_font("lg", bold=True),
            foreground=c["fg_primary"],
        )

        self.style.configure(
            f"{self.VARIANT_BODY}.TLabel",
            font=self.theme.get_font("base"),
            foreground=c["fg_secondary"],
        )

        self.style.configure(
            f"{self.VARIANT_HINT}.TLabel",
            font=self.theme.get_font("sm"),
            foreground=c["fg_hint"],
        )

        self.style.configure(
            f"{self.VARIANT_MONO}.TLabel",
            font=self.theme.get_mono_font("base"),
            foreground=c["fg_primary"],
        )

        # Button (default - secondary style)
        self.style.configure(
            "TButton",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            background=c["bg_card"],
            bordercolor=c["border"],
            borderwidth=1,
            relief="flat",
            padding=(sm, sm // 2, sm, sm // 2),
        )

        # Primary button
        self.style.configure(
            f"{self.VARIANT_PRIMARY}.TButton",
            font=self.theme.get_font("base", bold=True),
            foreground="#FFFFFF",
            background=c["primary"],
            bordercolor=c["primary"],
            borderwidth=0,
            relief="flat",
            padding=(md, sm, md, sm),
        )
        self.style.map(
            f"{self.VARIANT_PRIMARY}.TButton",
            background=[("active", c["primary_hover"]),
                       ("pressed", c["primary_hover"])],
        )

        # Danger button
        self.style.configure(
            f"{self.VARIANT_DANGER}.TButton",
            font=self.theme.get_font("base", bold=True),
            foreground="#FFFFFF",
            background=c["error"],
            bordercolor=c["error"],
            borderwidth=0,
            relief="flat",
            padding=(md, sm, md, sm),
        )
        self.style.map(
            f"{self.VARIANT_DANGER}.TButton",
            background=[("active", "#D32F2F"),
                       ("pressed", "#D32F2F")],
        )

        # Entry (text input)
        self.style.configure(
            "TEntry",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            fieldbackground=c["bg_card"],
            bordercolor=c["border"],
            borderwidth=1,
            relief="flat",
            padding=sm,
            insertcolor=c["fg_primary"],
        )
        self.style.map(
            "TEntry",
            bordercolor=[("focus", c["border_focus"])],
        )

        # Checkbutton
        self.style.configure(
            "TCheckbutton",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            background=c["bg_main"],
            bordercolor=c["border"],
        )

        # Radiobutton
        self.style.configure(
            "TRadiobutton",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            background=c["bg_main"],
        )

        # Combobox (dropdown)
        self.style.configure(
            "TCombobox",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            fieldbackground=c["bg_card"],
            bordercolor=c["border"],
            borderwidth=1,
            relief="flat",
            padding=sm,
        )
        self.style.map(
            "TCombobox",
            bordercolor=[("focus", c["border_focus"])],
        )

        # Notebook (tabbed interface)
        self.style.configure(
            "TNotebook",
            background=c["bg_main"],
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            font=self.theme.get_font("base", bold=True),
            foreground=c["fg_secondary"],
            background=c["bg_card"],
            borderwidth=0,
            padding=(md, sm),
        )
        self.style.map(
            "TNotebook.Tab",
            foreground=[("selected", c["fg_primary"])],
            background=[("selected", c["bg_main"])],
            expand=[("selected", [1, 1, 1, 0])],
        )

        # Treeview (list/table)
        self.style.configure(
            "Treeview",
            font=self.theme.get_font("base"),
            foreground=c["fg_primary"],
            background=c["bg_main"],
            fieldbackground=c["bg_main"],
            borderwidth=0,
        )
        self.style.configure(
            "Treeview.Heading",
            font=self.theme.get_font("sm", bold=True),
            foreground=c["fg_secondary"],
            background=c["bg_card"],
            borderwidth=0,
            relief="flat",
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", c["bg_hover"])],
        )
        self.style.map(
            "Treeview",
            background=[("selected", c["primary_light"])],
            foreground=[("selected", c["fg_primary"])],
        )

        # Progressbar
        self.style.configure(
            "TProgressbar",
            background=c["primary"],
            borderwidth=0,
            thickness=4,
        )

        # Horizontal Scale
        self.style.configure(
            "Horizontal.TScale",
            background=c["bg_main"],
            troughcolor=c["bg_card"],
            borderwidth=0,
        )

        # Separator
        self.style.configure(
            "TSeparator",
            background=c["border"],
        )

        # Scrollbar
        self.style.configure(
            "TScrollbar",
            background=c["bg_card"],
            bordercolor=c["bg_main"],
            arrowcolor=c["fg_secondary"],
            darkcolor=c["bg_card"],
            lightcolor=c["bg_card"],
            troughcolor=c["bg_main"],
            borderwidth=0,
            arrowsize=12,
        )

        # Panedwindow
        self.style.configure(
            "TPanedwindow",
            background=c["bg_main"],
        )

    def apply_to_widget(self, widget: tk.Widget):
        """Apply theme colors to a standard tk widget.

        Args:
            widget: The tkinter widget to style
        """
        c = self.theme.colors

        try:
            widget.configure(
                bg=c["bg_main"],
                fg=c["fg_primary"],
            )
        except tk.TclError:
            # Widget doesn't support bg/fg (e.g. ttk widgets)
            pass

        # Configure common widget types
        if isinstance(widget, (tk.Entry, tk.Text)):
            widget.configure(
                insertbackground=c["fg_primary"],
                selectbackground=c["primary"],
                selectforeground="#FFFFFF",
                bd=1,
                relief="flat",
                highlightthickness=1,
                highlightbackground=c["border"],
                highlightcolor=c["border_focus"],
            )
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=c["bg_card"],
                fg=c["fg_primary"],
                relief="flat",
                bd=0,
                padx=self.theme.get_spacing("sm"),
                pady=self.theme.get_spacing("sm") // 2,
                activebackground=c["bg_hover"],
            )
        elif isinstance(widget, tk.Listbox):
            widget.configure(
                bg=c["bg_main"],
                fg=c["fg_primary"],
                selectbackground=c["primary_light"],
                selectforeground=c["fg_primary"],
                highlightthickness=1,
                highlightbackground=c["border"],
                highlightcolor=c["border_focus"],
                bd=0,
                relief="flat",
            )
        elif isinstance(widget, tk.Canvas):
            widget.configure(
                bg=c["bg_main"],
                highlightthickness=0,
                bd=0,
            )

    def update_theme(self, theme: Theme):
        """Update style with new theme.

        Args:
            theme: New theme instance to apply
        """
        self.theme = theme
        self._configure_colors()
        self._configure_widgets()


class ThemeManager:
    """Manager for applying and switching themes at runtime with system detection."""

    # Theme modes
    MODE_LIGHT = "light"
    MODE_DARK = "dark"
    MODE_SYSTEM = "system"

    def __init__(
        self,
        root: tk.Tk,
        initial_mode: str = "system",
        config_path: Optional[Path] = None,
        save_callback: Optional[callable] = None
    ):
        """Initialize theme manager.

        Args:
            root: Root tkinter window
            initial_mode: Initial theme mode ("light", "dark", or "system")
            config_path: Path to theme config file. If None, uses default location.
            save_callback: Optional callback for saving theme changes. If provided,
                          config file saving is disabled.
        """
        self.root = root
        self.current_mode = initial_mode # Initialize public attribute
        self._current_setting = initial_mode  # User's setting
        self._effective_mode = self._detect_system_theme()  # Actual mode
        self.theme = Theme(mode=self._effective_mode)
        self.style = ModernStyle(self.theme)
        self._styled_widgets = []
        self._save_callback = save_callback

        # Determine config path
        if config_path is None:
            config_dir = Path.home() / ".config" / "faster-whisper-hotkey"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "theme.json"

        self.config_path = config_path

        # Update effective mode based on initial setting
        self._update_effective_mode()

        # Apply initial theme to root
        self.style.apply_to_widget(root)

    def _detect_system_theme(self) -> Literal["light", "dark"]:
        """
        Detect system theme preference.

        Returns:
            "dark" or "light" based on system settings.
        """
        system = platform.system()

        if system == "Windows":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                    # AppsUseLightTheme: 0 = dark, 1 = light
                    apps_use_light_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                    return "light" if apps_use_light_theme else "dark"
            except (ImportError, OSError):
                return "dark"

        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True, timeout=1
                )
                # Returns "Dark" if dark mode enabled
                return "dark" if "Dark" in result.stdout else "light"
            except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                return "light"

        else:  # Linux and others
            try:
                # Try reading from gsettings (GNOME)
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True, timeout=1
                )
                theme_name = result.stdout.strip().strip("'").lower()
                return "dark" if "dark" in theme_name else "light"
            except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass

            try:
                # Try XDG settings
                xdg_config = Path.home() / ".config" / "gtk-3.0" / "settings.ini"
                if xdg_config.exists():
                    with open(xdg_config, 'r') as f:
                        content = f.read().lower()
                        return "dark" if "gtk-application-prefer-dark-theme=1" in content else "light"
            except (IOError, OSError):
                pass

        # Default to dark theme
        return "dark"

    def _load_config(self) -> None:
        """Load theme configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self._current_setting = config.get("theme_mode", self.MODE_SYSTEM)
                    self._update_effective_mode()
            except (json.JSONDecodeError, IOError):
                self._current_setting = self.MODE_SYSTEM
                self._update_effective_mode()

    def _save_config(self) -> None:
        """Save theme configuration via callback or to file."""
        if self._save_callback is not None:
            # Use external callback (saves to main settings)
            self._save_callback(self._current_setting)
        else:
            # Fallback to config file
            try:
                with open(self.config_path, 'w') as f:
                    json.dump({"theme_mode": self._current_setting}, f)
            except IOError:
                pass

    def _update_effective_mode(self) -> None:
        """Update effective mode based on current setting."""
        if self._current_setting == self.MODE_SYSTEM:
            self._effective_mode = self._detect_system_theme()
        else:
            self._effective_mode = self._current_setting

    def apply_theme(self):
        """Apply current theme to root window."""
        self.style.apply_to_widget(self.root)

    def apply_to_window(self, window: tk.Tk | tk.Toplevel):
        """Apply current theme to a specific window.

        Args:
            window: The tkinter window to theme (can be root or a Toplevel).
        """
        self.style.apply_to_widget(window)

    def set_mode(self, mode: Literal["light", "dark", "system"]):
        """Set theme mode.

        Args:
            mode: "light", "dark", or "system"
        """
        if mode not in (self.MODE_LIGHT, self.MODE_DARK, self.MODE_SYSTEM):
            raise ValueError(f"Invalid theme mode: {mode}")

        self._current_setting = mode
        self._update_effective_mode()

        # Update theme if effective mode changed
        if self.theme.mode != self._effective_mode:
            self.theme = Theme(mode=self._effective_mode)
            self.style.update_theme(self.theme)

            # Re-apply to root
            self.apply_theme()

            # Update all tracked widgets
            for widget in self._styled_widgets:
                if widget.winfo_exists():
                    self.style.apply_to_widget(widget)

        # Save setting
        self._save_config()

    def get_mode(self) -> Literal["light", "dark", "system"]:
        """Get the current theme mode setting."""
        return self._current_setting

    def get_effective_mode(self) -> Literal["light", "dark"]:
        """Get the effective theme mode (after resolving 'system')."""
        return self._effective_mode

    def is_dark(self) -> bool:
        """Check if the effective theme is dark."""
        return self._effective_mode == self.MODE_DARK

    def is_light(self) -> bool:
        """Check if the effective theme is light."""
        return self._effective_mode == self.MODE_LIGHT

    def toggle_mode(self) -> str:
        """Toggle between light, dark, and system modes.

        Returns:
            New mode ("light", "dark", or "system")
        """
        if self._current_setting == self.MODE_LIGHT:
            new_mode = self.MODE_DARK
        elif self._current_setting == self.MODE_DARK:
            new_mode = self.MODE_SYSTEM
        else:
            new_mode = self.MODE_LIGHT

        self.set_mode(new_mode)
        return new_mode

    def refresh_system_theme(self) -> bool:
        """Refresh system theme detection and update if needed.

        Returns:
            True if effective mode changed, False otherwise
        """
        if self._current_setting == self.MODE_SYSTEM:
            old_effective = self._effective_mode
            self._update_effective_mode()
            if old_effective != self._effective_mode:
                self.theme = Theme(mode=self._effective_mode)
                self.style.update_theme(self.theme)
                self.apply_theme()
                for widget in self._styled_widgets:
                    if widget.winfo_exists():
                        self.style.apply_to_widget(widget)
                return True
        return False

    def track_widget(self, widget: tk.Widget):
        """Track a widget for theme updates.

        Args:
            widget: Widget to track
        """
        self._styled_widgets.append(widget)
        self.style.apply_to_widget(widget)

    def get_color(self, key: str) -> str:
        """Get current theme color."""
        return self.theme.get_color(key)

    def get_spacing(self, size: str = "sm") -> int:
        """Get spacing value."""
        return self.theme.get_spacing(size)

    def get_radius(self, size: str = "sm") -> int:
        """Get border radius."""
        return self.theme.get_radius(size)

    def get_font(self, size: str = "base", bold: bool = False, italic: bool = False) -> tuple:
        """Get font tuple."""
        return self.theme.get_font(size, bold, italic)

    def get_mono_font(self, size: str = "base") -> tuple:
        """Get monospace font tuple."""
        return self.theme.get_mono_font(size)


def create_styled_frame(parent: tk.Widget, theme_manager: ThemeManager,
                        card_style: bool = True, **kwargs) -> ttk.Frame:
    """Create a styled frame with theme applied.

    Args:
        parent: Parent widget
        theme_manager: Theme manager instance
        card_style: Whether to apply card styling (border, different bg)
        **kwargs: Additional arguments for ttk.Frame

    Returns:
        Styled ttk.Frame widget
    """
    style = f"{ModernStyle.VARIANT_CARD}.TFrame" if card_style else "TFrame"
    spacing = theme_manager.get_spacing("sm")

    # Add padding if not specified
    if "padding" not in kwargs:
        kwargs["padding"] = spacing

    frame = ttk.Frame(parent, style=style, **kwargs)
    return frame


def create_styled_label(parent: tk.Widget, theme_manager: ThemeManager,
                        variant: str = "", text: str = "", **kwargs) -> ttk.Label:
    """Create a styled label with theme applied.

    Args:
        parent: Parent widget
        theme_manager: Theme manager instance
        variant: Label variant - "", "title", "subtitle", "body", "hint", "mono"
        text: Label text
        **kwargs: Additional arguments for ttk.Label

    Returns:
        Styled ttk.Label widget
    """
    style = f"{variant}.TLabel" if variant else "TLabel"

    if text:
        kwargs["text"] = text

    label = ttk.Label(parent, style=style, **kwargs)
    return label


def create_styled_button(parent: tk.Widget, theme_manager: ThemeManager,
                         variant: str = "", text: str = "", **kwargs) -> ttk.Button:
    """Create a styled button with theme applied.

    Args:
        parent: Parent widget
        theme_manager: Theme manager instance
        variant: Button variant - "", "primary", "danger"
        text: Button text
        **kwargs: Additional arguments for ttk.Button

    Returns:
        Styled ttk.Button widget
    """
    style = f"{variant}.TButton" if variant else "TButton"

    if text:
        kwargs["text"] = text

    # Default padding
    if "padding" not in kwargs:
        spacing = theme_manager.get_spacing("sm")
        kwargs["padding"] = (spacing * 2, spacing)

    button = ttk.Button(parent, style=style, **kwargs)
    return button
