"""
Settings panel GUI with organized tabs using tkinter.

This module provides a comprehensive settings management interface organized
into logical tabs for General, Hotkeys, Audio, Post-processing, Privacy, and
Advanced settings. It includes a quick search feature to find settings quickly.

Classes
-------
SettingsPanel
    Main settings panel with tabbed interface and search functionality.

Functions
---------
show_settings_panel
    Convenience function to show the settings panel.

Notes
-----
Uses ttk.Notebook for tabbed interface and integrates with settings
module for persistence. Settings that require transcriber restart will
notify the user accordingly.
"""

import logging
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional, Dict, List, Any
import json
import os

from .settings import (
    load_settings, save_settings, Settings,
    SETTINGS_FILE, clear_history
)
from .hotkey_dialog import show_hotkey_dialog

logger = logging.getLogger(__name__)


# Constants for settings that may need new fields
DEFAULT_AUDIO_GAIN = 1.0
DEFAULT_NOISE_SUPPRESSION = False
DEFAULT_FILLER_REMOVAL = False
DEFAULT_PUNCTUATION = False
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_HISTORY_RETENTION_DAYS = 30


def get_available_languages() -> List[tuple]:
    """Get list of available languages for dropdown."""
    # Common languages with their codes
    languages = [
        ("Auto-detect", "auto"),
        ("English", "en"),
        ("Spanish", "es"),
        ("French", "fr"),
        ("German", "de"),
        ("Italian", "it"),
        ("Portuguese", "pt"),
        ("Dutch", "nl"),
        ("Russian", "ru"),
        ("Chinese", "zh"),
        ("Japanese", "ja"),
        ("Korean", "ko"),
        ("Arabic", "ar"),
        ("Hindi", "hi"),
        ("Turkish", "tr"),
        ("Polish", "pl"),
        ("Swedish", "sv"),
        ("Danish", "da"),
        ("Norwegian", "no"),
        ("Finnish", "fi"),
    ]
    return languages


def get_available_models() -> Dict[str, List[str]]:
    """Get available models by type."""
    return {
        "Whisper": ["tiny", "base", "small", "medium", "large-v3", "large-v2"],
        "Parakeet": ["ctc_en_rnnt", "rnnt_en"],
        "Canary": ["1.0"],
        "Voxtral": ["small"],
    }


def get_available_devices() -> List[str]:
    """Get available compute devices."""
    return ["CPU", "CUDA", "Auto"]


def get_compute_types() -> Dict[str, List[str]]:
    """Get available compute types by device."""
    return {
        "CUDA": ["float16", "int8", "int8_float16", "float32"],
        "CPU": ["int8", "float32"],
        "Auto": ["default"],
    }


class SettingsPanel:
    """Main settings panel with tabbed interface."""

    def __init__(
        self,
        parent=None,
        on_settings_changed: Callable = None,
        on_restart_required: Callable = None,
        on_theme_changed: Callable = None
    ):
        """
        Initialize the settings panel.

        Args:
            parent: Parent window
            on_settings_changed: Callback when settings are changed
            on_restart_required: Callback when transcriber restart is needed
            on_theme_changed: Callback when theme is changed
        """
        self.parent = parent or tk.Tk()
        self.on_settings_changed = on_settings_changed
        self.on_restart_required = on_restart_required
        self.on_theme_changed = on_theme_changed
        self.window = None
        self.settings = None
        self.search_var = None
        self.notebook = None
        self.setting_widgets = {}  # Map setting path to widget for search
        self.restart_required = False

        # Setting variables (for reading current values)
        self.vars = {
            # General
            "model_type": None,
            "model_name": None,
            "device": None,
            "compute_type": None,
            "language": None,
            "theme_mode": None,

            # Hotkeys
            "hotkey": None,
            "activation_mode": None,
            "secondary_hotkey": None,
            "per_app_hotkeys": None,

            # Audio
            "audio_gain": None,
            "noise_suppression": None,

            # Post-processing
            "filler_removal": None,
            "punctuation": None,

            # Privacy
            "privacy_mode": None,
            "history_max_items": None,
            "history_retention_days": None,
            "auto_clear_history": None,
            "history_confirm_clear": None,
            "history_backup_enabled": None,

            # Advanced
            "log_level": None,
            "debug_mode": None,
        }

    def show(self):
        """Show the settings panel window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return

        # Load current settings
        self.settings = load_settings()
        if not self.settings:
            # Create default settings
            self.settings = Settings(
                device_name="default",
                model_type="whisper",
                model_name="large-v3",
                compute_type="default",
                device="cpu",
                language="en",
            )

        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.geometry("650x550")
        self.window.minsize(600, 500)

        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        self._build_ui()
        self._load_settings_to_ui()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _build_ui(self):
        """Build the UI components."""
        main_frame = ttk.Frame(self.window, padding=0)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Header with title and search
        header_frame = ttk.Frame(main_frame, padding=(15, 15, 15, 10))
        header_frame.grid(row=0, column=0, sticky="ew")

        # Title
        ttk.Label(
            header_frame,
            text="Settings",
            font=("", 16, "bold")
        ).pack(side=tk.LEFT)

        # Search box
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)

        ttk.Label(
            search_frame,
            text="Search:",
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=25
        )
        search_entry.pack(side=tk.LEFT)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Create tabs
        self._create_general_tab()
        self._create_hotkeys_tab()
        self._create_audio_tab()
        self._create_post_processing_tab()
        self._create_privacy_tab()
        self._create_advanced_tab()

        # Footer with buttons
        footer_frame = ttk.Frame(main_frame, padding=(15, 10, 15, 15))
        footer_frame.grid(row=2, column=0, sticky="ew")

        # Restart warning label (hidden by default)
        self.restart_label = ttk.Label(
            footer_frame,
            text="Some changes require transcriber restart to take effect",
            foreground="#FF9800",
            font=("", 9, "italic")
        )
        # Don't pack initially - only show when needed

        # Buttons
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(side=tk.RIGHT)

        self.save_btn = ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=10
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=10
        ).pack(side=tk.LEFT)

        # Bind keyboard shortcuts
        self.window.bind("<Escape>", lambda e: self._cancel())

    def _create_scrollable_frame(self, parent) -> tuple:
        """Create a scrollable frame for tab content.

        Returns:
            Tuple of (canvas, frame, scrollbar)
        """
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_frame_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        frame.bind("<Configure>", on_frame_configure)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return canvas, frame

    def _create_setting_row(
        self,
        parent,
        label: str,
        widget_type: str,
        setting_key: str,
        tab_name: str = "",
        options: List[Any] = None,
        help_text: str = "",
        row: int = None,
        **kwargs
    ) -> Any:
        """Create a standardized setting row with label and widget.

        Args:
            parent: Parent frame
            label: Setting label text
            widget_type: Type of widget ("entry", "combobox", "check", "scale",
                          "spinbox", "radiogroup")
            setting_key: Key for self.vars
            tab_name: Name of the tab for search indexing
            options: Options for combobox/radiogroup
            help_text: Help text to display below the setting
            row: Grid row number (auto-increment if None)
            **kwargs: Additional arguments for the widget

        Returns:
            The created widget
        """
        if row is None:
            row = parent.grid_size()[1]

        # Label
        if label:
            ttk.Label(parent, text=label).grid(
                row=row, column=0, sticky=tk.W, padx=(20, 10), pady=(8, 0)
            )

        # Widget frame
        widget_frame = ttk.Frame(parent)
        widget_frame.grid(row=row, column=1, sticky=tk.EW, padx=(0, 20), pady=(8, 0))

        widget = None
        var = kwargs.get("variable")

        if widget_type == "entry":
            widget = ttk.Entry(
                widget_frame,
                textvariable=var,
                width=kwargs.get("width", 25)
            )
            widget.pack(fill=tk.X)

        elif widget_type == "combobox":
            widget = ttk.Combobox(
                widget_frame,
                textvariable=var,
                values=options or [],
                state="readonly",
                width=kwargs.get("width", 23)
            )
            widget.pack(fill=tk.X)

        elif widget_type == "check":
            widget = ttk.Checkbutton(
                widget_frame,
                text=kwargs.get("check_text", ""),
                variable=var
            )
            widget.pack(anchor=tk.W)

        elif widget_type == "scale":
            widget = ttk.Scale(
                widget_frame,
                from_=kwargs.get("from_", 0),
                to=kwargs.get("to", 100),
                variable=var,
                orient=tk.HORIZONTAL,
                command=kwargs.get("command", None)
            )
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Value label
            if kwargs.get("show_value", True):
                value_label = ttk.Label(widget_frame, text="")
                value_label.pack(side=tk.LEFT, padx=(5, 0))

                def update_label(*args):
                    value = var.get()
                    if kwargs.get("value_format"):
                        value_label.config(text=kwargs["value_format"].format(value))
                    else:
                        value_label.config(text=str(value))

                var.trace("w", update_label)
                update_label()

        elif widget_type == "spinbox":
            from_ = kwargs.get("from_", 0)
            to = kwargs.get("to", 100)
            widget = ttk.Spinbox(
                widget_frame,
                from_=from_,
                to=to,
                textvariable=var,
                width=10
            )
            widget.pack(side=tk.LEFT)

        elif widget_type == "radiogroup":
            widget = widget_frame  # Return frame for radiogroup
            for i, (value, text) in enumerate(options):
                ttk.Radiobutton(
                    widget_frame,
                    text=text,
                    variable=var,
                    value=value
                ).pack(anchor=tk.W, pady=(0, 2) if i < len(options) - 1 else 0)

        # Store widget for search
        search_key = f"{tab_name}/{setting_key}" if tab_name else setting_key
        self.setting_widgets[search_key] = {
            "widget": widget,
            "label": label,
            "tab": tab_name,
            "help_text": help_text,
            "row": row,
        }

        # Help text
        if help_text:
            help_label = ttk.Label(
                parent,
                text=help_text,
                foreground="gray",
                font=("", 8),
                wraplength=400
            )
            help_label.grid(
                row=row + 1, column=0, columnspan=2,
                sticky=tk.W, padx=(20, 20), pady=(0, 8)
            )
            # Store help label reference
            self.setting_widgets[search_key]["help_label"] = help_label

        parent.columnconfigure(1, weight=1)

        return widget

    def _create_section_header(self, parent, title: str, row: int = None) -> int:
        """Create a section header with separator.

        Returns:
            The next available row number
        """
        if row is None:
            row = parent.grid_size()[1]

        # Add some spacing first
        ttk.Label(parent, text="", height=1).grid(row=row, column=0, columnspan=2)

        # Section label
        ttk.Label(
            parent,
            text=title,
            font=("", 10, "bold"),
            foreground="#2196F3"
        ).grid(row=row + 1, column=0, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(5, 0))

        # Separator
        separator = ttk.Separator(parent, orient=tk.HORIZONTAL)
        separator.grid(row=row + 2, column=0, columnspan=2, sticky=tk.EW, padx=(20, 20), pady=(5, 10))

        return row + 3

    def _create_general_tab(self):
        """Create the General settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  General  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["model_type"] = tk.StringVar()
        self.vars["model_name"] = tk.StringVar()
        self.vars["device"] = tk.StringVar()
        self.vars["compute_type"] = tk.StringVar()
        self.vars["language"] = tk.StringVar()
        self.vars["theme_mode"] = tk.StringVar()

        row = 0

        # Model Configuration Section
        row = self._create_section_header(content_frame, "Model Configuration", row)

        # Model Type
        model_types = list(get_available_models().keys())
        self._create_setting_row(
            content_frame,
            "Model Type:",
            "combobox",
            "model_type",
            "General",
            options=model_types,
            help_text="Select the ASR model engine to use for transcription.",
            row=row
        )
        row += 2

        # Model Name (dynamic based on type)
        self._create_setting_row(
            content_frame,
            "Model Name:",
            "combobox",
            "model_name",
            "General",
            options=get_available_models()["Whisper"],
            help_text="Specific model size/variant. Larger models are more accurate but slower.",
            row=row
        )

        # Update model names when model type changes
        def on_model_type_change(*args):
            new_type = self.vars["model_type"].get()
            models = get_available_models().get(new_type, [])
            # Find the model_name combobox widget
            widget_info = self.setting_widgets.get("General/model_name")
            if widget_info and widget_info["widget"]:
                widget_info["widget"]["values"] = models
                if models and not self.vars["model_name"].get():
                    self.vars["model_name"].set(models[0])

        self.vars["model_type"].trace("w", on_model_type_change)

        row += 2

        # Device Section
        row = self._create_section_header(content_frame, "Compute Device", row)

        # Device selection
        self._create_setting_row(
            content_frame,
            "Device:",
            "combobox",
            "device",
            "General",
            options=get_available_devices(),
            help_text="CPU is slower but works everywhere. CUDA (GPU) is much faster if available.",
            row=row
        )
        row += 2

        # Compute type
        self._create_setting_row(
            content_frame,
            "Compute Type:",
            "combobox",
            "compute_type",
            "General",
            options=["default", "float16", "int8", "float32"],
            help_text="Lower precision (int8) uses less memory. float16 is best for GPU.",
            row=row
        )
        row += 2

        # Language Section
        row = self._create_section_header(content_frame, "Language Settings", row)

        # Language selection
        self._create_setting_row(
            content_frame,
            "Language:",
            "combobox",
            "language",
            "General",
            options=[code for _, code in get_available_languages()],
            help_text="Select 'Auto-detect' to automatically identify the language being spoken.",
            row=row
        )
        row += 2

        # Appearance Section
        row = self._create_section_header(content_frame, "Appearance", row)

        # Theme selection
        self._create_setting_row(
            content_frame,
            "Theme:",
            "combobox",
            "theme_mode",
            "General",
            options=["System", "Light", "Dark"],
            help_text="Choose the application theme. System follows your OS preference.",
            row=row
        )
        row += 2

    def _create_hotkeys_tab(self):
        """Create the Hotkeys settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Hotkeys  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["hotkey"] = tk.StringVar()
        self.vars["activation_mode"] = tk.StringVar()
        self.vars["secondary_hotkey"] = tk.StringVar()
        self.vars["per_app_hotkeys"] = tk.BooleanVar(value=False)

        row = 0

        # Primary Hotkey Section
        row = self._create_section_header(content_frame, "Primary Hotkey", row)

        # Hotkey display and capture button
        ttk.Label(content_frame, text="Primary Hotkey:").grid(
            row=row, column=0, sticky=tk.W, padx=(20, 10), pady=(8, 0)
        )

        hotkey_frame = ttk.Frame(content_frame)
        hotkey_frame.grid(row=row, column=1, sticky=tk.EW, padx=(0, 20), pady=(8, 0))

        self.hotkey_display_var = tk.StringVar()
        self.hotkey_display_label = ttk.Label(
            hotkey_frame,
            textvariable=self.hotkey_display_var,
            font=("Consolas", 11)
        )
        self.hotkey_display_label.pack(side=tk.LEFT)

        ttk.Button(
            hotkey_frame,
            text="Change...",
            command=self._change_primary_hotkey,
            width=12
        ).pack(side=tk.LEFT, padx=(10, 0))

        content_frame.columnconfigure(1, weight=1)
        row += 1

        ttk.Label(
            content_frame,
            text="Press this key combination to start/stop recording",
            foreground="gray",
            font=("", 8)
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(0, 8))
        row += 2

        # Activation Mode Section
        row = self._create_section_header(content_frame, "Activation Mode", row)

        self._create_setting_row(
            content_frame,
            None,  # No label, using radiogroup
            "radiogroup",
            "activation_mode",
            "Hotkeys",
            options=[
                ("hold", "Hold-to-talk (hold key while speaking)"),
                ("toggle", "Toggle (press to start, press again to stop)")
            ],
            help_text="Hold mode requires holding the hotkey. Toggle mode toggles recording on/off.",
            row=row
        )
        row += 2

        # Secondary Hotkey Section
        row = self._create_section_header(content_frame, "Secondary Hotkey", row)

        ttk.Label(content_frame, text="Secondary Hotkey:").grid(
            row=row, column=0, sticky=tk.W, padx=(20, 10), pady=(8, 0)
        )

        sec_hotkey_frame = ttk.Frame(content_frame)
        sec_hotkey_frame.grid(row=row, column=1, sticky=tk.EW, padx=(0, 20), pady=(8, 0))

        self.sec_hotkey_display_var = tk.StringVar()
        ttk.Label(
            sec_hotkey_frame,
            textvariable=self.sec_hotkey_display_var,
            font=("Consolas", 11)
        ).pack(side=tk.LEFT)

        ttk.Button(
            sec_hotkey_frame,
            text="Change...",
            command=self._change_secondary_hotkey,
            width=12
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(
            sec_hotkey_frame,
            text="Clear",
            command=self._clear_secondary_hotkey,
            width=8
        ).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(
            content_frame,
            text="Optional: Additional hotkey for the same function",
            foreground="gray",
            font=("", 8)
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(0, 8))
        row += 2

        # Per-App Hotkeys Section
        row = self._create_section_header(content_frame, "Per-Application Hotkeys", row)

        self._create_setting_row(
            content_frame,
            "Enable per-app hotkeys:",
            "check",
            "per_app_hotkeys",
            "Hotkeys",
            help_text="Use different hotkeys for different applications. Configure in the Shortcuts panel.",
            check_text="Enable application-specific hotkey overrides",
            row=row
        )

    def _create_audio_tab(self):
        """Create the Audio settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Audio  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["audio_gain"] = tk.DoubleVar(value=DEFAULT_AUDIO_GAIN)
        self.vars["noise_suppression"] = tk.BooleanVar(value=DEFAULT_NOISE_SUPPRESSION)
        self.vars["input_device"] = tk.StringVar(value="default")

        row = 0

        # Input Device Section
        row = self._create_section_header(content_frame, "Input Device", row)

        # Get available audio devices
        devices = self._get_audio_devices()
        device_options = ["Default"] + devices

        self._create_setting_row(
            content_frame,
            "Microphone:",
            "combobox",
            "input_device",
            "Audio",
            options=device_options,
            help_text="Select which microphone to use for recording.",
            row=row
        )
        row += 2

        # Audio Enhancement Section
        row = self._create_section_header(content_frame, "Audio Enhancement", row)

        # Audio gain
        self._create_setting_row(
            content_frame,
            "Audio Gain:",
            "scale",
            "audio_gain",
            "Audio",
            from_=0.5,
            to=2.0,
            value_format="x{:.2f}",
            help_text="Boost or reduce microphone volume. 1.0 is normal level.",
            row=row
        )
        row += 2

        # Noise suppression
        self._create_setting_row(
            content_frame,
            None,
            "check",
            "noise_suppression",
            "Audio",
            help_text="Reduce background noise from audio input (requires additional processing).",
            check_text="Enable noise suppression",
            row=row
        )

    def _create_post_processing_tab(self):
        """Create the Post-processing settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Post-Processing  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["filler_removal"] = tk.BooleanVar(value=DEFAULT_FILLER_REMOVAL)
        self.vars["punctuation"] = tk.BooleanVar(value=DEFAULT_PUNCTUATION)
        self.vars["capitalization"] = tk.BooleanVar(value=True)

        row = 0

        # Text Enhancement Section
        row = self._create_section_header(content_frame, "Text Enhancement", row)

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "capitalization",
            "Post-processing",
            help_text="Automatically capitalize the first letter of sentences and proper nouns.",
            check_text="Enable automatic capitalization",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "filler_removal",
            "Post-processing",
            help_text="Remove common filler words like 'um', 'uh', 'like', etc.",
            check_text="Enable filler word removal",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "punctuation",
            "Post-processing",
            help_text="Add punctuation to transcribed text for better readability.",
            check_text="Enable automatic punctuation",
            row=row
        )

        # Note about post-processing
        row = content_frame.grid_size()[1] + 1
        note_frame = ttk.Frame(content_frame, relief=tk.GROOVE, padding=10)
        note_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=(20, 20), pady=(20, 10))

        ttk.Label(
            note_frame,
            text="Note: Post-processing features require additional processing time.",
            foreground="#FF9800",
            font=("", 9, "italic")
        ).pack(anchor=tk.W)

    def _create_privacy_tab(self):
        """Create the Privacy settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Privacy  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["privacy_mode"] = tk.BooleanVar(value=False)
        self.vars["history_max_items"] = tk.IntVar(value=1000)
        self.vars["history_retention_days"] = tk.IntVar(value=DEFAULT_HISTORY_RETENTION_DAYS)
        self.vars["auto_clear_history"] = tk.BooleanVar(value=False)
        self.vars["history_confirm_clear"] = tk.BooleanVar(value=True)
        self.vars["history_backup_enabled"] = tk.BooleanVar(value=False)

        row = 0

        # Privacy Mode Section
        row = self._create_section_header(content_frame, "Privacy Mode", row)

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "privacy_mode",
            "Privacy",
            help_text="When enabled, no transcription history is saved and audio is deleted immediately after processing.",
            check_text="Enable privacy mode (no data stored)",
            row=row
        )
        row += 2

        # Privacy status indicator
        status_frame = ttk.Frame(content_frame)
        status_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=(20, 20), pady=(0, 10))

        self.privacy_status_label = ttk.Label(
            status_frame,
            text="Status: OFF - History is saved",
            foreground="#4CAF50",
            font=("", 9, "bold")
        )
        self.privacy_status_label.pack(anchor=tk.W)

        # Update status when privacy mode changes
        def on_privacy_change(*args):
            is_private = self.vars["privacy_mode"].get()
            self.privacy_status_label.config(
                text=f"Status: {'ACTIVE - No data being stored' if is_private else 'OFF - History is saved'}",
                foreground="#F44336" if is_private else "#4CAF50"
            )
            # Disable other privacy options when private mode is on
            state = tk.DISABLED if is_private else tk.NORMAL
            # We'll update the widgets in _load_settings_to_ui

        self.vars["privacy_mode"].trace("w", on_privacy_change)
        row += 2

        # History Settings Section
        row = self._create_section_header(content_frame, "History Settings", row)

        self._create_setting_row(
            content_frame,
            "Max history items:",
            "spinbox",
            "history_max_items",
            "Privacy",
            from_=5,
            to=10000,
            help_text="Maximum number of transcriptions to keep in history.",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            "Retention days:",
            "spinbox",
            "history_retention_days",
            "Privacy",
            from_=1,
            to=365,
            help_text="Automatically remove history entries older than this many days.",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "auto_clear_history",
            "Privacy",
            help_text="Automatically clear all history when closing the application.",
            check_text="Clear history on exit",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "history_confirm_clear",
            "Privacy",
            help_text="Show confirmation dialog before clearing history.",
            check_text="Confirm before clearing history",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "history_backup_enabled",
            "Privacy",
            help_text="Automatically backup history before clearing.",
            check_text="Auto-backup before clearing",
            row=row
        )
        row += 2

        # Action buttons
        action_frame = ttk.Frame(content_frame)
        action_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=(20, 20), pady=(10, 10))

        ttk.Button(
            action_frame,
            text="Clear History Now",
            command=self._clear_history,
            width=20
        ).pack(side=tk.LEFT)

        ttk.Button(
            action_frame,
            text="Export History",
            command=self._export_history,
            width=20
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(
            action_frame,
            text="Backup History",
            command=self._backup_history,
            width=20
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(
            action_frame,
            text="Restore History",
            command=self._restore_history,
            width=20
        ).pack(side=tk.LEFT, padx=(10, 0))

    def _create_advanced_tab(self):
        """Create the Advanced settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  Advanced  ")

        _, content_frame = self._create_scrollable_frame(tab)

        # Initialize variables
        self.vars["log_level"] = tk.StringVar(value=DEFAULT_LOG_LEVEL)
        self.vars["debug_mode"] = tk.BooleanVar(value=False)
        self.vars["cli_path"] = tk.StringVar(value="")

        row = 0

        # Logging Section
        row = self._create_section_header(content_frame, "Logging", row)

        self._create_setting_row(
            content_frame,
            "Log Level:",
            "combobox",
            "log_level",
            "Advanced",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            help_text="Set the verbosity of logging output. DEBUG shows all messages.",
            row=row
        )
        row += 2

        self._create_setting_row(
            content_frame,
            None,
            "check",
            "debug_mode",
            "Advanced",
            help_text="Enable debug mode for detailed troubleshooting information.",
            check_text="Enable debug mode",
            row=row
        )
        row += 2

        # CLI Integration Section
        row = self._create_section_header(content_frame, "CLI Integration", row)

        self._create_setting_row(
            content_frame,
            "CLI Path:",
            "entry",
            "cli_path",
            "Advanced",
            help_text="Path to the faster-whisper-hotkey CLI executable (leave empty for auto-detect).",
            row=row,
            width=30
        )
        row += 2

        cli_note = ttk.Label(
            content_frame,
            text="Note: Some advanced model settings must be configured via CLI.\n"
                 "Run 'faster-whisper-hotkey --help' in a terminal for more options.",
            foreground="gray",
            font=("", 8)
        )
        cli_note.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(0, 10))
        row += 2

        # File Locations Section
        row = self._create_section_header(content_frame, "File Locations", row)

        # Settings file location
        ttk.Label(content_frame, text="Settings File:").grid(
            row=row, column=0, sticky=tk.W, padx=(20, 10), pady=(8, 0)
        )
        settings_path_frame = ttk.Frame(content_frame)
        settings_path_frame.grid(row=row, column=1, sticky=tk.EW, padx=(0, 20), pady=(8, 0))

        ttk.Label(
            settings_path_frame,
            text=SETTINGS_FILE,
            font=("Consolas", 9),
            foreground="gray"
        ).pack(side=tk.LEFT)

        ttk.Button(
            settings_path_frame,
            text="Open Folder",
            command=self._open_settings_folder,
            width=12
        ).pack(side=tk.LEFT, padx=(10, 0))
        row += 1

        content_frame.columnconfigure(1, weight=1)

        # Reset Section
        row = content_frame.grid_size()[1] + 2
        reset_frame = ttk.Frame(content_frame)
        reset_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=(20, 20), pady=(20, 10))

        ttk.Label(
            reset_frame,
            text="Reset all settings to default values",
            foreground="gray"
        ).pack(side=tk.LEFT)

        ttk.Button(
            reset_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            width=15
        ).pack(side=tk.RIGHT)

    def _get_audio_devices(self) -> List[str]:
        """Get list of available audio input devices."""
        try:
            import sounddevice as sd
            devices = []
            for i, device in enumerate(sd.query_devices()):
                if device.get('max_input_channels', 0) > 0:
                    devices.append(f"{i}: {device['name']}")
            return devices
        except (ImportError, Exception):
            return ["Default Device"]

    def _load_settings_to_ui(self):
        """Load current settings values into the UI widgets."""
        if not self.settings:
            return

        # Load settings as dict to get extended values
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings_dict = {}

        # General settings
        self.vars["model_type"].set(self.settings.model_type)
        self.vars["model_name"].set(self.settings.model_name)
        self.vars["device"].set(self.settings.device.upper())
        self.vars["compute_type"].set(self.settings.compute_type)
        self.vars["language"].set(self.settings.language)
        # Theme settings (capitalize to match combobox options: System, Light, Dark)
        theme_value = getattr(self.settings, 'theme_mode', 'system')
        self.vars["theme_mode"].set(theme_value.capitalize())

        # Hotkeys
        self.vars["hotkey"].set(self.settings.hotkey)
        self.hotkey_display_var.set(self.settings.hotkey.upper())
        self.vars["activation_mode"].set(self.settings.activation_mode)
        self.vars["secondary_hotkey"].set(settings_dict.get("secondary_hotkey", ""))
        self.sec_hotkey_display_var.set(
            self.vars["secondary_hotkey"].get().upper() if self.vars["secondary_hotkey"].get() else "Not Set"
        )
        self.vars["per_app_hotkeys"].set(settings_dict.get("per_app_hotkeys", False))

        # Audio
        self.vars["audio_gain"].set(settings_dict.get("audio_gain", DEFAULT_AUDIO_GAIN))
        self.vars["noise_suppression"].set(settings_dict.get("noise_suppression", DEFAULT_NOISE_SUPPRESSION))
        self.vars["input_device"].set(settings_dict.get("input_device", "default"))

        # Post-processing
        self.vars["filler_removal"].set(settings_dict.get("filler_removal", DEFAULT_FILLER_REMOVAL))
        self.vars["punctuation"].set(settings_dict.get("punctuation", DEFAULT_PUNCTUATION))
        self.vars["capitalization"].set(settings_dict.get("capitalization", True))

        # Privacy
        self.vars["privacy_mode"].set(self.settings.privacy_mode)
        self.vars["history_max_items"].set(self.settings.history_max_items)
        self.vars["history_retention_days"].set(settings_dict.get("history_retention_days", DEFAULT_HISTORY_RETENTION_DAYS))
        self.vars["auto_clear_history"].set(settings_dict.get("auto_clear_history", False))
        self.vars["history_confirm_clear"].set(settings_dict.get("history_confirm_clear", True))
        self.vars["history_backup_enabled"].set(settings_dict.get("history_backup_enabled", False))

        # Advanced
        self.vars["log_level"].set(settings_dict.get("log_level", DEFAULT_LOG_LEVEL))
        self.vars["debug_mode"].set(settings_dict.get("debug_mode", False))
        self.vars["cli_path"].set(settings_dict.get("cli_path", ""))

    def _on_search(self, *args):
        """Handle search input to highlight matching settings."""
        search_term = self.search_var.get().lower().strip()

        if not search_term:
            # Reset all widgets to normal state
            for key, info in self.setting_widgets.items():
                if "help_label" in info:
                    info["help_label"].config(foreground="gray")
            return

        # Find matching settings
        for key, info in self.setting_widgets.items():
            label_text = info["label"].lower() if info["label"] else ""
            help_text = info["help_text"].lower()
            tab_name = info["tab"].lower()

            # Check if search term matches
            matches = (
                search_term in label_text or
                search_term in help_text or
                search_term in tab_name or
                search_term in key.lower()
            )

            # Update help label color to indicate match
            if "help_label" in info:
                if matches:
                    info["help_label"].config(foreground="#2196F3")  # Blue for match
                else:
                    info["help_label"].config(foreground="gray")

    def _change_primary_hotkey(self):
        """Open dialog to change the primary hotkey."""
        current = self.vars["hotkey"].get()
        current_mode = self.vars["activation_mode"].get()

        new_hotkey, new_mode = show_hotkey_dialog(
            self.window,
            current,
            current_mode
        )

        if new_hotkey or new_mode:
            if new_hotkey:
                self.vars["hotkey"].set(new_hotkey)
                self.hotkey_display_var.set(new_hotkey.upper())
            if new_mode:
                self.vars["activation_mode"].set(new_mode)
            self._mark_restart_required()

    def _change_secondary_hotkey(self):
        """Open dialog to change the secondary hotkey."""
        from .hotkey_dialog import HotkeyDialog

        current = self.vars["secondary_hotkey"].get()

        # Create a simple capture dialog
        dialog = HotkeyDialog(self.window, current if current else "not set", "hold")
        new_hotkey, _ = dialog.show()

        if new_hotkey:
            self.vars["secondary_hotkey"].set(new_hotkey)
            self.sec_hotkey_display_var.set(new_hotkey.upper())
            self._mark_restart_required()

    def _clear_secondary_hotkey(self):
        """Clear the secondary hotkey."""
        self.vars["secondary_hotkey"].set("")
        self.sec_hotkey_display_var.set("Not Set")

    def _clear_history(self):
        """Clear all transcription history."""
        # Check if confirmation is enabled
        confirm_clear = self.vars.get("history_confirm_clear")
        if confirm_clear and isinstance(confirm_clear, tk.BooleanVar):
            should_confirm = confirm_clear.get()
        else:
            should_confirm = True  # Default to confirm

        if should_confirm:
            if not messagebox.askyesno(
                "Clear History",
                "Are you sure you want to clear all transcription history?\n\nThis action cannot be undone."
            ):
                return

        # Check if backup is enabled
        backup_enabled = self.vars.get("history_backup_enabled")
        if backup_enabled and isinstance(backup_enabled, tk.BooleanVar):
            if backup_enabled.get():
                self._backup_history(silent=True)

        clear_history()
        messagebox.showinfo("History Cleared", "All transcription history has been cleared.")

    def _export_history(self):
        """Export history to a file."""
        from .settings import load_history
        from ..flet_gui.history_manager import HistoryManager

        # Try to use HistoryManager for export if available
        try:
            history_mgr = HistoryManager()
            stats = history_mgr.get_statistics()
            if stats.get("total_items", 0) == 0:
                messagebox.showinfo("Export History", "No history to export.")
                return
        except Exception:
            # Fall back to JSON history
            history = load_history()
            if not history:
                messagebox.showinfo("Export History", "No history to export.")
                return

        path = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if path:
            try:
                if path.endswith(".json"):
                    if 'history_mgr' in locals():
                        history_mgr.export_to_json(path)
                    else:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(history, f, indent=2, ensure_ascii=False)
                else:
                    # Export as plain text
                    if 'history_mgr' in locals():
                        history_mgr.export_to_txt(path)
                    else:
                        with open(path, "w", encoding="utf-8") as f:
                            for i, item in enumerate(history, 1):
                                timestamp = item.get("timestamp", "Unknown")
                                text = item.get("text", "")
                                f.write(f"[{timestamp}]\n{text}\n\n")

                messagebox.showinfo("Export Successful", f"History exported to {path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export history:\n{e}")

    def _backup_history(self, silent: bool = False):
        """Backup history to a timestamped file."""
        from ..flet_gui.history_manager import HistoryManager
        from datetime import datetime
        import os

        try:
            history_mgr = HistoryManager()
            stats = history_mgr.get_statistics()
            if stats.get("total_items", 0) == 0:
                if not silent:
                    messagebox.showinfo("Backup History", "No history to backup.")
                return
        except Exception as e:
            if not silent:
                messagebox.showerror("Backup Failed", f"Failed to access history:\n{e}")
            return

        # Create timestamped backup filename
        backup_dir = os.path.join(os.path.dirname(SETTINGS_FILE), "history_backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"history_backup_{timestamp}.json")

        try:
            history_mgr.export_to_json(backup_path)
            if not silent:
                messagebox.showinfo("Backup Successful", f"History backed up to:\n{backup_path}")
            return backup_path
        except Exception as e:
            if not silent:
                messagebox.showerror("Backup Failed", f"Failed to backup history:\n{e}")
            return None

    def _restore_history(self):
        """Restore history from a backup file."""
        from ..flet_gui.history_manager import HistoryManager
        import os

        backup_dir = os.path.join(os.path.dirname(SETTINGS_FILE), "history_backups")
        os.makedirs(backup_dir, exist_ok=True)

        path = filedialog.askopenfilename(
            title="Restore History",
            initialdir=backup_dir,
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        # Confirm restore
        if not messagebox.askyesno(
            "Confirm Restore",
            "This will add all items from the backup to your current history. Continue?"
        ):
            return

        try:
            import json
            from ..flet_gui.history_manager import HistoryItem

            history_mgr = HistoryManager()

            with open(path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            restored_count = 0
            for entry in backup_data:
                try:
                    # Create HistoryItem from backup data
                    item = HistoryItem(
                        timestamp=entry.get("timestamp", ""),
                        text=entry.get("text", ""),
                        model=entry.get("model", ""),
                        language=entry.get("language", ""),
                        device=entry.get("device", ""),
                        app_context=entry.get("app_context"),
                        confidence=entry.get("confidence"),
                        duration_ms=entry.get("duration_ms"),
                        tags=entry.get("tags", []),
                        edited=entry.get("edited", False),
                    )
                    if history_mgr.add_item(item, skip_notification=True):
                        restored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to restore history item: {e}")
                    continue

            messagebox.showinfo(
                "Restore Successful",
                f"Restored {restored_count} items from backup."
            )

        except Exception as e:
            messagebox.showerror("Restore Failed", f"Failed to restore history:\n{e}")

    def _open_settings_folder(self):
        """Open the settings folder in the file manager."""
        import subprocess
        import os

        settings_dir = os.path.dirname(SETTINGS_FILE)

        try:
            if os.name == "nt":  # Windows
                os.startfile(settings_dir)
            elif os.name == "posix":
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", settings_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", settings_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")

    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n\nThis will discard all your custom settings."
        ):
            # Create default settings
            default_settings = {
                "device_name": "default",
                "model_type": "whisper",
                "model_name": "large-v3",
                "compute_type": "default",
                "device": "cpu",
                "language": "en",
                "hotkey": "pause",
                "activation_mode": "hold",
                "history_max_items": 1000,
                "privacy_mode": False,
                "onboarding_completed": True,
                # Additional settings
                "secondary_hotkey": "",
                "per_app_hotkeys": False,
                "audio_gain": DEFAULT_AUDIO_GAIN,
                "noise_suppression": DEFAULT_NOISE_SUPPRESSION,
                "input_device": "default",
                "filler_removal": DEFAULT_FILLER_REMOVAL,
                "punctuation": DEFAULT_PUNCTUATION,
                "capitalization": True,
                "history_retention_days": DEFAULT_HISTORY_RETENTION_DAYS,
                "auto_clear_history": False,
                "history_confirm_clear": True,
                "history_backup_enabled": False,
                "log_level": DEFAULT_LOG_LEVEL,
                "debug_mode": False,
                "cli_path": "",
            }

            save_settings(default_settings)
            self.settings = load_settings()
            self._load_settings_to_ui()

            messagebox.showinfo("Settings Reset", "All settings have been reset to defaults.")
            self._mark_restart_required()

    def _mark_restart_required(self):
        """Mark that a restart is required for changes to take effect."""
        self.restart_required = True
        self.restart_label.pack(side=tk.LEFT, padx=(0, 20))

    def _save_settings(self):
        """Save all settings and close the window."""
        # Build settings dict from current values
        settings_dict = {
            # Core settings (from Settings dataclass)
            "device_name": self.vars["input_device"].get(),
            "model_type": self.vars["model_type"].get(),
            "model_name": self.vars["model_name"].get(),
            "compute_type": self.vars["compute_type"].get(),
            "device": self.vars["device"].get().lower(),
            "language": self.vars["language"].get(),
            "hotkey": self.vars["hotkey"].get(),
            "activation_mode": self.vars["activation_mode"].get(),
            "history_max_items": self.vars["history_max_items"].get(),
            "privacy_mode": self.vars["privacy_mode"].get(),
            "onboarding_completed": getattr(self.settings, "onboarding_completed", True),

            # Extended settings
            "secondary_hotkey": self.vars["secondary_hotkey"].get(),
            "per_app_hotkeys": self.vars["per_app_hotkeys"].get(),
            "audio_gain": self.vars["audio_gain"].get(),
            "noise_suppression": self.vars["noise_suppression"].get(),
            "input_device": self.vars["input_device"].get(),
            "filler_removal": self.vars["filler_removal"].get(),
            "punctuation": self.vars["punctuation"].get(),
            "capitalization": self.vars["capitalization"].get(),
            "history_retention_days": self.vars["history_retention_days"].get(),
            "auto_clear_history": self.vars["auto_clear_history"].get(),
            "history_confirm_clear": self.vars["history_confirm_clear"].get(),
            "history_backup_enabled": self.vars["history_backup_enabled"].get(),
            "log_level": self.vars["log_level"].get(),
            "debug_mode": self.vars["debug_mode"].get(),
            "cli_path": self.vars["cli_path"].get(),
            # Theme settings (lowercase to match internal representation)
            "theme_mode": self.vars["theme_mode"].get().lower(),
        }

        # Check if theme changed
        old_theme = getattr(self.settings, 'theme_mode', 'system')
        new_theme = settings_dict["theme_mode"]
        theme_changed = old_theme != new_theme

        # Save to file
        save_settings(settings_dict)

        # Notify callbacks
        if self.on_settings_changed:
            self.on_settings_changed()

        if self.restart_required and self.on_restart_required:
            self.on_restart_required()

        # Notify theme changed callback
        if theme_changed and self.on_theme_changed:
            self.on_theme_changed(new_theme)

        # Close window
        self._on_window_close()

        # Show success message
        if self.restart_required:
            messagebox.showinfo(
                "Settings Saved",
                "Settings saved successfully.\n\nSome changes require restarting the transcriber to take effect."
            )
        else:
            # Show toast or brief message
            pass

    def _cancel(self):
        """Close without saving."""
        self._on_window_close()

    def _on_window_close(self):
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None

    def close(self):
        """Close the window if open."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None


def show_settings_panel(
    parent=None,
    on_settings_changed: Callable = None,
    on_restart_required: Callable = None,
    on_theme_changed: Callable = None
) -> SettingsPanel:
    """
    Show the settings panel.

    Args:
        parent: Parent window
        on_settings_changed: Callback when settings are changed
        on_restart_required: Callback when transcriber restart is needed
        on_theme_changed: Callback when theme is changed

    Returns:
        The SettingsPanel instance
    """
    panel = SettingsPanel(parent, on_settings_changed, on_restart_required, on_theme_changed)
    panel.show()
    return panel
