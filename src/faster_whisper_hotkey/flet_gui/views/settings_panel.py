"""
Settings panel view for the Flet GUI.

This module provides the settings interface with model selection, language selection,
device type selection, hotkey configuration, and save functionality.
"""

import logging
from typing import Callable, Optional, List

import flet as ft

from ..settings_service import SettingsService
from ..app_state import AppState
from ..hardware_detector import HardwareDetector, HardwareInfo, format_vram_size

logger = logging.getLogger(__name__)


class SettingsPanel:
    """
    Settings panel with configuration options.

    This panel provides:
    - Model selector dropdown (Whisper models)
    - Language selector dropdown
    - Device type selector (CPU/CUDA with auto-detection)
    - Hotkey configuration input field with live capture
    - Activation mode selector (hold/toggle)
    - Save/Apply button that persists settings
    """

    # Language display names
    LANGUAGE_NAMES = {
        "auto": "Auto-detect",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "nl": "Dutch",
        "pl": "Polish",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "no": "Norwegian",
        "tr": "Turkish",
        "cs": "Czech",
        "el": "Greek",
        "he": "Hebrew",
        "th": "Thai",
        "vi": "Vietnamese",
        "id": "Indonesian",
        "uk": "Ukrainian",
    }

    # Model display names
    MODEL_NAMES = {
        "large-v3": "Large v3 (Recommended)",
        "large-v2": "Large v2",
        "large-v1": "Large v1",
        "medium": "Medium",
        "medium.en": "Medium (English only)",
        "small": "Small",
        "small.en": "Small (English only)",
        "base": "Base",
        "base.en": "Base (English only)",
        "tiny": "Tiny (Fastest)",
        "tiny.en": "Tiny (English only, Fastest)",
        "distil-large-v3": "Distil Large v3 (Faster, English only)",
        "distil-large-v2": "Distil Large v2 (Faster, English only)",
        "distil-medium.en": "Distil Medium (Faster, English only)",
        "distil-small.en": "Distil Small (Fastest, English only)",
    }

    def __init__(
        self,
        settings_service: SettingsService,
        app_state: AppState,
        on_save: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        on_open_model_manager: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the settings panel.

        Parameters
        ----------
        settings_service
            Settings management service.
        app_state
            Shared application state.
        on_save
            Callback when settings are saved.
        on_cancel
            Callback when settings are cancelled.
        on_open_model_manager
            Callback to open the model manager.
        """
        self.settings_service = settings_service
        self.app_state = app_state
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._on_open_model_manager = on_open_model_manager

        # Hardware detection
        self._hardware_detector = HardwareDetector()
        self._hardware_info: Optional[HardwareInfo] = None

        # UI components
        self._model_dropdown: Optional[ft.Dropdown] = None
        self._language_dropdown: Optional[ft.Dropdown] = None
        self._device_dropdown: Optional[ft.Dropdown] = None
        self._compute_type_dropdown: Optional[ft.Dropdown] = None
        self._hotkey_field: Optional[ft.TextField] = None
        self._activation_mode_dropdown: Optional[ft.Dropdown] = None
        self._hotkey_capture_status: Optional[ft.Text] = None
        self._is_capturing_hotkey = False
        self._captured_keys: List[str] = []
        self._hardware_status_text: Optional[ft.Text] = None
        self._model_status_text: Optional[ft.Text] = None

    def build(self) -> ft.Container:
        """
        Build the settings panel UI.

        Returns
        -------
        ft.Container
            The settings panel container.
        """
        # Model selector
        self._model_dropdown = ft.Dropdown(
            label="Model",
            hint_text="Select transcription model",
            options=[ft.dropdown_option(m, self.MODEL_NAMES.get(m, m)) for m in SettingsService.ACCEPTED_MODELS],
            width=300,
            expand=True,
        )

        # Language selector
        language_options = [
            ft.dropdown_option(lang, self.LANGUAGE_NAMES.get(lang, lang.upper()))
            for lang in SettingsService.ACCEPTED_LANGUAGES
        ]
        self._language_dropdown = ft.Dropdown(
            label="Language",
            hint_text="Select transcription language",
            options=language_options,
            width=300,
            expand=True,
        )

        # Device type selector
        self._device_dropdown = ft.Dropdown(
            label="Device",
            hint_text="Select compute device",
            options=[
                ft.dropdown_option("cpu", "CPU (Slower, compatible)"),
                ft.dropdown_option("cuda", "CUDA GPU (Faster, requires NVIDIA)"),
            ],
            width=300,
            expand=True,
        )

        # Compute type selector
        self._compute_type_dropdown = ft.Dropdown(
            label="Compute Type",
            hint_text="Select computation precision",
            options=[
                ft.dropdown_option("float16", "Float16 (Best quality, GPU recommended)"),
                ft.dropdown_option("int8", "Int8 (Faster, slightly less accurate)"),
            ],
            width=300,
            expand=True,
        )

        # Hotkey input with capture button
        self._hotkey_field = ft.TextField(
            label="Hotkey",
            hint_text="e.g., pause, f1, ctrl+shift+h",
            width=200,
            read_only=True,
        )

        self._hotkey_capture_status = ft.Text(
            "Click 'Capture' to record a hotkey",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )

        hotkey_capture_button = ft.ElevatedButton(
            "Capture",
            on_click=self._start_hotkey_capture,
            icon=ft.icons.KEYBOARD,
        )

        # Activation mode selector
        self._activation_mode_dropdown = ft.Dropdown(
            label="Activation Mode",
            hint_text="How the hotkey triggers recording",
            options=[
                ft.dropdown_option("hold", "Hold (Hold key to record, release to transcribe)"),
                ft.dropdown_option("toggle", "Toggle (Press to start, press again to stop)"),
            ],
            width=300,
            expand=True,
        )

        # Build the panel layout
        panel = ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Icon(ft.icons.SETTINGS, size=24, color=ft.colors.PRIMARY),
                            ft.Text(
                                "Settings",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.ON_SURFACE,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=20),

                    # Hardware detection section (new)
                    ft.Text(
                        "Hardware Detection",
                        size=14,
                        weight=ft.FontWeight.MEDIUM,
                        color=ft.colors.ON_SURFACE,
                    ),
                    self._build_hardware_status(),

                    ft.Divider(height=20),

                    # Model settings section
                    ft.Row(
                        [
                            ft.Text(
                                "Model Settings",
                                size=14,
                                weight=ft.FontWeight.MEDIUM,
                                color=ft.colors.ON_SURFACE,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "Browse All Models",
                                icon=ft.icons.MODEL_TRAINING,
                                on_click=self._on_open_model_manager_click,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Column(
                        [self._model_dropdown],
                        spacing=8,
                    ),
                    ft.Column(
                        [self._language_dropdown],
                        spacing=8,
                    ),

                    ft.Divider(height=20),

                    # Device settings section
                    ft.Text(
                        "Device Settings",
                        size=14,
                        weight=ft.FontWeight.MEDIUM,
                        color=ft.colors.ON_SURFACE,
                    ),
                    ft.Column(
                        [self._device_dropdown],
                        spacing=8,
                    ),
                    ft.Column(
                        [self._compute_type_dropdown],
                        spacing=8,
                    ),

                    ft.Divider(height=20),

                    # Hotkey settings section
                    ft.Text(
                        "Hotkey Settings",
                        size=14,
                        weight=ft.FontWeight.MEDIUM,
                        color=ft.colors.ON_SURFACE,
                    ),
                    ft.Row(
                        [self._hotkey_field, hotkey_capture_button],
                        spacing=12,
                    ),
                    self._hotkey_capture_status,
                    ft.Column(
                        [self._activation_mode_dropdown],
                        spacing=8,
                    ),

                    ft.Divider(height=30),

                    # Action buttons
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Cancel",
                                on_click=self._on_cancel_click,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
                                    color=ft.colors.ON_SURFACE,
                                ),
                            ),
                            ft.ElevatedButton(
                                "Save",
                                on_click=self._on_save_click,
                                icon=ft.icons.SAVE,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.colors.PRIMARY,
                                    color=ft.colors.ON_PRIMARY,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=12,
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.all(24),
            expand=True,
        )

        # Load current settings into UI
        self._load_current_settings()

        # Run hardware detection
        self._run_hardware_detection()

        return panel

    def _load_current_settings(self):
        """Load current settings into the UI fields."""
        settings = self.settings_service.settings
        if not settings:
            return

        # Set dropdown values
        self._model_dropdown.value = settings.model_name
        self._language_dropdown.value = settings.language
        self._device_dropdown.value = settings.device
        self._compute_type_dropdown.value = settings.compute_type
        self._hotkey_field.value = settings.hotkey
        self._activation_mode_dropdown.value = getattr(settings, 'activation_mode', 'hold')

    def _start_hotkey_capture(self, e):
        """Start capturing a hotkey combination."""
        self._is_capturing_hotkey = True
        self._captured_keys = []
        self._hotkey_capture_status.value = "Press your hotkey combination now..."
        self._hotkey_capture_status.color = ft.colors.AMBER
        self._hotkey_field.value = ""

        # In a real implementation, this would use pynput to capture keys
        # For MVP, we'll show a dialog for input
        self._show_hotkey_dialog()

    def _show_hotkey_dialog(self):
        """Show a dialog for manual hotkey input (MVP approach)."""
        if not self._hotkey_field.page:
            return

        temp_hotkey = ft.TextField(
            label="Enter hotkey",
            hint_text="e.g., pause, f1, ctrl+shift+h",
            value=self._hotkey_field.value or "",
            autofocus=True,
        )

        def save_hotkey(e):
            hotkey = temp_hotkey.value.strip().lower()
            if hotkey:
                is_valid, error = SettingsService.validate_hotkey(hotkey)
                if is_valid:
                    self._hotkey_field.value = hotkey
                    self._hotkey_capture_status.value = f"Hotkey set: {hotkey.upper()}"
                    self._hotkey_capture_status.color = ft.colors.GREEN
                    self._hotkey_field.page.close(dialog)
                else:
                    self._hotkey_capture_status.value = f"Invalid hotkey: {error}"
                    self._hotkey_capture_status.color = ft.colors.ERROR

        def cancel_dialog(e):
            self._hotkey_field.page.close(dialog)
            self._hotkey_capture_status.value = "Click 'Capture' to record a hotkey"
            self._hotkey_capture_status.color = ft.colors.ON_SURFACE_VARIANT

        dialog = ft.AlertDialog(
            title=ft.Text("Set Hotkey"),
            content=ft.Column(
                [temp_hotkey],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_dialog),
                ft.TextButton("Set", on_click=save_hotkey),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._hotkey_field.page.dialog = dialog
        dialog.open = True
        self._hotkey_field.page.update()

    def _on_save_click(self, e):
        """Handle save button click."""
        # Validate inputs
        model = self._model_dropdown.value
        language = self._language_dropdown.value
        device = self._device_dropdown.value
        compute_type = self._compute_type_dropdown.value
        hotkey = self._hotkey_field.value
        activation_mode = self._activation_mode_dropdown.value

        # Validate all settings
        if not SettingsService.validate_model(model):
            self._show_error("Invalid model selected")
            return

        if not SettingsService.validate_language(language):
            self._show_error("Invalid language selected")
            return

        if not SettingsService.validate_device(device):
            self._show_error("Invalid device selected")
            return

        if compute_type not in SettingsService.ACCEPTED_COMPUTE_TYPES:
            self._show_error("Invalid compute type selected")
            return

        is_valid, error = SettingsService.validate_hotkey(hotkey)
        if not is_valid:
            self._show_error(f"Invalid hotkey: {error}")
            return

        if activation_mode not in SettingsService.ACTIVATION_MODES:
            self._show_error("Invalid activation mode")
            return

        # Apply settings
        self.settings_service.set_model_name(model, notify=False)
        self.settings_service.set_language(language, notify=False)
        self.settings_service.set_device(device, notify=False)
        settings = self.settings_service.settings
        settings.compute_type = compute_type
        settings.hotkey = hotkey
        settings.activation_mode = activation_mode

        # Save to disk
        if self.settings_service.save():
            # Update app state
            self.app_state.update_from_settings(settings)

            # Show success message
            self._show_success("Settings saved successfully")

            # Notify callback
            if self._on_save:
                self._on_save()
        else:
            self._show_error("Failed to save settings")

    def _on_cancel_click(self, e):
        """Handle cancel button click."""
        # Reload original settings
        self._load_current_settings()

        # Notify callback
        if self._on_cancel:
            self._on_cancel()

    def _show_error(self, message: str):
        """Show an error snackbar."""
        if self._hotkey_field and self._hotkey_field.page:
            self._hotkey_field.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.colors.ERROR_CONTAINER,
                    duration=3000,
                )
            )

    def _show_success(self, message: str):
        """Show a success snackbar."""
        if self._hotkey_field and self._hotkey_field.page:
            self._hotkey_field.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.colors.SUCCESS_CONTAINER,
                    duration=2000,
                )
            )

    # Public properties for accessing UI components
    @property
    def model_dropdown(self) -> Optional[ft.Dropdown]:
        """Get the model dropdown."""
        return self._model_dropdown

    @property
    def language_dropdown(self) -> Optional[ft.Dropdown]:
        """Get the language dropdown."""
        return self._language_dropdown

    @property
    def device_dropdown(self) -> Optional[ft.Dropdown]:
        """Get the device dropdown."""
        return self._device_dropdown

    @property
    def hotkey_field(self) -> Optional[ft.TextField]:
        """Get the hotkey field."""
        return self._hotkey_field

    # Hardware detection methods
    def _build_hardware_status(self) -> ft.Container:
        """Build the hardware detection status display."""
        self._hardware_status_text = ft.Text(
            "Detecting hardware...",
            size=12,
            color=ft.colors.ON_SURFACE_VARIANT,
        )

        return ft.Container(
            content=self._hardware_status_text,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
        )

    def _run_hardware_detection(self) -> None:
        """Run hardware detection in background."""
        def detect():
            self._hardware_info = self._hardware_detector.detect()
            self._update_hardware_display()

        import threading
        threading.Thread(target=detect, daemon=True).start()

    def _update_hardware_display(self) -> None:
        """Update the hardware display with detection results."""
        if not self._hardware_info or not self._hardware_status_text:
            return

        if self._hardware_info.has_cuda:
            status = f"GPU: {self._hardware_info.gpu_name}"
            if self._hardware_info.vram_total_mb:
                status += f" ({format_vram_size(self._hardware_info.vram_total_mb)} VRAM)"
            color = ft.colors.GREEN
        else:
            status = "CPU mode (no GPU detected)"
            color = ft.colors.AMBER

        self._hardware_status_text.value = status
        self._hardware_status_text.color = color

        # Update device dropdown recommendation
        if self._hardware_info.recommended_device:
            self._device_dropdown.value = self._hardware_info.recommended_device
        if self._hardware_info.recommended_compute_type:
            self._compute_type_dropdown.value = self._hardware_info.recommended_compute_type

        # Update UI
        if self._hardware_status_text.page:
            self._hardware_status_text.page.update()

    # Model manager integration
    def _on_open_model_manager_click(self, e) -> None:
        """Handle Browse Models button click."""
        if self._on_open_model_manager:
            self._on_open_model_manager()

    def set_model_status(self, model_name: str, is_installed: bool, status: str = "installed") -> None:
        """
        Update the model status display.

        Parameters
        ----------
        model_name
            Name of the model.
        is_installed
            Whether the model is installed.
        status
            Additional status info.
        """
        # Status text may not be initialized yet
        pass
