"""
First-run setup wizard for faster-whisper-hotkey.

This module provides a multi-step wizard for first-time users to configure
the application with hardware detection, model selection, and hotkey setup.

Classes
-------
WizardStep
    Enum of wizard step identifiers.

SetupWizard
    Main setup wizard implementation.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Callable, List

import flet as ft

from ..hardware_detector import HardwareDetector, HardwareInfo, format_vram_size
from ..model_selector import ModelSelector, get_model_selector, ModelRecommendation
from ..model_download import get_model_download_manager, DownloadProgress
from ..settings_service import SettingsService

logger = logging.getLogger(__name__)


class WizardStep:
    """Wizard step identifiers."""
    WELCOME = "welcome"
    HARDWARE = "hardware"
    MODEL_SELECT = "model_select"
    DOWNLOAD = "download"
    HOTKEY = "hotkey"
    TUTORIAL = "tutorial"
    COMPLETE = "complete"


@dataclass
class WizardState:
    """State tracked through the wizard."""
    hardware_info: Optional[HardwareInfo] = None
    selected_model: Optional[str] = None
    selected_language: str = "en"
    hotkey: str = "pause"
    activation_mode: str = "hold"
    download_completed: bool = False
    tutorial_shown: bool = False


class SetupWizard:
    """
    First-run setup wizard with multi-step configuration.

    Steps:
    1. Welcome screen with app overview
    2. Hardware detection (show detected GPU/CPU)
    3. Model selection with recommendations
    4. Download selected model with progress
    5. Hotkey configuration with test
    6. Quick tutorial (how to use push-to-talk)
    7. Ready to use summary
    """

    def __init__(
        self,
        on_complete: Callable[[WizardState], None],
        on_skip: Optional[Callable[[], None]] = None,
        settings_service: Optional[SettingsService] = None,
    ):
        """
        Initialize the setup wizard.

        Parameters
        ----------
        on_complete
            Callback when wizard is completed successfully.
        on_skip
            Callback when wizard is skipped.
        settings_service
            Optional settings service to update.
        """
        self._on_complete = on_complete
        self._on_skip = on_skip
        self._settings_service = settings_service

        # Services
        self._hardware_detector = HardwareDetector()
        self._model_selector = get_model_selector()
        self._download_manager = get_model_download_manager()

        # State
        self._state = WizardState()
        self._current_step = WizardStep.WELCOME
        self._page: Optional[ft.Page] = None

        # UI components
        self._dialog: Optional[ft.AlertDialog] = None
        self._content_column: Optional[ft.Column] = None
        self._progress_bar: Optional[ft.ProgressBar] = None
        self._next_button: Optional[ft.ElevatedButton] = None
        self._back_button: Optional[ft.ElevatedButton] = None
        self._skip_button: Optional[ft.TextButton] = None

    def show(self, page: ft.Page) -> None:
        """
        Show the setup wizard.

        Parameters
        ----------
        page
            Flet page to show the wizard on.
        """
        self._page = page

        # Build dialog
        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.icons.ROCKET_LAUNCH, color=ft.colors.PRIMARY),
                    ft.Text("Welcome to faster-whisper-hotkey"),
                ],
                spacing=8,
            ),
            content=self._build_content(),
            actions=self._build_actions(),
            actions_padding=ft.padding.all(16),
        )

        page.dialog = self._dialog
        self._dialog.open = True
        page.update()

        # Start hardware detection
        self._detect_hardware()

    def _build_content(self) -> ft.Control:
        """Build the main content area."""
        # Progress indicator
        steps = [
            ("Welcome", WizardStep.WELCOME),
            ("Hardware", WizardStep.HARDWARE),
            ("Model", WizardStep.MODEL_SELECT),
            ("Download", WizardStep.DOWNLOAD),
            ("Hotkey", WizardStep.HOTKEY),
            ("Tutorial", WizardStep.TUTORIAL),
            ("Done", WizardStep.COMPLETE),
        ]

        progress_indicators = []
        for i, (label, step) in enumerate(steps):
            is_active = step == self._current_step
            is_past = list(steps.keys()).index(step) < list(steps.keys()).index(self._current_step)

            color = ft.colors.PRIMARY if is_active else (
                ft.colors.GREEN if is_past else ft.colors.OUTLINE_VARIANT
            )

            progress_indicators.append(
                ft.Container(
                    width=24,
                    height=24,
                    border_radius=12,
                    bgcolor=color,
                    content=ft.Icon(
                        ft.icons.CHECK if is_past else None,
                        size=14,
                        color=ft.colors.ON_PRIMARY if is_past else None,
                    ),
                )
            )

            if i < len(steps) - 1:
                progress_indicators.append(
                    ft.Container(
                        width=40,
                        height=2,
                        bgcolor=ft.colors.OUTLINE_VARIANT if not is_past else ft.colors.GREEN,
                    )
                )

        self._progress_bar = ft.Row(
            progress_indicators,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Content column
        self._content_column = ft.Column(
            [self._progress_bar],
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=self._content_column,
            width=600,
            height=450,
        )

    def _build_actions(self) -> ft.Row:
        """Build action buttons."""
        self._back_button = ft.ElevatedButton(
            "Back",
            on_click=self._on_back,
            visible=False,
        )

        self._skip_button = ft.TextButton(
            "Skip Wizard",
            on_click=self._on_skip_wizard,
        )

        self._next_button = ft.ElevatedButton(
            "Next",
            on_click=self._on_next,
            icon=ft.icons.ARROW_FORWARD,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.PRIMARY,
                color=ft.colors.ON_PRIMARY,
            ),
        )

        return ft.Row(
            [self._back_button, ft.Container(expand=True), self._skip_button, self._next_button],
            alignment=ft.MainAxisAlignment.END,
        )

    def _update_step(self) -> None:
        """Update the wizard to show current step."""
        # Clear content
        self._content_column.controls = [self._progress_bar]

        # Update button visibility
        step_order = [
            WizardStep.WELCOME,
            WizardStep.HARDWARE,
            WizardStep.MODEL_SELECT,
            WizardStep.DOWNLOAD,
            WizardStep.HOTKEY,
            WizardStep.TUTORIAL,
            WizardStep.COMPLETE,
        ]
        current_index = step_order.index(self._current_step)

        self._back_button.visible = current_index > 0
        self._skip_button.visible = self._current_step != WizardStep.COMPLETE

        if self._current_step == WizardStep.COMPLETE:
            self._next_button.text = "Finish"
            self._next_button.icon = ft.icons.CHECK
            self._skip_button.visible = False
        else:
            self._next_button.text = "Next"
            self._next_button.icon = ft.icons.ARROW_FORWARD

        # Build step content
        if self._current_step == WizardStep.WELCOME:
            self._build_welcome_step()
        elif self._current_step == WizardStep.HARDWARE:
            self._build_hardware_step()
        elif self._current_step == WizardStep.MODEL_SELECT:
            self._build_model_select_step()
        elif self._current_step == WizardStep.DOWNLOAD:
            self._build_download_step()
        elif self._current_step == WizardStep.HOTKEY:
            self._build_hotkey_step()
        elif self._current_step == WizardStep.TUTORIAL:
            self._build_tutorial_step()
        elif self._current_step == WizardStep.COMPLETE:
            self._build_complete_step()

        # Update dialog
        if self._dialog:
            self._dialog.update()
            if self._page:
                self._page.update()

    def _build_welcome_step(self) -> None:
        """Build welcome screen."""
        content = ft.Column(
            [
                ft.Icon(ft.icons.ROCKET_LAUNCH, size=64, color=ft.colors.PRIMARY),
                ft.Text(
                    "Welcome to faster-whisper-hotkey!",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Let's set up your application in a few quick steps.",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=20),
                ft.Text(
                    "What you'll get:",
                    size=16,
                    weight=ft.FontWeight.MEDIUM,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [ft.Icon(ft.icons.CHECK, color=ft.colors.GREEN, size=20), ft.Text("Push-to-talk transcription")],
                            spacing=8,
                        ),
                        ft.Row(
                            [ft.Icon(ft.icons.CHECK, color=ft.colors.GREEN, size=20), ft.Text("Automatic hardware detection")],
                            spacing=8,
                        ),
                        ft.Row(
                            [ft.Icon(ft.icons.CHECK, color=ft.colors.GREEN, size=20), ft.Text("Optimal model selection")],
                            spacing=8,
                        ),
                        ft.Row(
                            [ft.Icon(ft.icons.CHECK, color=ft.colors.GREEN, size=20), ft.Text("Customizable hotkeys")],
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        self._content_column.controls.append(content)

    def _build_hardware_step(self) -> None:
        """Build hardware detection step."""
        if self._state.hardware_info:
            info = self._state.hardware_info

            if info.has_cuda:
                hardware_text = f"GPU Detected: {info.gpu_name}"
                status_color = ft.colors.GREEN
                details = [
                    f"VRAM: {format_vram_size(info.vram_total_mb)}",
                    f"Recommended Device: CUDA",
                    f"Compute Type: {info.recommended_compute_type}",
                ]
            else:
                hardware_text = "No GPU detected - CPU mode"
                status_color = ft.colors.AMBER
                details = [
                    "CPU-based transcription",
                    "Recommended Device: CPU",
                    "Compute Type: int8",
                ]

            content = ft.Column(
                [
                    ft.Text(
                        "Hardware Detection",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=16),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    width=16,
                                    height=16,
                                    border_radius=8,
                                    bgcolor=status_color,
                                ),
                                ft.Text(
                                    hardware_text,
                                    size=16,
                                    weight=ft.FontWeight.MEDIUM,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.all(16),
                        bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
                        border_radius=8,
                    ),
                    ft.Column(
                        [ft.Text(d, size=14, color=ft.colors.ON_SURFACE_VARIANT) for d in details],
                        spacing=4,
                    ),
                    ft.Divider(height=16),
                    ft.Text(
                        info.reason,
                        size=13,
                        color=ft.colors.ON_SURFACE_VARIANT,
                        italic=True,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        else:
            content = ft.Column(
                [
                    ft.ProgressRing(width=32, height=32),
                    ft.Text("Detecting hardware...", color=ft.colors.ON_SURFACE_VARIANT),
                ],
                spacing=16,
            )

        self._content_column.controls.append(content)

    def _build_model_select_step(self) -> None:
        """Build model selection step."""
        recommendation = self._model_selector.get_first_run_recommendation()

        # Store recommendation
        self._state.selected_model = recommendation.model_name

        content = ft.Column(
            [
                ft.Text(
                    "Select Your Model",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Based on your hardware, we recommend:",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=16),

                # Recommended model card
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.icons.STAR, color=ft.colors.AMBER),
                                    ft.Text(
                                        recommendation.display_name,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Text(
                                recommendation.reason,
                                size=13,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Divider(height=8),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Speed: {'★' * recommendation.estimated_speed}",
                                        size=12,
                                    ),
                                    ft.Text(
                                        f"Accuracy: {'★' * recommendation.estimated_accuracy}",
                                        size=12,
                                    ),
                                ],
                                spacing=16,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.all(16),
                    bgcolor=ft.colors.PRIMARY_CONTAINER,
                    border_radius=12,
                    border=ft.border.all(2, ft.colors.PRIMARY),
                ),

                ft.Divider(height=16),
                ft.Text(
                    f"This will download approximately {self._download_manager.get_model_info(recommendation.model_name).size_mb if self._download_manager.get_model_info(recommendation.model_name) else 'unknown'} MB.",
                    size=12,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self._content_column.controls.append(content)

    def _build_download_step(self) -> None:
        """Build model download step."""
        if not self._state.selected_model:
            self._start_download()
            return

        progress = self._download_manager.get_download_progress(self._state.selected_model)

        if progress and progress.status == "downloading":
            # Show progress
            content = ft.Column(
                [
                    ft.Text(
                        f"Downloading {self._state.selected_model}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(height=20),
                    ft.ProgressBar(
                        value=progress.percentage / 100,
                        bgcolor=ft.colors.SURFACE_CONTAINER_HIGH,
                        color=ft.colors.PRIMARY,
                        width=400,
                    ),
                    ft.Text(
                        f"{progress.percentage:.0f}% - {progress.speed_formatted} - {progress.eta_formatted}",
                        size=14,
                    ),
                    ft.Text(
                        "This may take a few minutes on first run...",
                        size=12,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        elif progress and progress.status == "completed":
            self._state.download_completed = True
            content = ft.Column(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE, size=48, color=ft.colors.GREEN),
                    ft.Text(
                        "Download Complete!",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"{self._state.selected_model} is ready to use.",
                        size=14,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        elif progress and progress.status == "error":
            content = ft.Column(
                [
                    ft.Icon(ft.icons.ERROR, size=48, color=ft.colors.ERROR),
                    ft.Text(
                        "Download Failed",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        progress.error_message or "An error occurred",
                        size=14,
                        color=ft.colors.ERROR,
                    ),
                    ft.ElevatedButton(
                        "Retry",
                        on_click=lambda _: self._start_download(),
                        icon=ft.icons.REFRESH,
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            # Start download
            self._start_download()
            return

        self._content_column.controls.append(content)

    def _build_hotkey_step(self) -> None:
        """Build hotkey configuration step."""
        content = ft.Column(
            [
                ft.Text(
                    "Configure Your Hotkey",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Choose a key to start/stop recording",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=20),

                ft.Text(
                    f"Selected: {self._state.hotkey.upper()}",
                    size=18,
                    weight=ft.FontWeight.MEDIUM,
                ),

                ft.Divider(height=16),

                ft.Text(
                    "Activation Mode:",
                    size=14,
                    weight=ft.FontWeight.MEDIUM,
                ),

                ft.RadioGroup(
                    content=ft.Column(
                        [
                            ft.Radio(
                                value="hold",
                                label="Hold - Hold key to record, release to transcribe",
                            ),
                            ft.Radio(
                                value="toggle",
                                label="Toggle - Press to start, press again to stop",
                            ),
                        ]
                    ),
                    value=self._state.activation_mode,
                    on_change=lambda e: setattr(self._state, 'activation_mode', e.data),
                ),

                ft.Divider(height=16),
                ft.Text(
                    "Tip: You can change this later in Settings",
                    size=12,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self._content_column.controls.append(content)

    def _build_tutorial_step(self) -> None:
        """Build tutorial step."""
        content = ft.Column(
            [
                ft.Icon(ft.icons.SCHOOL, size=48, color=ft.colors.PRIMARY),
                ft.Text(
                    "How to Use",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(height=20),

                self._build_tutorial_step_item(
                    "1",
                    "Press your hotkey",
                    f"Press {self._state.hotkey.upper()} to start recording",
                ),
                self._build_tutorial_step_item(
                    "2",
                    "Speak",
                    "Talk clearly into your microphone",
                ),
                self._build_tutorial_step_item(
                    "3",
                    "Release or press again",
                    f"{'Release' if self._state.activation_mode == 'hold' else 'Press again'} to transcribe",
                ),
                self._build_tutorial_step_item(
                    "4",
                    "Text appears",
                    "Your transcription appears automatically",
                ),

                ft.Divider(height=16),
                ft.Text(
                    "That's it! You're ready to go.",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._content_column.controls.append(content)

    def _build_tutorial_step_item(self, num: str, title: str, desc: str) -> ft.Container:
        """Build a single tutorial step item."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(num, size=14, weight=ft.FontWeight.BOLD),
                        width=32,
                        height=32,
                        border_radius=16,
                        bgcolor=ft.colors.PRIMARY,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(title, size=14, weight=ft.FontWeight.MEDIUM),
                            ft.Text(desc, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(12),
            bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
        )

    def _build_complete_step(self) -> None:
        """Build completion step."""
        content = ft.Column(
            [
                ft.Icon(ft.icons.CHECK_CIRCLE, size=64, color=ft.colors.GREEN),
                ft.Text(
                    "You're All Set!",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(height=20),

                ft.Text(
                    "Your Configuration:",
                    size=16,
                    weight=ft.FontWeight.MEDIUM,
                ),

                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [ft.Text("Model:", size=13), ft.Text(self._state.selected_model or "base", size=13, weight=ft.FontWeight.BOLD)],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                [ft.Text("Hotkey:", size=13), ft.Text(self._state.hotkey.upper(), size=13, weight=ft.FontWeight.BOLD)],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                [ft.Text("Mode:", size=13), ft.Text(self._state.activation_mode.capitalize(), size=13, weight=ft.FontWeight.BOLD)],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.all(16),
                    bgcolor=ft.colors.SURFACE_CONTAINER_LOW,
                    border_radius=8,
                ),

                ft.Divider(height=20),
                ft.Text(
                    "Click Finish to start using faster-whisper-hotkey!",
                    size=14,
                    color=ft.colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._content_column.controls.append(content)

    # Actions
    def _on_next(self, e) -> None:
        """Handle next button."""
        step_order = [
            WizardStep.WELCOME,
            WizardStep.HARDWARE,
            WizardStep.MODEL_SELECT,
            WizardStep.DOWNLOAD,
            WizardStep.HOTKEY,
            WizardStep.TUTORIAL,
            WizardStep.COMPLETE,
        ]

        current_index = step_order.index(self._current_step)

        # Special handling for download step - wait for completion
        if self._current_step == WizardStep.DOWNLOAD and not self._state.download_completed:
            return  # Don't allow proceeding until download completes

        if current_index < len(step_order) - 1:
            self._current_step = step_order[current_index + 1]
            self._update_step()

    def _on_back(self, e) -> None:
        """Handle back button."""
        step_order = [
            WizardStep.WELCOME,
            WizardStep.HARDWARE,
            WizardStep.MODEL_SELECT,
            WizardStep.DOWNLOAD,
            WizardStep.HOTKEY,
            WizardStep.TUTORIAL,
            WizardStep.COMPLETE,
        ]

        current_index = step_order.index(self._current_step)

        if current_index > 0:
            self._current_step = step_order[current_index - 1]
            self._update_step()

    def _on_skip_wizard(self, e) -> None:
        """Handle skip wizard button."""
        if self._on_skip:
            self._on_skip()

        if self._dialog:
            self._dialog.open = False
            if self._page:
                self._page.update()

    # Background operations
    def _detect_hardware(self) -> None:
        """Detect hardware in background."""
        def detect():
            self._state.hardware_info = self._hardware_detector.detect()
            self._update_step()

        import threading
        threading.Thread(target=detect, daemon=True).start()

    def _start_download(self, e=None) -> None:
        """Start model download."""
        if not self._state.selected_model:
            return

        # Register progress callback
        def on_progress(progress: DownloadProgress):
            if progress.model_name == self._state.selected_model:
                if self._current_step == WizardStep.DOWNLOAD:
                    self._build_download_step()
                    if self._dialog:
                        self._dialog.update()

        self._download_manager.register_progress_callback(on_progress)

        # Start download
        progress = self._download_manager.download_model(self._state.selected_model)

        if progress.status == "completed":
            self._state.download_completed = True
            self._build_download_step()

    def close(self) -> None:
        """Close the wizard."""
        if self._dialog:
            self._dialog.open = False
            if self._page:
                self._page.update()
