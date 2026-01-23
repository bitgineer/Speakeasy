"""
Modern settings window with tabbed interface and theme support.

This module provides a modern GUI window for application settings.
It features:
- Tabbed interface for organized settings
- Modern card-based design
- Theme support (light/dark mode)
- Improved iconography
- Toggle switches instead of checkboxes

Classes
-------
ModernSettingsWindow
    Modern settings window with tabbed interface.

ModernToggleSwitch
    Custom toggle switch widget for boolean settings.

Notes
-----
Settings are persisted to JSON file and applied immediately where possible.
"""

import tkinter as tk
from tkinter import ttk
import json
from typing import Optional, Callable

from .theme import ThemeManager, create_styled_frame, create_styled_label, create_styled_button
from .icons import IconFactory
from .settings import SETTINGS_FILE, save_settings, clear_history


class ModernToggleSwitch(tk.Canvas):
    """Custom toggle switch widget.

    A modern iOS-style toggle switch for boolean settings.
    """

    def __init__(self, parent, theme_manager: ThemeManager, on_value: bool = False,
                 on_change: Optional[Callable] = None, **kwargs):
        """Initialize toggle switch.

        Args:
            parent: Parent widget
            theme_manager: ThemeManager instance
            on_value: Initial state (True = on, False = off)
            on_change: Callback when state changes
            **kwargs: Additional canvas arguments
        """
        width = kwargs.pop('width', 44)
        height = kwargs.pop('height', 24)

        # Get colors from theme
        c = theme_manager.colors
        bg = parent.cget("bg") if hasattr(parent, "cget") else c["bg_main"]

        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=bg,
            **kwargs
        )

        self.theme_manager = theme_manager
        self.on_change = on_change
        self._on_value = on_value
        self._animating = False

        # Bind click
        self.bind("<Button-1>", self._toggle)
        self.bind("<Return>", self._toggle)
        self.bind("<space>", self._toggle)

        # Draw initial state
        self._draw()

    def _toggle(self, event=None):
        """Toggle the switch state."""
        if not self._animating:
            self._on_value = not self._on_value
            self._draw()
            if self.on_change:
                self.on_change(self._on_value)

    def _draw(self):
        """Draw the toggle switch."""
        self.delete("all")

        c = self.theme_manager.colors
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            w = 44
        if h <= 1:
            h = 24

        # Track color (green when on, gray when off)
        track_color = c["success"] if self._on_value else c["border"]

        # Draw track (rounded rectangle)
        self.create_rectangle(
            2, 2, w - 2, h - 2,
            fill=track_color,
            outline="",
            tags="track"
        )

        # Thumb position
        thumb_x = w - 12 if self._on_value else 4

        # Draw thumb (circle)
        thumb_color = c["bg_card"] if self._on_value else "#FFFFFF"
        self.create_oval(
            thumb_x, 4, thumb_x + 16, h - 4,
            fill=thumb_color,
            outline="",
            tags="thumb"
        )

        # Add shadow effect
        if self._on_value:
            self.create_oval(
                thumb_x + 2, 6, thumb_x + 14, h - 6,
                fill="",
                outline="",
                tags="thumb_shadow"
            )

    @property
    def value(self) -> bool:
        """Get the current value."""
        return self._on_value

    @value.setter
    def value(self, new_value: bool):
        """Set the value."""
        if self._on_value != new_value:
            self._on_value = new_value
            self._draw()

    def get(self) -> bool:
        """Get the current value."""
        return self._on_value


class ModernSettingsWindow:
    """Modern settings window with tabbed interface.

    Features:
    - General settings tab (hotkey, activation mode)
    - Privacy tab (privacy mode, history settings)
    - Appearance tab (theme, font size)
    - About tab (version, info)
    """

    def __init__(self, parent: tk.Tk, theme_manager: ThemeManager,
                 settings, on_hotkey_change: Optional[Callable] = None,
                 on_settings_change: Optional[Callable] = None):
        """Initialize the settings window.

        Args:
            parent: Parent tkinter window
            theme_manager: ThemeManager instance
            settings: Current settings object
            on_hotkey_change: Callback when hotkey changes
            on_settings_change: Callback when any setting changes
        """
        self.parent = parent
        self.theme_manager = theme_manager
        self.settings = settings
        self.on_hotkey_change = on_hotkey_change
        self.on_settings_change = on_settings_change
        self.window = None
        self.icon_factory = IconFactory(theme_manager)

        # Toggle switches
        self.privacy_toggle = None
        self.privacy_status_label = None

    def show(self):
        """Show the settings window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.geometry("650x500")
        self.window.resizable(False, False)

        # Apply theme to window
        self.theme_manager.style.apply_to_widget(self.window)

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        """Build the settings UI."""
        # Main container
        main_frame = create_styled_frame(
            self.window,
            self.theme_manager,
            card_style=False
        )
        main_frame.pack(fill=tk.BOTH, expand=True,
                       padx=self.theme_manager.get_spacing("md"),
                       pady=self.theme_manager.get_spacing("md"))

        # Header
        self._create_header(main_frame)

        # Notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(self.theme_manager.get_spacing("md"), 0))

        # Create tabs
        self._create_general_tab(notebook)
        self._create_privacy_tab(notebook)
        self._create_about_tab(notebook)

        # Footer with close button
        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("md"), 0))

        close_btn = create_styled_button(
            footer,
            self.theme_manager,
            variant="primary",
            text="Close",
            command=self.window.destroy
        )
        close_btn.pack(side=tk.RIGHT)

    def _create_header(self, parent):
        """Create the header section."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        # Settings icon
        icon = self.icon_factory.create(header_frame, "settings", size=28,
                                       color=self.theme_manager.get_color("primary"))
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("sm")))

        # Title
        title = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="title",
            text="Settings"
        )
        title.pack(side=tk.LEFT)

    def _create_general_tab(self, notebook: ttk.Notebook):
        """Create the General settings tab."""
        tab_frame = create_styled_frame(notebook, self.theme_manager, card_style=False)
        tab_frame.pack(fill=tk.BOTH, expand=True)
        tab_frame.columnconfigure(0, weight=1)

        notebook.add(tab_frame, text="  General  ")

        # Scrollable content
        canvas = tk.Canvas(tab_frame, highlightthickness=0,
                          bg=self.theme_manager.get_color("bg_main"))
        scrollbar = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Content sections
        self._create_general_section(scrollable)
        self._create_hotkey_section(scrollable)
        self._create_streaming_section(scrollable)

    def _create_general_section(self, parent):
        """Create general settings section."""
        # Section card
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(self.theme_manager.get_spacing("md"), self.theme_manager.get_spacing("sm")))
        card.columnconfigure(1, weight=1)

        # Section header
        header = create_styled_label(
            card,
            self.theme_manager,
            variant="subtitle",
            text="Current Configuration"
        )
        header.grid(row=0, column=0, columnspan=2,
                   sticky="w", padx=self.theme_manager.get_spacing("sm"),
                   pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        ttk.Separator(card, orient=tk.HORIZONTAL).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )

        # Settings values
        if self.settings:
            settings_items = [
                ("Model", self.settings.model_name),
                ("Device", self.settings.device),
            ]

            for i, (label, value) in enumerate(settings_items):
                row = 2 + i

                # Label
                lbl = create_styled_label(
                    card,
                    self.theme_manager,
                    variant="body",
                    text=f"{label}:"
                )
                lbl.grid(row=row, column=0, sticky="w",
                        padx=self.theme_manager.get_spacing("sm"), pady=self.theme_manager.get_spacing("xs"))

                # Value (mono)
                val_lbl = create_styled_label(
                    card,
                    self.theme_manager,
                    variant="mono",
                    text=value
                )
                val_lbl.grid(row=row, column=1, sticky="w",
                            padx=self.theme_manager.get_spacing("xs"), pady=self.theme_manager.get_spacing("xs"))

        # Note about CLI
        note_frame = tk.Frame(card, bg=self.theme_manager.get_color("warning_bg"), padx=12, pady=8)
        note_frame.grid(row=10, column=0, columnspan=2, sticky="ew",
                       padx=self.theme_manager.get_spacing("sm"), pady=(self.theme_manager.get_spacing("sm"), 0))

        note_label = tk.Label(
            note_frame,
            text="To change model, device, or language settings, use the CLI: faster-whisper-hotkey",
            fg=self.theme_manager.get_color("fg_secondary"),
            bg=self.theme_manager.get_color("warning_bg"),
            font=self.theme_manager.get_font("sm")
        )
        note_label.pack()

    def _create_hotkey_section(self, parent):
        """Create hotkey configuration section."""
        # Section card
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(0, self.theme_manager.get_spacing("md")))

        # Section header with icon
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        icon = self.icon_factory.create(header_frame, "keyboard", size=20,
                                       color=self.theme_manager.get_color("primary"))
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        header = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="subtitle",
            text="Hotkey Configuration"
        )
        header.pack(side=tk.LEFT)

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        # Current hotkey display
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                          pady=self.theme_manager.get_spacing("sm"))

        if self.settings:
            hotkey = self.settings.hotkey.upper() if self.settings.hotkey else "Not Set"
            mode = self.settings.activation_mode.title() if self.settings.activation_mode else "Hold"

            # Hotkey row
            hotkey_row = ttk.Frame(content_frame)
            hotkey_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("xs")))

            create_styled_label(hotkey_row, self.theme_manager, text="Recording Hotkey:").pack(side=tk.LEFT)

            hotkey_display = tk.Label(
                hotkey_row,
                text=hotkey,
                font=self.theme_manager.get_mono_font("lg"),
                bg=self.theme_manager.get_color("primary_light"),
                fg=self.theme_manager.get_color("primary"),
                padx=self.theme_manager.get_spacing("sm"),
                pady=self.theme_manager.get_spacing("xs")
            )
            hotkey_display.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("sm"))

            # Mode row
            mode_row = ttk.Frame(content_frame)
            mode_row.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("xs"), 0))

            create_styled_label(mode_row, self.theme_manager, text="Activation Mode:").pack(side=tk.LEFT)

            mode_display = tk.Label(
                mode_row,
                text=mode,
                font=self.theme_manager.get_font("base", bold=True),
                fg=self.theme_manager.get_color("fg_secondary")
            )
            mode_display.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("sm"))

        # Configure button
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                      pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("sm")))

        configure_btn = create_styled_button(
            btn_frame,
            self.theme_manager,
            variant="primary",
            text="Configure Hotkey...",
            command=self._configure_hotkey
        )
        configure_btn.pack(side=tk.LEFT)

    def _create_streaming_section(self, parent):
        """Create streaming transcription settings section."""
        # Section card
        card = create_styled_frame(parent, self.theme_manager, card_style=True)
        card.pack(fill=tk.X, padx=self.theme_manager.get_spacing("md"),
                  pady=(0, self.theme_manager.get_spacing("md")))

        # Section header with icon
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        icon = self.icon_factory.create(header_frame, "bolt", size=20,
                                       color=self.theme_manager.get_color("primary"))
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        header = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="subtitle",
            text="Streaming Transcription"
        )
        header.pack(side=tk.LEFT)

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        # Content frame
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                          pady=self.theme_manager.get_spacing("sm"))

        # Get current settings
        enable_streaming = getattr(self.settings, 'enable_streaming', False) if self.settings else False
        auto_copy = getattr(self.settings, 'auto_copy_on_release', True) if self.settings else True
        confidence_threshold = getattr(self.settings, 'confidence_threshold', 0.5) if self.settings else 0.5

        # Enable streaming toggle row
        toggle_row = ttk.Frame(content_frame)
        toggle_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        create_styled_label(
            toggle_row,
            self.theme_manager,
            variant="body",
            text="Enable real-time preview"
        ).pack(side=tk.LEFT)

        self.streaming_toggle = ModernToggleSwitch(
            toggle_row,
            self.theme_manager,
            on_value=enable_streaming,
            on_change=self._toggle_streaming
        )
        self.streaming_toggle.pack(side=tk.RIGHT)

        # Description
        desc_text = (
            "Show transcription results in real-time as you speak.\n"
            "A floating preview window appears during recording with\n"
            "confidence-based text highlighting."
        )
        desc_label = create_styled_label(
            content_frame,
            self.theme_manager,
            variant="body",
            text=desc_text
        )
        desc_label.pack(anchor=tk.W, pady=(0, self.theme_manager.get_spacing("sm")))

        # Auto-copy toggle row
        auto_copy_row = ttk.Frame(content_frame)
        auto_copy_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        create_styled_label(
            auto_copy_row,
            self.theme_manager,
            variant="body",
            text="Auto-copy on release"
        ).pack(side=tk.LEFT)

        self.auto_copy_toggle = ModernToggleSwitch(
            auto_copy_row,
            self.theme_manager,
            on_value=auto_copy,
            on_change=self._toggle_auto_copy
        )
        self.auto_copy_toggle.pack(side=tk.RIGHT)

        # Confidence threshold row
        threshold_row = ttk.Frame(content_frame)
        threshold_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        create_styled_label(
            threshold_row,
            self.theme_manager,
            variant="body",
            text="Low confidence threshold"
        ).pack(side=tk.LEFT)

        # Confidence threshold slider
        self.confidence_slider = ttk.Scale(
            threshold_row,
            from_=0.0,
            to=1.0,
            value=confidence_threshold,
            command=self._on_confidence_change
        )
        self.confidence_slider.pack(side=tk.LEFT, padx=self.theme_manager.get_spacing("sm"))

        self.confidence_value_label = create_styled_label(
            threshold_row,
            self.theme_manager,
            variant="mono",
            text=f"{confidence_threshold:.0%}"
        )
        self.confidence_value_label.pack(side=tk.LEFT)

        # Note about confidence
        note_frame = tk.Frame(
            content_frame,
            bg=self.theme_manager.get_color("info_bg"),
            padx=self.theme_manager.get_spacing("sm"),
            pady=self.theme_manager.get_spacing("xs")
        )
        note_frame.pack(fill=tk.X, pady=(self.theme_manager.get_spacing("xs"), 0))

        note_label = create_styled_label(
            note_frame,
            self.theme_manager,
            variant="sm",
            text="Text below this confidence level will be highlighted in red."
        )
        note_label.pack()

    def _toggle_streaming(self, enabled: bool):
        """Toggle streaming mode setting."""
        self._update_setting("enable_streaming", enabled)

    def _toggle_auto_copy(self, enabled: bool):
        """Toggle auto-copy on release setting."""
        self._update_setting("auto_copy_on_release", enabled)

    def _on_confidence_change(self, value):
        """Handle confidence threshold slider change."""
        threshold = float(value)
        if self.confidence_value_label:
            self.confidence_value_label.configure(text=f"{threshold:.0%}")
        # Debounce save
        if hasattr(self, '_confidence_debounce_id'):
            self.window.after_cancel(self._confidence_debounce_id)
        self._confidence_debounce_id = self.window.after(500, lambda: self._update_setting("confidence_threshold", threshold))

    def _update_setting(self, key: str, value):
        """Update a single setting and save."""
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}

        data[key] = value
        save_settings(data)

        # Notify callback
        if self.on_settings_change:
            self.on_settings_change()

    def _create_privacy_tab(self, notebook: ttk.Notebook):
        """Create the Privacy settings tab."""
        tab_frame = create_styled_frame(notebook, self.theme_manager, card_style=False)
        tab_frame.pack(fill=tk.BOTH, expand=True)

        notebook.add(tab_frame, text="  Privacy  ")

        # Privacy card
        card = create_styled_frame(tab_frame, self.theme_manager, card_style=True)
        card.pack(fill=tk.BOTH, expand=True,
                  padx=self.theme_manager.get_spacing("md"),
                  pady=self.theme_manager.get_spacing("md"))

        # Header with shield icon
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"),
                         pady=(self.theme_manager.get_spacing("sm"), self.theme_manager.get_spacing("xs")))

        icon = self.icon_factory.create(header_frame, "shield", size=24,
                                       color=self.theme_manager.get_color("primary"))
        icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        header = create_styled_label(
            header_frame,
            self.theme_manager,
            variant="subtitle",
            text="Privacy Mode"
        )
        header.pack(side=tk.LEFT)

        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=self.theme_manager.get_spacing("sm"))

        # Content
        content_frame = ttk.Frame(card)
        content_frame.pack(fill=tk.BOTH, expand=True,
                          padx=self.theme_manager.get_spacing("sm"),
                          pady=self.theme_manager.get_spacing("sm"))

        # Toggle row
        toggle_row = ttk.Frame(content_frame)
        toggle_row.pack(fill=tk.X, pady=(0, self.theme_manager.get_spacing("sm")))

        create_styled_label(
            toggle_row,
            self.theme_manager,
            variant="subtitle",
            text="Enable Privacy Mode"
        ).pack(side=tk.LEFT)

        # Get current privacy mode
        privacy_mode = getattr(self.settings, 'privacy_mode', False) if self.settings else False

        self.privacy_toggle = ModernToggleSwitch(
            toggle_row,
            self.theme_manager,
            on_value=privacy_mode,
            on_change=self._toggle_privacy_mode
        )
        self.privacy_toggle.pack(side=tk.RIGHT)

        # Description
        desc_text = (
            "When enabled, no transcription history is saved and audio is\n"
            "deleted immediately after processing. A shield icon appears\n"
            "in the system tray to confirm privacy mode is active."
        )
        desc_label = create_styled_label(
            content_frame,
            self.theme_manager,
            variant="body",
            text=desc_text
        )
        desc_label.pack(anchor=tk.W, pady=(0, self.theme_manager.get_spacing("sm")))

        # Status indicator
        status_frame = tk.Frame(
            content_frame,
            bg=self.theme_manager.get_color("success_bg" if not privacy_mode else "error_bg"),
            padx=self.theme_manager.get_spacing("sm"),
            pady=self.theme_manager.get_spacing("sm")
        )
        status_frame.pack(fill=tk.X)

        status_icon = self.icon_factory.create(
            status_frame,
            "check" if not privacy_mode else "warning",
            size=16,
            color=self.theme_manager.get_color("success" if not privacy_mode else "error")
        )
        status_icon.configure(bg=status_frame.cget("bg"))
        status_icon.pack(side=tk.LEFT, padx=(0, self.theme_manager.get_spacing("xs")))

        status_text = "History is being saved" if not privacy_mode else "No data being stored"
        self.privacy_status_label = tk.Label(
            status_frame,
            text=status_text,
            fg=self.theme_manager.get_color("success" if not privacy_mode else "error"),
            bg=status_frame.cget("bg"),
            font=self.theme_manager.get_font("sm", bold=True)
        )
        self.privacy_status_label.pack(side=tk.LEFT)

    def _create_about_tab(self, notebook: ttk.Notebook):
        """Create the About tab."""
        tab_frame = create_styled_frame(notebook, self.theme_manager, card_style=False)
        tab_frame.pack(fill=tk.BOTH, expand=True)

        notebook.add(tab_frame, text="  About  ")

        # Center content
        center_frame = ttk.Frame(tab_frame)
        center_frame.pack(expand=True, fill=tk.BOTH,
                         padx=self.theme_manager.get_spacing("md"),
                         pady=self.theme_manager.get_spacing("md"))

        # App icon/name
        icon_frame = ttk.Frame(center_frame)
        icon_frame.pack(pady=self.theme_manager.get_spacing("lg"))

        # Mic icon
        icon = self.icon_factory.create(icon_frame, "microphone", size=48,
                                       color=self.theme_manager.get_color("primary"))
        icon.pack()

        # App name
        name_label = create_styled_label(
            icon_frame,
            self.theme_manager,
            variant="title",
            text="Faster Whisper Hotkey"
        )
        name_label.pack(pady=(self.theme_manager.get_spacing("sm"), 0))

        # Version
        from . import __version__
        version_label = create_styled_label(
            icon_frame,
            self.theme_manager,
            variant="body",
            text=f"Version {__version__}"
        )
        version_label.pack()

        # Description
        desc_frame = create_styled_frame(center_frame, self.theme_manager, card_style=True)
        desc_frame.pack(fill=tk.X, pady=self.theme_manager.get_spacing("lg"))

        desc_text = (
            "A push-to-talk transcription tool using faster-whisper.\n\n"
            "Press your hotkey while speaking to transcribe audio.\n"
            "Transcribed text is automatically copied to your clipboard."
        )
        desc_label = create_styled_label(
            desc_frame,
            self.theme_manager,
            variant="body",
            text=desc_text
        )
        desc_label.pack(padx=self.theme_manager.get_spacing("sm"),
                       pady=self.theme_manager.get_spacing("sm"))

    def _toggle_privacy_mode(self, enabled: bool):
        """Toggle privacy mode setting."""
        # Load current settings as dict
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}

        data["privacy_mode"] = enabled
        save_settings(data)

        # Update status display
        if self.privacy_status_label:
            status_text = "History is being saved" if not enabled else "No data being stored"
            color = self.theme_manager.get_color("success" if not enabled else "error")
            bg_color = self.theme_manager.get_color("success_bg" if not enabled else "error_bg")

            self.privacy_status_label.configure(text=status_text, fg=color)
            self.privacy_status_label.master.configure(bg=bg_color)

        # Clear history if enabling
        if enabled:
            clear_history()

        # Notify callback
        if self.on_settings_change:
            self.on_settings_change()

    def _configure_hotkey(self):
        """Open hotkey configuration dialog."""
        if self.on_hotkey_change:
            self.on_hotkey_change()

    def _center_window(self):
        """Center the window on parent."""
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - self.window.winfo_width()) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")


def show_modern_settings(parent, theme_manager: ThemeManager, settings,
                         on_hotkey_change=None, on_settings_change=None) -> ModernSettingsWindow:
    """Show the modern settings window.

    Args:
        parent: Parent tkinter window
        theme_manager: ThemeManager instance
        settings: Current settings object
        on_hotkey_change: Callback when hotkey changes
        on_settings_change: Callback when any setting changes

    Returns:
        ModernSettingsWindow instance
    """
    window = ModernSettingsWindow(
        parent, theme_manager, settings,
        on_hotkey_change, on_settings_change
    )
    window.show()
    return window
