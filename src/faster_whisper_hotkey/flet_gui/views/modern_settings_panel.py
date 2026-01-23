"""
Modern settings panel view for the Flet GUI.

This module provides a comprehensive, categorized settings interface with:
- Logical organization of settings into categories
- Search functionality to find settings quickly
- Reset to defaults option with confirmation
- Restart-required indicators
- Per-application settings override support

Classes
-------
SettingsCategory
    Enum for settings categories.

ModernSettingsPanel
    Comprehensive modern settings interface.

SettingsItem
    Individual setting item component.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, List, Dict, Any

import flet as ft

from ..settings_service import SettingsService
from ..app_state import AppState
from ..hardware_detector import HardwareDetector, HardwareInfo, format_vram_size
from ..theme import get_theme_manager, SPACING, BORDER_RADIUS, ANIMATION_DURATION
from ..components import Card, Button
from ..notifications import NotificationManager, NotificationType
from ..accessibility import (
    get_accessibility_manager,
    FontSize,
    ContrastMode,
    AccessibilitySettings,
)

logger = logging.getLogger(__name__)


class SettingsCategory(Enum):
    """Settings category definitions."""

    GENERAL = "general"
    RECORDING = "recording"
    MODELS = "models"
    TEXT_PROCESSING = "text_processing"
    HISTORY = "history"
    SHORTCUTS = "shortcuts"
    ACCESSIBILITY = "accessibility"
    ADVANCED = "advanced"


@dataclass
class SettingDefinition:
    """
    Definition of a setting item.

    Attributes
    ----------
    key
        Settings key.
    title
        Display title.
    description
        Optional description.
    category
        Settings category.
    type
        Setting type (dropdown, toggle, text, hotkey).
    options
        Options for dropdown type.
    default
        Default value.
    requires_restart
        Whether changing this requires restart.
    search_keywords
        Additional search keywords.
    tooltip
        Optional tooltip text for additional help.
    """

    key: str
    title: str
    description: str = ""
    category: SettingsCategory = SettingsCategory.GENERAL
    type: str = "text"  # dropdown, toggle, text, hotkey, slider
    options: List[tuple[str, str]] = None  # List of (value, label)
    default: Any = None
    requires_restart: bool = False
    search_keywords: List[str] = None
    tooltip: str = ""

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.search_keywords is None:
            self.search_keywords = []


class SettingsItem(ft.Container):
    """
    A single settings item with label, description, and control.

    Parameters
    ----------
    definition
        Setting definition.
    value
        Current value.
    on_change
        Callback when value changes.
    **kwargs
        Additional Container properties.
    """

    def __init__(
        self,
        definition: SettingDefinition,
        value: Any = None,
        on_change: Optional[Callable[[str, Any], None]] = None,
        **kwargs,
    ):
        self._theme = get_theme_manager()
        self._definition = definition
        self._on_change = on_change
        self._current_value = value

        # Build content
        content = self._build_content()

        super().__init__(
            content=content,
            padding=SPACING.sm,
            **kwargs,
        )

    def _build_content(self) -> ft.Control:
        """Build the settings item content."""
        # Create label and description
        label_row_parts = [ft.Text(
            self._definition.title,
            size=14,
            weight=ft.FontWeight.MEDIUM,
            color=self._theme.colors.on_surface,
        )]

        # Add tooltip icon if tooltip text exists
        if self._definition.tooltip:
            label_row_parts.append(ft.Icon(
                ft.icons.HELP_OUTLINE,
                size=14,
                color=self._theme.colors.primary,
                tooltip=self._definition.tooltip,
            ))

        label_parts = [ft.Row(
            label_row_parts,
            spacing=SPACING.xs,
            alignment=ft.MainAxisAlignment.START,
        )]

        if self._definition.description:
            label_parts.append(ft.Text(
                self._definition.description,
                size=12,
                color=self._theme.colors.on_surface_variant,
            ))

        if self._definition.requires_restart:
            label_parts.append(ft.Row([
                ft.Icon(
                    ft.icons.INFO,
                    size=12,
                    color=self._theme.colors.warning,
                ),
                ft.Text(
                    "Requires restart",
                    size=11,
                    color=self._theme.colors.warning,
                ),
            ], spacing=4))

        label_column = ft.Column(
            controls=label_parts,
            spacing=4,
            expand=True,
        )

        # Create control based on type
        control = self._build_control()

        return ft.Row(
            [label_column, control],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_control(self) -> ft.Control:
        """Build the input control based on setting type."""
        if self._definition.type == "toggle":
            return ft.Switch(
                value=self._current_value or False,
                active_color=self._theme.colors.primary,
                on_change=self._on_toggle_change,
            )

        elif self._definition.type == "dropdown":
            return ft.Dropdown(
                options=[
                    ft.dropdown_option(key, label)
                    for key, label in self._definition.options
                ],
                value=self._current_value,
                width=200,
                on_change=self._on_dropdown_change,
            )

        elif self._definition.type == "hotkey":
            self._hotkey_display = ft.Text(
                self._current_value or "Not set",
                size=13,
                color=self._theme.colors.primary,
            )
            capture_btn = ft.IconButton(
                icon=ft.icons.KEYBOARD,
                icon_size=18,
                tooltip="Set hotkey",
                on_click=self._on_hotkey_click,
            )

            return ft.Row([
                self._hotkey_display,
                capture_btn,
            ], spacing=SPACING.sm)

        elif self._definition.type == "slider":
            return ft.Slider(
                value=self._current_value or 0,
                min=0,
                max=1,
                divisions=100,
                on_change=self._on_slider_change,
            )

        elif self._definition.type == "number":
            return ft.TextField(
                value=str(self._current_value or 0),
                width=100,
                text_align=ft.TextAlign.RIGHT,
                on_change=self._on_text_change,
            )

        # Default to text field
        return ft.TextField(
            value=str(self._current_value or ""),
            width=200,
            on_change=self._on_text_change,
        )

    def _on_toggle_change(self, e):
        """Handle toggle change."""
        self._current_value = e.data == "true"
        if self._on_change:
            self._on_change(self._definition.key, self._current_value)

    def _on_dropdown_change(self, e):
        """Handle dropdown change."""
        self._current_value = e.data
        if self._on_change:
            self._on_change(self._definition.key, self._current_value)

    def _on_slider_change(self, e):
        """Handle slider change."""
        self._current_value = float(e.data)
        if self._on_change:
            self._on_change(self._definition.key, self._current_value)

    def _on_text_change(self, e):
        """Handle text field change."""
        self._current_value = e.control.value
        if self._on_change:
            self._on_change(self._definition.key, self._current_value)

    def _on_hotkey_click(self, e):
        """Handle hotkey capture button click."""
        if self.page:
            self._show_hotkey_dialog()

    def _show_hotkey_dialog(self):
        """Show dialog for hotkey input."""
        temp_hotkey = ft.TextField(
            label="Enter hotkey",
            hint_text="e.g., pause, f1, ctrl+shift+h",
            value=self._current_value or "",
            autofocus=True,
        )

        def save_hotkey(e):
            hotkey = temp_hotkey.value.strip().lower()
            if hotkey:
                is_valid, error = SettingsService.validate_hotkey(hotkey)
                if is_valid:
                    self._current_value = hotkey
                    if hasattr(self, '_hotkey_display'):
                        self._hotkey_display.value = hotkey.upper()
                    if self._on_change:
                        self._on_change(self._definition.key, hotkey)
                    self.page.close(dialog)
                else:
                    self._show_error(f"Invalid hotkey: {error}")

        def cancel_dialog(e):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Set Hotkey"),
            content=ft.Column([temp_hotkey], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_dialog),
                ft.TextButton("Set", on_click=save_hotkey),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _show_error(self, message: str):
        """Show error snackbar."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.colors.ERROR_CONTAINER,
                )
            )

    @property
    def value(self) -> Any:
        """Get current value."""
        return self._current_value


class ModernSettingsPanel:
    """
    Comprehensive modern settings panel with categorized organization.

    Features:
    - Logical category organization
    - Search functionality
    - Reset to defaults
    - Restart-required indicators
    """

    # Category display info
    CATEGORY_INFO = {
        SettingsCategory.GENERAL: (
            "General",
            ft.icons.TUNE,
            "Theme, language, and startup behavior",
        ),
        SettingsCategory.RECORDING: (
            "Recording",
            ft.icons.MIC,
            "Hotkey, audio device, and recording behavior",
        ),
        SettingsCategory.MODELS: (
            "Models",
            ft.icons.MODEL_TRAINING,
            "AI model selection and configuration",
        ),
        SettingsCategory.TEXT_PROCESSING: (
            "Text Processing",
            ft.icons.TEXT_FIELDS,
            "Capitalization, punctuation, and formatting",
        ),
        SettingsCategory.HISTORY: (
            "History",
            ft.icons.HISTORY,
            "Transcription history management",
        ),
        SettingsCategory.SHORTCUTS: (
            "Shortcuts",
            ft.icons.KEYBOARD,
            "Keyboard shortcuts and gestures",
        ),
        SettingsCategory.ACCESSIBILITY: (
            "Accessibility",
            ft.icons.ACCESSIBILITY_NEW,
            "Display, navigation, and screen reader options",
        ),
        SettingsCategory.ADVANCED: (
            "Advanced",
            ft.icons.SETTINGS,
            "Developer options and diagnostics",
        ),
    }

    def __init__(
        self,
        settings_service: SettingsService,
        app_state: AppState,
        on_save: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        on_open_model_manager: Optional[Callable[[], None]] = None,
    ):
        """Initialize the modern settings panel."""
        self.settings_service = settings_service
        self.app_state = app_state
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._on_open_model_manager = on_open_model_manager

        self._theme = get_theme_manager()

        # Hardware detection
        self._hardware_detector = HardwareDetector()
        self._hardware_info: Optional[HardwareInfo] = None

        # UI state
        self._current_category: SettingsCategory = SettingsCategory.GENERAL
        self._search_query: str = ""
        self._pending_changes: Dict[str, Any] = {}
        self._special_settings: Dict[str, Any] = {}

        # Setting definitions
        self._definitions: List[SettingDefinition] = self._build_definitions()

        # UI references
        self._category_buttons: Dict[SettingsCategory, ft.Control] = {}
        self._settings_items: Dict[str, SettingsItem] = {}
        self._search_field: Optional[ft.TextField] = None
        self._content_area: Optional[ft.Column] = None
        self._results_count: Optional[ft.Text] = None

    def _build_definitions(self) -> List[SettingDefinition]:
        """Build setting definitions for all categories."""
        # Language display names
        language_options = [
            ("auto", "Auto-detect"),
            ("en", "English"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("ru", "Russian"),
            ("zh", "Chinese"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("ar", "Arabic"),
            ("hi", "Hindi"),
            ("nl", "Dutch"),
            ("pl", "Polish"),
            ("sv", "Swedish"),
            ("da", "Danish"),
            ("fi", "Finnish"),
            ("no", "Norwegian"),
            ("tr", "Turkish"),
            ("cs", "Czech"),
            ("el", "Greek"),
            ("he", "Hebrew"),
            ("th", "Thai"),
            ("vi", "Vietnamese"),
            ("id", "Indonesian"),
            ("uk", "Ukrainian"),
        ]

        # Model display names
        model_options = [
            ("large-v3", "Large v3 (Recommended)"),
            ("large-v2", "Large v2"),
            ("large-v1", "Large v1"),
            ("medium", "Medium"),
            ("medium.en", "Medium (English only)"),
            ("small", "Small"),
            ("small.en", "Small (English only)"),
            ("base", "Base"),
            ("base.en", "Base (English only)"),
            ("tiny", "Tiny (Fastest)"),
            ("tiny.en", "Tiny (English only, Fastest)"),
            ("distil-large-v3", "Distil Large v3"),
            ("distil-large-v2", "Distil Large v2"),
            ("distil-medium.en", "Distil Medium"),
            ("distil-small.en", "Distil Small"),
        ]

        theme_options = [
            ("system", "System"),
            ("light", "Light"),
            ("dark", "Dark"),
        ]

        activation_mode_options = [
            ("hold", "Hold to record"),
            ("toggle", "Toggle on/off"),
        ]

        device_options = [
            ("cpu", "CPU"),
            ("cuda", "CUDA GPU"),
        ]

        compute_type_options = [
            ("float16", "Float16"),
            ("int8", "Int8 (Faster)"),
        ]

        capitalization_options = [
            ("sentence", "Sentence case"),
            ("title", "Title Case"),
        ]

        punctuation_options = [
            ("minimal", "Minimal"),
            ("full", "Full"),
        ]

        number_style_options = [
            ("commas", "1,234.56"),
            ("words", "One thousand..."),
            ("both", "Both formats"),
        ]

        tone_preset_options = [
            ("neutral", "Neutral"),
            ("professional", "Professional"),
            ("casual", "Casual"),
            ("technical", "Technical"),
            ("concise", "Concise"),
            ("creative", "Creative"),
        ]

        definitions = [
            # General settings
            SettingDefinition(
                key="theme_mode",
                title="Theme",
                description="Choose your preferred color scheme",
                category=SettingsCategory.GENERAL,
                type="dropdown",
                options=theme_options,
                default="system",
                tooltip="Light: bright colors, Dark: easy on eyes, System: follows Windows setting",
            ),
            SettingDefinition(
                key="language",
                title="Language",
                description="Primary transcription language",
                category=SettingsCategory.GENERAL,
                type="dropdown",
                options=language_options,
                default="en",
                requires_restart=True,
                search_keywords=["transcription", "speech", "input"],
                tooltip="Select 'Auto-detect' to let the AI identify the language automatically",
            ),
            SettingDefinition(
                key="onboarding_completed",
                title="Show onboarding",
                description="Display the tutorial on next launch",
                category=SettingsCategory.GENERAL,
                type="toggle",
                default=False,
                search_keywords=["tutorial", "help", "guide"],
                tooltip="Enable this to see the interactive tutorial again next time you start the app",
            ),

            # Recording settings
            SettingDefinition(
                key="hotkey",
                title="Recording hotkey",
                description="Press to start/stop recording",
                category=SettingsCategory.RECORDING,
                type="hotkey",
                default="pause",
                search_keywords=["keyboard", "shortcut", "trigger"],
                tooltip="Choose a key that doesn't conflict with other applications. PAUSE is a good default.",
            ),
            SettingDefinition(
                key="history_hotkey",
                title="History hotkey",
                description="Quick access to transcription history",
                category=SettingsCategory.SHORTCUTS,
                type="hotkey",
                default="ctrl+shift+h",
                search_keywords=["keyboard", "shortcut", "log"],
                tooltip="Press this to quickly open the history panel from anywhere",
            ),
            SettingDefinition(
                key="activation_mode",
                title="Activation mode",
                description="How the hotkey triggers recording",
                category=SettingsCategory.RECORDING,
                type="dropdown",
                options=activation_mode_options,
                default="hold",
                tooltip="Hold: Press and hold to record, release to stop. Toggle: Press once to start, press again to stop.",
            ),
            SettingDefinition(
                key="enable_streaming",
                title="Enable streaming",
                description="Show real-time transcription preview",
                category=SettingsCategory.RECORDING,
                type="toggle",
                default=False,
                tooltip="Shows text as you speak. May be less accurate than waiting until you finish speaking.",
            ),
            SettingDefinition(
                key="stream_chunk_duration",
                title="Stream chunk duration",
                description="Audio chunk size for streaming (seconds)",
                category=SettingsCategory.RECORDING,
                type="slider",
                default=3.0,
                tooltip="Smaller values = faster updates but may reduce accuracy. Larger values = more accurate but slower.",
            ),
            SettingDefinition(
                key="confidence_threshold",
                title="Confidence threshold",
                description="Minimum confidence for transcription",
                category=SettingsCategory.RECORDING,
                type="slider",
                default=0.5,
                tooltip="Higher values filter out uncertain text but may miss some words. Lower values capture more but may include errors.",
            ),

            # Model settings
            SettingDefinition(
                key="model_name",
                title="AI Model",
                description="Larger models are more accurate but slower",
                category=SettingsCategory.MODELS,
                type="dropdown",
                options=model_options,
                default="large-v3",
                requires_restart=True,
                search_keywords=["whisper", "ai", "transcription", "accuracy"],
                tooltip="Large-v3: best accuracy, slow. Medium: good balance. Small/Tiny: fastest, less accurate.",
            ),
            SettingDefinition(
                key="device",
                title="Compute device",
                description="Use GPU for faster transcription",
                category=SettingsCategory.MODELS,
                type="dropdown",
                options=device_options,
                default="cpu",
                requires_restart=True,
                search_keywords=["gpu", "cuda", "hardware"],
                tooltip="CUDA GPU: Much faster if you have an NVIDIA GPU. CPU: Slower but works on any computer.",
            ),
            SettingDefinition(
                key="compute_type",
                title="Compute precision",
                description="Lower precision = faster, less accurate",
                category=SettingsCategory.MODELS,
                type="dropdown",
                options=compute_type_options,
                default="float16",
                requires_restart=True,
                tooltip="Float16: Good balance of speed and accuracy. Int8: Fastest, slightly less accurate.",
            ),

            # Text processing settings
            SettingDefinition(
                key="tp_auto_capitalize",
                title="Auto-capitalize",
                description="Capitalize the first letter of sentences",
                category=SettingsCategory.TEXT_PROCESSING,
                type="toggle",
                default=True,
                search_keywords=["capitalization", "formatting"],
                tooltip="Automatically capitalizes the first letter of each sentence for proper formatting.",
            ),
            SettingDefinition(
                key="tp_capitalization_style",
                title="Capitalization style",
                description="How to capitalize text",
                category=SettingsCategory.TEXT_PROCESSING,
                type="dropdown",
                options=capitalization_options,
                default="sentence",
                tooltip="Sentence case: Only first letter capitalized. Title Case: First Letter Of Each Word Capitalized.",
            ),
            SettingDefinition(
                key="tp_auto_punctuate",
                title="Auto-punctuate",
                description="Add punctuation automatically",
                category=SettingsCategory.TEXT_PROCESSING,
                type="toggle",
                default=True,
                search_keywords=["punctuation", "grammar"],
                tooltip="Uses AI to add appropriate punctuation (periods, commas, etc.) to your transcription.",
            ),
            SettingDefinition(
                key="tp_punctuation_style",
                title="Punctuation style",
                description="How much punctuation to add",
                category=SettingsCategory.TEXT_PROCESSING,
                type="dropdown",
                options=punctuation_options,
                default="minimal",
            ),
            SettingDefinition(
                key="tp_remove_filler_words",
                title="Remove filler words",
                description="Remove ums, ahs, and other fillers",
                category=SettingsCategory.TEXT_PROCESSING,
                type="toggle",
                default=True,
                search_keywords=["clean", "filter"],
            ),
            SettingDefinition(
                key="tp_format_numbers",
                title="Format numbers",
                description="Format spoken numbers consistently",
                category=SettingsCategory.TEXT_PROCESSING,
                type="toggle",
                default=False,
            ),
            SettingDefinition(
                key="tp_number_style",
                title="Number style",
                description="How to format numbers",
                category=SettingsCategory.TEXT_PROCESSING,
                type="dropdown",
                options=number_style_options,
                default="commas",
            ),
            SettingDefinition(
                key="tp_tone_preset_enabled",
                title="Enable tone processing",
                description="Apply tone/style adjustments to text",
                category=SettingsCategory.TEXT_PROCESSING,
                type="toggle",
                default=False,
            ),
            SettingDefinition(
                key="tp_tone_preset",
                title="Tone preset",
                description="Select the tone/style for transcription",
                category=SettingsCategory.TEXT_PROCESSING,
                type="dropdown",
                options=tone_preset_options,
                default="neutral",
            ),

            # History settings
            SettingDefinition(
                key="history_max_items",
                title="History limit",
                description="Maximum items to keep in history",
                category=SettingsCategory.HISTORY,
                type="number",
                default=50,
                search_keywords=["log", "storage", "save"],
            ),
            SettingDefinition(
                key="history_retention_days",
                title="Auto-delete after",
                description="Days to keep history (0 = never)",
                category=SettingsCategory.HISTORY,
                type="number",
                default=30,
            ),
            SettingDefinition(
                key="privacy_mode",
                title="Privacy mode",
                description="Don't save history, delete audio immediately",
                category=SettingsCategory.HISTORY,
                type="toggle",
                default=False,
                search_keywords=["security", "private"],
            ),
            SettingDefinition(
                key="history_confirm_clear",
                title="Confirm before clear",
                description="Show confirmation when clearing history",
                category=SettingsCategory.HISTORY,
                type="toggle",
                default=True,
            ),
            SettingDefinition(
                key="history_backup_enabled",
                title="Auto-backup",
                description="Backup history before clearing",
                category=SettingsCategory.HISTORY,
                type="toggle",
                default=False,
            ),

            # Accessibility settings
            SettingDefinition(
                key="a11y_font_size",
                title="Font size",
                description="Scale text size for better readability",
                category=SettingsCategory.ACCESSIBILITY,
                type="dropdown",
                options=[
                    ("small", "Small (85%)"),
                    ("normal", "Normal (100%)"),
                    ("large", "Large (115%)"),
                    ("extra_large", "Extra Large (130%)"),
                ],
                default="normal",
                search_keywords=["text", "readability", "scale"],
            ),
            SettingDefinition(
                key="a11y_high_contrast",
                title="High contrast mode",
                description="Increase contrast for better visibility",
                category=SettingsCategory.ACCESSIBILITY,
                type="toggle",
                default=False,
                search_keywords=["visibility", "colors", "contrast"],
            ),
            SettingDefinition(
                key="a11y_contrast_mode",
                title="Contrast level",
                description="Select contrast intensity",
                category=SettingsCategory.ACCESSIBILITY,
                type="dropdown",
                options=[
                    ("high_contrast", "High Contrast"),
                    ("extra_high_contrast", "Extra High (Black/White)"),
                ],
                default="high_contrast",
                search_keywords=["colors", "theme", "visibility"],
            ),
            SettingDefinition(
                key="a11y_focus_indicators",
                title="Focus indicators",
                description="Show visual indicators for keyboard navigation",
                category=SettingsCategory.ACCESSIBILITY,
                type="toggle",
                default=True,
                search_keywords=["keyboard", "navigation", "focus"],
            ),
            SettingDefinition(
                key="a11y_screen_reader",
                title="Screen reader announcements",
                description="Announce state changes for screen readers",
                category=SettingsCategory.ACCESSIBILITY,
                type="toggle",
                default=True,
                search_keywords=["announcements", "audio", "blind"],
            ),
            SettingDefinition(
                key="a11y_reduce_motion",
                title="Reduce motion",
                description="Minimize animations for reduced motion preference",
                category=SettingsCategory.ACCESSIBILITY,
                type="toggle",
                default=False,
                search_keywords=["animation", "transitions", "vestibular"],
            ),

            # Advanced settings
            SettingDefinition(
                key="auto_copy_on_release",
                title="Auto-copy on release",
                description="Copy transcription when releasing hotkey",
                category=SettingsCategory.ADVANCED,
                type="toggle",
                default=True,
                search_keywords=["clipboard", "paste"],
            ),
            SettingDefinition(
                key="compact_mode",
                title="Compact mode",
                description="Use smaller UI elements for tight spaces",
                category=SettingsCategory.ADVANCED,
                type="toggle",
                default=False,
                search_keywords=["size", "layout", "small screen"],
                tooltip="Enable this to make the UI more compact. Useful for smaller screens or if you want to fit more content.",
            ),
            SettingDefinition(
                key="tray_notifications_enabled",
                title="Tray notifications",
                description="Show system tray notifications for transcription events",
                category=SettingsCategory.ADVANCED,
                type="toggle",
                default=True,
                search_keywords=["systray", "notification", "balloon", "popup"],
            ),
        ]

        return definitions

    def build(self) -> ft.Container:
        """Build the settings panel UI."""
        # Create the main layout
        main_content = ft.Row(
            [
                self._build_sidebar(),
                self._build_main_content(),
            ],
            expand=True,
        )

        panel = ft.Container(
            content=main_content,
            expand=True,
        )

        # Run hardware detection
        self._run_hardware_detection()

        return panel

    def _build_sidebar(self) -> ft.Container:
        """Build the category sidebar."""
        categories = [
            (SettingsCategory.GENERAL, "General", ft.icons.TUNE),
            (SettingsCategory.RECORDING, "Recording", ft.icons.MIC),
            (SettingsCategory.MODELS, "Models", ft.icons.MODEL_TRAINING),
            (SettingsCategory.TEXT_PROCESSING, "Text", ft.icons.TEXT_FIELDS),
            (SettingsCategory.HISTORY, "History", ft.icons.HISTORY),
            (SettingsCategory.SHORTCUTS, "Shortcuts", ft.icons.KEYBOARD),
            (SettingsCategory.ACCESSIBILITY, "Accessibility", ft.icons.ACCESSIBILITY_NEW),
            (SettingsCategory.ADVANCED, "Advanced", ft.icons.SETTINGS),
        ]

        category_buttons = []
        for cat_id, title, icon in categories:
            btn = ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=18),
                    ft.Text(title, size=13),
                ], spacing=SPACING.sm),
                padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
                border_radius=ft.BorderRadius(SPACING.sm, 0, 0, SPACING.sm),
                on_click=lambda _, cat=cat_id: self._select_category(cat),
                cursor=ft.MouseCursor.CLICKER,
            )
            self._category_buttons[cat_id] = btn
            category_buttons.append(btn)

        # Reset and Actions buttons
        divider = ft.Container(
            height=1,
            bgcolor=ft.colors.OUTLINE_VARIANT,
            margin=ft.Margin(0, SPACING.md, 0, SPACING.md),
        )

        reset_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.RESTORE, size=16),
                ft.Text("Reset All", size=12),
            ], spacing=SPACING.sm),
            padding=ft.padding.symmetric(horizontal=SPACING.md, vertical=SPACING.sm),
            border_radius=ft.BorderRadius(SPACING.sm, 0, 0, SPACING.sm),
            on_click=self._on_reset_all_click,
            cursor=ft.MouseCursor.CLICKER,
        )

        sidebar_content = ft.Column(
            category_buttons + [divider, reset_btn],
            spacing=2,
        )

        sidebar = ft.Container(
            content=sidebar_content,
            width=180,
            bgcolor=self._theme.colors.surface_container_low,
            border=ft.border.only(
                right=ft.BorderSide(1, self._theme.colors.outline_variant)
            ),
            padding=ft.padding.only(top=SPACING.md),
        )

        # Set initial selection
        self._update_category_selection()

        return sidebar

    def _build_main_content(self) -> ft.Container:
        """Build the main content area."""
        # Header with search and title
        self._search_field = ft.TextField(
            hint_text="Search settings...",
            prefix_icon=ft.icons.SEARCH,
            border=ft.InputBorder.NONE,
            bgcolor=self._theme.colors.surface_container,
            on_change=self._on_search_change,
            expand=True,
        )

        header = ft.Container(
            content=ft.Row([
                self._search_field,
            ], spacing=SPACING.md),
            padding=SPACING.md,
            bgcolor=self._theme.colors.surface,
        )

        # Category title and description
        self._category_title = ft.Text(
            "",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=self._theme.colors.on_surface,
        )
        self._category_desc = ft.Text(
            "",
            size=13,
            color=self._theme.colors.on_surface_variant,
        )

        category_header = ft.Container(
            content=ft.Column([
                self._category_title,
                self._category_desc,
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=SPACING.lg, vertical=SPACING.md),
        )

        # Results count (for search)
        self._results_count = ft.Text(
            "",
            size=12,
            color=self._theme.colors.on_surface_variant,
        )

        # Content area for settings items
        self._content_area = ft.Column(
            [],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        main_column = ft.Column([
            header,
            category_header,
            self._results_count,
            ft.Divider(height=1),
            self._content_area,
        ], expand=True)

        return ft.Container(
            content=main_column,
            expand=True,
            padding=ft.padding.only(bottom=SPACING.lg),
        )

    def _select_category(self, category: SettingsCategory):
        """Select a category and update display."""
        self._current_category = category
        self._search_query = ""
        if self._search_field:
            self._search_field.value = ""
        self._update_category_selection()
        self._update_content()

    def _update_category_selection(self):
        """Update visual selection state of category buttons."""
        for cat, btn in self._category_buttons.items():
            if cat == self._current_category:
                btn.bgcolor = self._theme.colors.primary_container
            else:
                btn.bgcolor = None

    def _on_search_change(self, e):
        """Handle search input change."""
        self._search_query = e.control.value.lower()
        self._update_content()

    def _update_content(self):
        """Update the content area based on selection/search."""
        # Filter definitions
        filtered = self._filter_definitions()

        # Update header
        if self._search_query:
            self._category_title.value = f"Search Results"
            self._category_desc.value = f"Showing {len(filtered)} result(s)"
            self._results_count.value = ""
        else:
            title, icon, desc = self.CATEGORY_INFO[self._current_category]
            self._category_title.value = title
            self._category_desc.value = desc
            self._results_count.value = f"{len(filtered)} settings"

        # Build content
        self._content_area.controls.clear()
        self._settings_items.clear()

        # Group by subcategory or add hardware status for relevant categories
        if self._current_category == SettingsCategory.MODELS and not self._search_query:
            self._add_hardware_status()

        for definition in filtered:
            item = self._create_settings_item(definition)
            self._content_area.controls.append(item)
            self._settings_items[definition.key] = item

        # Add model manager link for models category
        if (self._current_category == SettingsCategory.MODELS and
                not self._search_query and self._on_open_model_manager):
            self._content_area.controls.append(
                ft.Container(
                    content=ft.TextButton(
                        "Browse All Models \u2192",
                        icon=ft.icons.MODEL_TRAINING,
                        on_click=self._on_open_model_manager,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING.lg, vertical=SPACING.sm),
                )
            )

        # Update UI
        if self._category_title.page:
            self._category_title.page.update()

    def _filter_definitions(self) -> List[SettingDefinition]:
        """Filter settings definitions based on category/search."""
        if not self._search_query:
            # Filter by category
            return [
                d for d in self._definitions
                if d.category == self._current_category
            ]

        # Search filter
        results = []
        for d in self._definitions:
            # Search in title, description, and keywords
            search_text = (
                d.title.lower() + " " +
                d.description.lower() + " " +
                " ".join(d.search_keywords).lower()
            )
            if self._search_query in search_text:
                results.append(d)

        return results

    def _add_hardware_status(self):
        """Add hardware status display."""
        status_text = ft.Text(
            "Detecting hardware...",
            size=12,
            color=self._theme.colors.on_surface_variant,
        )

        # Will be updated by hardware detection
        self._hardware_status_text = status_text

        status_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.DEVICES, size=16),
                    ft.Text(
                        "Hardware Detection",
                        size=13,
                        weight=ft.FontWeight.MEDIUM,
                    ),
                ], spacing=SPACING.sm),
                status_text,
            ], spacing=SPACING.xs),
            padding=SPACING.md,
            bgcolor=self._theme.colors.surface_container_low,
            border_radius=BORDER_RADIUS.md,
            margin=ft.Margin(SPACING.md, SPACING.md, 0, SPACING.md),
        )

        self._content_area.controls.append(status_card)

    def _create_settings_item(self, definition: SettingDefinition) -> ft.Container:
        """Create a settings item UI."""
        # Get current value
        value = self._get_setting_value(definition.key)

        # Create item container
        item = ft.Container(
            content=SettingsItem(
                definition=definition,
                value=value,
                on_change=self._on_setting_change,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING.lg, vertical=2),
        )

        return item

    def _get_setting_value(self, key: str) -> Any:
        """Get the current value for a setting key."""
        settings = self.settings_service.settings
        if not settings:
            return None

        # Handle text processing sub-settings
        if key.startswith("tp_"):
            tp_settings = settings.get_text_processing_settings()
            attr_name = key[3:]  # Remove "tp_" prefix
            return getattr(tp_settings, attr_name, None)

        # Handle accessibility sub-settings
        if key.startswith("a11y_"):
            a11y_manager = get_accessibility_manager()
            a11y_settings = a11y_manager.settings
            setting_name = key[5:]  # Remove "a11y_" prefix

            if setting_name == "font_size":
                # Map font size scale to string
                scale = a11y_settings.font_size_scale
                if scale <= 0.9:
                    return "small"
                elif scale <= 1.05:
                    return "normal"
                elif scale <= 1.2:
                    return "large"
                else:
                    return "extra_large"

            elif setting_name == "high_contrast":
                return a11y_settings.enable_high_contrast

            elif setting_name == "contrast_mode":
                return a11y_settings.contrast_mode.value

            elif setting_name == "focus_indicators":
                return a11y_settings.enable_focus_indicators

            elif setting_name == "screen_reader":
                return a11y_settings.enable_screen_reader

            elif setting_name == "reduce_motion":
                return a11y_settings.reduce_motion

        # Handle responsive settings
        if key == "compact_mode":
            from ..responsive import get_responsive_manager
            resp_manager = get_responsive_manager()
            return resp_manager.state.is_compact

        # Direct settings
        return getattr(settings, key, None)

    def _on_setting_change(self, key: str, value: Any):
        """Handle setting value change."""
        self._pending_changes[key] = value

    def _on_reset_all_click(self, e):
        """Handle reset all settings button click."""
        if not self.page:
            return

        def confirm_reset(reset_e):
            # Reset to defaults by creating a new default settings object
            from ..settings import Settings

            default_settings = Settings(
                device_name="default",
                model_type="whisper",
                model_name="large-v3",
                compute_type="float16",
                device="cpu",
                language="en",
                hotkey="pause",
                history_hotkey="ctrl+shift+h",
                activation_mode="hold",
                history_max_items=50,
                privacy_mode=False,
                onboarding_completed=False,
                enable_streaming=False,
                auto_copy_on_release=True,
                confidence_threshold=0.5,
                stream_chunk_duration=3.0,
                theme_mode="system",
                history_retention_days=30,
                history_confirm_clear=True,
                history_backup_enabled=False,
                text_processing={
                    "remove_filler_words": True,
                    "auto_capitalize": True,
                    "auto_punctuate": True,
                    "format_numbers": False,
                    "expand_acronyms": False,
                    "use_dictionary": True,
                    "filler_aggressiveness": 0.5,
                    "capitalization_style": "sentence",
                    "punctuation_style": "minimal",
                    "number_style": "commas",
                    "dictionary_fuzzy_matching": True,
                    "tone_preset": "neutral",
                    "tone_preset_enabled": False,
                },
                voice_commands={"enabled": True},
            )

            # Apply default values to settings service
            self.settings_service._settings = default_settings
            self.settings_service.save()

            # Clear pending changes and reload
            self._pending_changes.clear()
            self._update_content()
            self.page.close(dialog)

            # Show success message
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Settings reset to defaults"),
                    bgcolor=self._theme.colors.success_container,
                    duration=2000,
                )
            )

        def cancel_reset(reset_e):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Row(
                [ft.Icon(ft.icons.WARNING, color=self._theme.colors.warning),
                 ft.Text("Reset All Settings")],
                spacing=SPACING.sm,
            ),
            content=ft.Column(
                [
                    ft.Text(
                        "This will reset all settings to their default values. "
                        "This action cannot be undone."
                    ),
                    ft.Text(
                        "Are you sure you want to continue?",
                        size=12,
                        color=self._theme.colors.on_surface_variant,
                    ),
                ],
                spacing=SPACING.sm,
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_reset),
                ft.ElevatedButton(
                    "Reset All",
                    bgcolor=self._theme.colors.error,
                    color=self._theme.colors.on_error,
                    on_click=confirm_reset,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _run_hardware_detection(self):
        """Run hardware detection in background."""
        import threading

        def detect():
            self._hardware_info = self._hardware_detector.detect()
            self._update_hardware_display()

        threading.Thread(target=detect, daemon=True).start()

    def _update_hardware_display(self):
        """Update hardware display with detection results."""
        if not self._hardware_info or not hasattr(self, '_hardware_status_text'):
            return

        if self._hardware_info.has_cuda:
            status = f"GPU: {self._hardware_info.gpu_name}"
            if self._hardware_info.vram_total_mb:
                status += f" ({format_vram_size(self._hardware_info.vram_total_mb)} VRAM)"
            color = self._theme.colors.success
        else:
            status = "CPU mode (no CUDA GPU detected)"
            color = self._theme.colors.warning

        self._hardware_status_text.value = status
        self._hardware_status_text.color = color

        # Update recommended settings
        if self._hardware_info.recommended_device:
            device_key = "device"
            if device_key in self._pending_changes:
                self._pending_changes[device_key] = self._hardware_info.recommended_device
        if self._hardware_info.recommended_compute_type:
            compute_key = "compute_type"
            if compute_key in self._pending_changes:
                self._pending_changes[compute_key] = self._hardware_info.recommended_compute_type

        # Update UI
        if self._hardware_status_text.page:
            self._hardware_status_text.page.update()

    def save(self) -> bool:
        """
        Apply pending changes and save settings.

        Returns
        -------
        bool
            True if save was successful.
        """
        settings = self.settings_service.settings
        if not settings:
            return False

        # Get accessibility manager for accessibility settings
        a11y_manager = get_accessibility_manager()

        # Store special settings that aren't part of Settings object
        special_settings = {}

        # Apply changes
        for key, value in self._pending_changes.items():
            # Handle text processing sub-settings
            if key.startswith("tp_"):
                tp_dict = settings.text_processing or {}
                attr_name = key[3:]  # Remove "tp_" prefix
                tp_dict[attr_name] = value
                settings.text_processing = tp_dict
            # Handle accessibility sub-settings
            elif key.startswith("a11y_"):
                self._apply_accessibility_setting(key, value, a11y_manager)
            # Handle responsive settings
            elif key == "compact_mode":
                from ..responsive import get_responsive_manager
                resp_manager = get_responsive_manager()
                resp_manager.set_compact_mode(value, manual=True)
            # Handle special settings that aren't in Settings object
            elif key == "tray_notifications_enabled":
                special_settings[key] = value
            else:
                # Direct setting
                setattr(settings, key, value)

        # Save to disk
        success = self.settings_service.save()

        if success:
            # Store special settings to be retrieved after save
            self._special_settings = special_settings
            self._pending_changes.clear()

        return success

    def _apply_accessibility_setting(self, key: str, value: Any, a11y_manager):
        """
        Apply an accessibility setting.

        Parameters
        ----------
        key
            Setting key (with a11y_ prefix).
        value
            Setting value.
        a11y_manager
            Accessibility manager instance.
        """
        setting_name = key[5:]  # Remove "a11y_" prefix

        if setting_name == "font_size":
            # Map string to FontSize enum
            font_size_map = {
                "small": FontSize.SMALL,
                "normal": FontSize.NORMAL,
                "large": FontSize.LARGE,
                "extra_large": FontSize.EXTRA_LARGE,
            }
            a11y_manager.set_font_size(font_size_map.get(value, FontSize.NORMAL))

        elif setting_name == "high_contrast":
            # Get contrast mode value or default to high_contrast
            contrast_mode_key = self._pending_changes.get("a11y_contrast_mode", "high_contrast")
            contrast_mode_map = {
                "high_contrast": ContrastMode.HIGH_CONTRAST,
                "extra_high_contrast": ContrastMode.EXTRA_HIGH_CONTRAST,
            }
            a11y_manager.set_high_contrast(
                value,
                contrast_mode_map.get(contrast_mode_key, ContrastMode.HIGH_CONTRAST)
            )

        elif setting_name == "contrast_mode":
            # Only apply if high contrast is enabled
            if self._pending_changes.get("a11y_high_contrast", False):
                contrast_mode_map = {
                    "high_contrast": ContrastMode.HIGH_CONTRAST,
                    "extra_high_contrast": ContrastMode.EXTRA_HIGH_CONTRAST,
                }
                a11y_manager.set_high_contrast(True, contrast_mode_map.get(value, ContrastMode.HIGH_CONTRAST))

        elif setting_name == "focus_indicators":
            a11y_manager._settings.enable_focus_indicators = value
            a11y_manager._save_settings()

        elif setting_name == "screen_reader":
            a11y_manager._settings.enable_screen_reader = value
            a11y_manager._save_settings()

        elif setting_name == "reduce_motion":
            a11y_manager.set_reduce_motion(value)

    def has_changes(self) -> bool:
        """Check if there are pending changes."""
        return len(self._pending_changes) > 0

    def get_changes(self) -> Dict[str, Any]:
        """Get pending changes."""
        return self._pending_changes.copy()

    def get_special_settings(self) -> Dict[str, Any]:
        """Get special settings that were applied during save."""
        return self._special_settings.copy()

    @property
    def page(self) -> Optional[ft.Page]:
        """Get the page reference from UI elements."""
        if self._content_area and self._content_area.page:
            return self._content_area.page
        return None
