"""
Main Flet application for faster-whisper-hotkey.

This module provides the main Flet application window and UI layout.
It integrates the transcription service, settings service, and hotkey manager
into a cohesive application with a modern Windows-first interface.

Classes
-------
FletApp
    Main Flet application class.
"""

import logging
import sys
import threading
import time
from typing import Optional

import flet as ft

from ..settings import load_settings
from ..config import accepted_models_whisper, accepted_languages_whisper
from .app_state import AppState, RecordingState
from .settings_service import SettingsService
from .transcription_service import TranscriptionService
from .hotkey_manager import HotkeyManager
from .tray_manager import TrayManager, RecentItem, ModelInfo, TrayIconState
from .views.transcription_panel import TranscriptionPanel
from .views.modern_transcription_panel import ModernTranscriptionPanel
from .views.settings_panel import SettingsPanel
from .views.modern_settings_panel import ModernSettingsPanel
from .views.history_panel import HistoryPanel
from .views.help_panel import HelpPanel
from .history_manager import HistoryManager
from .auto_paste import get_auto_paste, AutoPasteResult
from .notifications import (
    init_notifications,
    get_notification_manager,
    get_sound_manager,
    SoundNotificationManager,
)
from .accessibility import get_accessibility_manager
from .theme import get_theme_manager
from .responsive import get_responsive_manager, ResponsiveManager
from .wizards.setup_wizard import SetupWizard, WizardState
from .updater import UpdateManager, UpdateDialog, get_update_manager
from .telemetry import (
    get_telemetry_manager,
    init_telemetry,
    shutdown_telemetry,
    EventType,
    FeatureType,
)

logger = logging.getLogger(__name__)


class FletApp:
    """
    Main Flet application for faster-whisper-hotkey.

    This application provides:
    - A main window with header, content area, and controls
    - Push-to-talk transcription functionality
    - Real-time audio level visualization
    - Settings management interface
    - System tray integration (minimize to tray)
    - Hotkey detection in background

    Attributes
    ----------
    page
        The Flet page/control for the main window.
    app_state
        Shared application state.
    settings_service
        Settings management service.
    transcription_service
        Transcription service wrapper.
    hotkey_manager
        Hotkey detection manager.
    """

    def __init__(self, use_modern_ui: bool = True, use_modern_settings: bool = True):
        """
        Initialize the Flet application.

        Parameters
        ----------
        use_modern_ui
            Whether to use the modern UI design.
        use_modern_settings
            Whether to use the modern settings panel.
        """
        self.page: Optional[ft.Page] = None
        self.app_state = AppState()
        self.settings_service = SettingsService()
        self.history_manager = HistoryManager()
        self.auto_paste = get_auto_paste()
        self.transcription_service: Optional[TranscriptionService] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.tray_manager: Optional[TrayManager] = None
        self._is_shutting_down = False
        self._use_modern_ui = use_modern_ui
        self._use_modern_settings = use_modern_settings

        # Accessibility and theme managers
        self.accessibility_manager = get_accessibility_manager()
        self.theme_manager = get_theme_manager()

        # Responsive manager
        self.responsive_manager = get_responsive_manager()

        # UI references
        self._status_indicator: Optional[ft.Container] = None
        self._status_text: Optional[ft.Text] = None
        self._hotkey_display: Optional[ft.Text] = None
        self._content_stack: Optional[ft.Stack] = None
        self._main_column: Optional[ft.Column] = None

        # Views
        self._transcription_panel: Optional[TranscriptionPanel] = None
        self._modern_transcription_panel: Optional[ModernTranscriptionPanel] = None
        self._settings_panel: Optional[SettingsPanel] = None
        self._modern_settings_panel: Optional[ModernSettingsPanel] = None
        self._history_panel: Optional[HistoryPanel] = None
        self._help_panel: Optional[HelpPanel] = None
        self._model_manager_panel = None  # Will be initialized when needed
        self._current_view = "transcription"  # "transcription", "settings", "history", "help", or "models"
        self._setup_wizard: Optional[SetupWizard] = None

        # Update manager
        self.update_manager: Optional[UpdateManager] = None
        self._update_dialog: Optional[UpdateDialog] = None

        # Telemetry manager
        self.telemetry_manager = get_telemetry_manager()

    def build(self, page: ft.Page):
        """
        Build the main Flet application UI.

        Parameters
        ----------
        page
            The Flet page to build the UI on.
        """
        self.page = page
        page.title = "faster-whisper-hotkey"
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.window_width = 500 if not self._use_modern_ui else 450
        page.window_height = 700
        # Set minimum supported resolution
        page.window_min_width = ResponsiveManager.MIN_WIDTH
        page.window_min_height = ResponsiveManager.MIN_HEIGHT
        page.padding = 0
        page.bgcolor = ft.colors.SURFACE_CONTAINER_LOWEST if hasattr(ft.colors, 'SURFACE_CONTAINER_LOWEST') else ft.colors.GREY_50

        # Attach responsive manager to page for resize handling
        self.responsive_manager.attach_to_page(page)

        # Apply accessibility settings
        # Link accessibility manager to theme manager for adaptive theming
        self.theme_manager.set_accessibility_manager(self.accessibility_manager)

        # Apply theme with accessibility adaptations
        self.theme_manager.apply_to_page(page)

        # Handle window events
        page.window_prevent_close = True
        page.on_window_event = self._on_window_event

        # Create the main column for view switching
        self._main_column = ft.Column(
            [
                self._build_header(),
                ft.Divider(height=1),
                self._build_content_area(),
            ],
            spacing=0,
            expand=True,
        )

        # Build the main UI
        page.add(self._main_column)

        # Initialize services after UI is built
        self._initialize_services()

        # Start the event processing timer
        self._start_event_processing()

    def _build_content_area(self) -> ft.Container:
        """Build the main content area that switches between views."""
        # Create panels
        if self._use_modern_ui:
            self._modern_transcription_panel = ModernTranscriptionPanel(
                self.app_state,
                self.history_manager,
                on_copy=self._copy_transcription,
                on_paste=self._paste_transcription,
                on_recent_click=self._on_recent_transcription_click,
                responsive_manager=self.responsive_manager,
            )
        else:
            self._transcription_panel = TranscriptionPanel(
                self.app_state,
                on_copy=self._copy_transcription,
                on_paste=self._paste_transcription,
            )

        # Create settings panel based on flag
        if self._use_modern_settings:
            self._modern_settings_panel = ModernSettingsPanel(
                self.settings_service,
                self.app_state,
                on_save=self._on_settings_saved,
                on_cancel=self._on_settings_cancelled,
                on_open_model_manager=self._on_model_manager_selected,
                on_check_updates=self._on_check_updates_from_settings,
                app_instance=self,
            )
        else:
            self._settings_panel = SettingsPanel(
                self.settings_service,
                self.app_state,
                on_save=self._on_settings_saved,
                on_cancel=self._on_settings_cancelled,
                on_open_model_manager=self._open_model_manager,
            )

        self._history_panel = HistoryPanel(
            self.history_manager,
            self.app_state,
            on_paste=self._paste_to_active_window,
            on_close=lambda: self._switch_view("transcription"),
        )

        # Create help panel
        self._help_panel = HelpPanel(
            on_close=lambda: self._switch_view("transcription"),
            hotkey=self.app_state.hotkey,
            history_hotkey=self.app_state.history_hotkey if hasattr(self.app_state, 'history_hotkey') else "ctrl+shift+h",
        )

        # Build transcription panel with controls
        if self._use_modern_ui:
            transcription_content = ft.Column(
                [
                    self._modern_transcription_panel.build(),
                    self._build_controls(),
                ],
                spacing=0,
                expand=True,
            )
        else:
            transcription_content = ft.Column(
                [
                    self._transcription_panel.build(),
                    self._build_controls(),
                ],
                spacing=0,
                expand=True,
            )

        # Build settings panel with controls
        if self._use_modern_settings:
            # Modern settings has its own controls built-in
            settings_content = ft.Column(
                [
                    self._modern_settings_panel.build(),
                    self._build_modern_settings_controls(),
                ],
                spacing=0,
                expand=True,
            )
        else:
            settings_content = ft.Column(
                [
                    self._settings_panel.build(),
                    self._build_settings_controls(),
                ],
                spacing=0,
                expand=True,
            )

        # Build history panel with controls
        history_content = ft.Column(
            [
                self._history_panel.build(),
                self._build_history_controls(),
            ],
            spacing=0,
            expand=True,
        )

        # Stack for view switching
        self._content_stack = ft.Stack(
            [
                ft.Container(
                    content=transcription_content,
                    expand=True,
                    visible=True,
                    key="transcription",
                ),
                ft.Container(
                    content=settings_content,
                    expand=True,
                    visible=False,
                    key="settings",
                ),
                ft.Container(
                    content=history_content,
                    expand=True,
                    visible=False,
                    key="history",
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            self._help_panel.build(),
                            self._build_help_controls(),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                    visible=False,
                    key="help",
                ),
            ],
            expand=True,
        )

        # Wire up the transcription panel's record button
        if self._use_modern_ui:
            if self._modern_transcription_panel.record_button:
                self._modern_transcription_panel.record_button.on_click = self._on_record_button_click
        else:
            if self._transcription_panel.record_button:
                self._transcription_panel.record_button.on_click = self._on_record_button_click

        # Refresh recent transcriptions for modern panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.refresh_recent_transcriptions()

        return ft.Container(
            content=self._content_stack,
            expand=True,
        )

    def _build_settings_controls(self) -> ft.Container:
        """Build the bottom control panel for settings view."""
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="Back to transcription",
            icon_size=24,
            on_click=lambda _: self._switch_view("transcription"),
        )

        controls = ft.Container(
            content=ft.Row(
                [back_button],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _build_modern_settings_controls(self) -> ft.Container:
        """Build the bottom control panel for modern settings view."""
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="Back to transcription",
            icon_size=24,
            on_click=lambda _: self._on_settings_back_click(),
        )

        save_button = ft.TextButton(
            "Save",
            icon=ft.icons.SAVE,
            on_click=lambda _: self._on_settings_save_click(),
        )

        controls = ft.Container(
            content=ft.Row(
                [back_button, ft.Container(expand=True), save_button],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _on_settings_back_click(self):
        """Handle back button click from modern settings."""
        # Check if there are unsaved changes
        if self._modern_settings_panel and self._modern_settings_panel.has_changes():
            self._show_unsaved_changes_dialog()
        else:
            self._switch_view("transcription")

    def _on_settings_save_click(self):
        """Handle save button click from modern settings."""
        if self._modern_settings_panel:
            if self._modern_settings_panel.save():
                # Reinitialize services if needed
                if self.transcription_service and self.settings_service.settings:
                    self.transcription_service.reinitialize(self.settings_service.settings)

                # Update hotkey manager if hotkey changed
                if self.hotkey_manager:
                    new_hotkey = self.settings_service.get_hotkey()
                    self.hotkey_manager.set_hotkey(new_hotkey)

                    # Update history hotkey
                    new_history_hotkey = self.settings_service.get_history_hotkey()
                    self.hotkey_manager.set_hotkey(new_history_hotkey, name=HotkeyManager.HISTORY_HOTKEY)

                # Update hotkey display
                if self._hotkey_display:
                    self._hotkey_display.text = f"Hotkey: {self.settings_service.get_hotkey().upper()}"

                # Show success and go back
                self._show_snackbar("Settings saved successfully")
                self._switch_view("transcription")
            else:
                self._show_error("Failed to save settings")

    def _show_unsaved_changes_dialog(self):
        """Show dialog for unsaved changes."""
        if not self.page:
            return

        def discard(e):
            if self._modern_settings_panel:
                self._modern_settings_panel._pending_changes.clear()
            self.page.close(dialog)
            self._switch_view("transcription")

        def cancel(e):
            self.page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Unsaved Changes"),
            content=ft.Text("You have unsaved changes. Do you want to discard them?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton("Discard", on_click=discard, style=ft.ButtonStyle(color=ft.colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_model_manager_selected(self, model_name: str):
        """
        Handle model selection from model manager (for modern settings).

        Parameters
        ----------
        model_name
            Selected model identifier.
        """
        # Update settings
        self.settings_service.set_model_name(model_name)

        # Update app state
        if self.settings_service.settings:
            self.app_state.update_from_settings(self.settings_service.settings)

        # Show success message
        self._show_snackbar(f"Model changed to {model_name}")

        # Go back to settings
        self._switch_view("settings")

        # Reinitialize transcription service with new model
        if self.transcription_service and self.settings_service.settings:
            self.transcription_service.reinitialize(self.settings_service.settings)

    def _build_history_controls(self) -> ft.Container:
        """Build the bottom control panel for history view."""
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="Back to transcription",
            icon_size=24,
            on_click=lambda _: self._switch_view("transcription"),
        )

        controls = ft.Container(
            content=ft.Row(
                [back_button],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _build_help_controls(self) -> ft.Container:
        """Build the bottom control panel for help view."""
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="Back to transcription",
            icon_size=24,
            on_click=lambda _: self._switch_view("transcription"),
        )

        controls = ft.Container(
            content=ft.Row(
                [back_button],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _switch_view(self, view: str):
        """
        Switch between transcription, settings, history, help, and models views.

        Parameters
        ----------
        view
            The view to switch to: "transcription", "settings", "history", "help", or "models".
        """
        if not self._content_stack:
            return

        self._current_view = view

        # Update visibility
        for control in self._content_stack.controls:
            if isinstance(control, ft.Container):
                if control.key == view:
                    control.visible = True
                else:
                    control.visible = False

        # Update page
        if self.page:
            self.page.update()

    def _on_settings_saved(self):
        """Handle settings save."""
        # Reinitialize transcription service with new settings
        if self.transcription_service and self.settings_service.settings:
            self.transcription_service.reinitialize(self.settings_service.settings)

        # Update hotkey manager if hotkey changed
        if self.hotkey_manager:
            new_hotkey = self.settings_service.get_hotkey()
            self.hotkey_manager.set_hotkey(new_hotkey)

            # Update history hotkey
            new_history_hotkey = self.settings_service.get_history_hotkey()
            self.hotkey_manager.set_hotkey(new_history_hotkey, name=HotkeyManager.HISTORY_HOTKEY)

        # Update hotkey display
        if self._hotkey_display:
            self._hotkey_display.text = f"Hotkey: {self.settings_service.get_hotkey().upper()}"

        # Update tray notification setting
        if self.tray_manager and self._modern_settings_panel:
            # Check if the tray notifications setting was changed
            special_settings = self._modern_settings_panel.get_special_settings()
            if "tray_notifications_enabled" in special_settings:
                self.tray_manager.set_tray_notifications_enabled(special_settings["tray_notifications_enabled"])

        # Switch back to transcription view
        self._switch_view("transcription")

        # Show success message
        self._show_snackbar("Settings saved successfully")

        # Play sound notification
        if self.sound_manager:
            self.sound_manager.play(SoundNotificationManager.EVENT_SETTINGS_SAVED)

    def _on_settings_cancelled(self):
        """Handle settings cancel."""
        self._switch_view("transcription")

    def _build_header(self) -> ft.Container:
        """Build the header section with title and status."""
        self._status_indicator = ft.Container(
            width=12,
            height=12,
            border_radius=6,
            bgcolor=ft.colors.GREEN,
        )

        self._status_text = ft.Text(
            "Ready",
            color=ft.colors.ON_SURFACE,
            size=14,
        )

        self._hotkey_display = ft.Text(
            f"Hotkey: {self.app_state.hotkey.upper()}",
            color=ft.colors.ON_SURFACE_VARIANT,
            size=12,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "faster-whisper-hotkey",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.PRIMARY,
                            ),
                            ft.Row(
                                [self._status_indicator, self._status_text],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            self._hotkey_display,
                            ft.Text(
                                "v0.4.3",
                                size=10,
                                color=ft.colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAlignment.END,
                        spacing=4,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return header

    def _build_controls(self) -> ft.Container:
        """Build the bottom control panel."""
        history_button = ft.IconButton(
            icon=ft.icons.HISTORY,
            tooltip="History",
            icon_size=24,
            on_click=self._open_history,
        )

        help_button = ft.IconButton(
            icon=ft.icons.HELP_OUTLINE,
            tooltip="Help",
            icon_size=24,
            on_click=self._open_help,
        )

        settings_button = ft.IconButton(
            icon=ft.icons.SETTINGS,
            tooltip="Settings",
            icon_size=24,
            on_click=self._open_settings,
        )

        minimize_button = ft.IconButton(
            icon=ft.icons.MINIMIZE,
            tooltip="Minimize to tray",
            icon_size=24,
            on_click=self._minimize_to_tray,
        )

        controls = ft.Container(
            content=ft.Row(
                [
                    ft.Container(expand=True),
                    history_button,
                    help_button,
                    settings_button,
                    minimize_button,
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _initialize_services(self):
        """Initialize the background services."""
        # Load settings
        settings = self.settings_service.load()
        if settings:
            self.app_state.update_from_settings(settings)
            self._hotkey_display.text = f"Hotkey: {settings.hotkey.upper()}"
        else:
            # Use defaults
            self._show_error("Failed to load settings. Using defaults.")

        # Initialize transcription service
        self.transcription_service = TranscriptionService(settings or self._create_default_settings())

        # Register callbacks
        self.transcription_service.on("state_change", self._on_state_change)
        self.transcription_service.on("transcription", self._on_transcription)
        self.transcription_service.on("transcription_start", self._on_transcription_start)
        self.transcription_service.on("audio_level", self._on_audio_level)
        self.transcription_service.on("error", self._on_error)

        # Initialize the transcriber
        if not self.transcription_service.initialize():
            self._show_error("Failed to initialize transcription service")

        # Initialize hotkey manager
        hotkey = self.app_state.hotkey
        self.hotkey_manager = HotkeyManager(hotkey)

        # Register the history hotkey
        history_hotkey = getattr(settings, 'history_hotkey', "ctrl+shift+h")
        self.hotkey_manager.set_hotkey(history_hotkey, name=HotkeyManager.HISTORY_HOTKEY)

        # Register callbacks
        self.hotkey_manager.on("hotkey_press", self._on_hotkey_press)
        self.hotkey_manager.on("hotkey_release", self._on_hotkey_release)
        self.hotkey_manager.start()

        # Initialize tray manager with enhanced callbacks
        self.tray_manager = TrayManager(
            on_show=self.restore_from_tray,
            on_record_toggle=self._handle_tray_record_toggle,
            on_exit=self._handle_tray_exit,
            on_recent_item_click=self._on_tray_recent_item_click,
            on_open_history=self._open_history_from_tray,
            on_open_settings=self._open_settings_from_tray,
            on_model_selected=self._on_tray_model_selected,
            on_double_click=self._handle_tray_double_click,
        )
        self.tray_manager.start()

        # Initialize notification manager with tray support
        self.notification_manager = init_notifications(
            page,
            tray_manager=self.tray_manager,
            enable_tray_notifications=True,
        )

        # Initialize sound notification manager
        self.sound_manager = get_sound_manager()

        # Initialize tray with recent items from history
        self._update_tray_recent_items()

        # Initialize tray with available models
        self._update_tray_models()

        # Check for first-run and show setup wizard
        self._check_first_run()

        # Initialize update manager
        self._initialize_update_manager()

        # Initialize telemetry manager
        self._initialize_telemetry()

    def _initialize_telemetry(self):
        """Initialize the telemetry manager based on user settings."""
        from ..settings import get_settings_dir

        # Get telemetry enabled setting from settings (opt-in only)
        telemetry_enabled = False
        if settings and hasattr(settings, 'telemetry_enabled'):
            telemetry_enabled = settings.telemetry_enabled

        # Initialize telemetry with settings directory
        self.telemetry_manager = init_telemetry(
            enabled=telemetry_enabled,
            settings_dir=get_settings_dir(),
        )

    def _initialize_update_manager(self):
        """Initialize the auto-update manager."""
        self.update_manager = get_update_manager()

        if self.update_manager and settings:
            # Configure update manager from settings
            self.update_manager.check_frequency = settings.update_check_frequency
            self.update_manager.include_prereleases = settings.update_include_prereleases
            self.update_manager.auto_download = settings.update_auto_download

            # Create update dialog
            self._update_dialog = UpdateDialog(self.update_manager)

            # Check for updates if it's time
            if self.update_manager.should_check_for_updates():
                def on_update_available(update_info):
                    """Show update notification when available."""
                    if self.page and self._update_dialog:
                        self._update_dialog.show_update_available(self.page, update_info)

                # Check in background after a short delay
                self.page.run_thread(
                    lambda: self.update_manager.check_for_updates(on_update_available),
                    delay=3000  # Wait 3 seconds after startup
                )

    def check_for_updates_now(self):
        """
        Manually trigger an update check.

        This can be called from the settings UI when user clicks "Check for Updates".
        """
        if self.update_manager:
            def on_update_available(update_info):
                """Show update notification when available."""
                if self.page and self._update_dialog:
                    self._update_dialog.show_update_available(self.page, update_info)
                else:
                    self._show_snackbar(f"Update available: {update_info.version}")

            def on_no_update():
                """Notify that no updates are available."""
                self._show_snackbar("No updates available")

            # Check in background
            import threading
            def check_and_notify():
                self.update_manager.check_for_updates(on_update_available)
                # If no update found after check, notify
                if not self.update_manager.available_update:
                    self.page.run_thread(on_no_update)

            threading.Thread(target=check_and_notify, daemon=True).start()

    def _on_check_updates_from_settings(self):
        """Callback from settings panel to check for updates."""
        self.check_for_updates_now()

    def _check_first_run(self):
        """Check if this is a first run and show setup wizard if needed."""
        settings = self.settings_service.settings
        if settings and not settings.onboarding_completed:
            # Delay showing wizard slightly to let UI fully load
            self.page.run_thread(self._show_setup_wizard, delay=500)

    def _show_setup_wizard(self):
        """Show the first-run setup wizard."""
        if not self.page:
            return

        def on_wizard_complete(state: WizardState):
            """Handle wizard completion."""
            # Update settings with wizard choices
            if self.settings_service.settings:
                # Update model
                if state.selected_model:
                    self.settings_service.settings.model_name = state.selected_model

                # Update hotkey and activation mode
                if state.hotkey:
                    self.settings_service.settings.hotkey = state.hotkey
                if state.activation_mode:
                    self.settings_service.settings.activation_mode = state.activation_mode

                # Update device/compute type based on hardware detection
                if state.hardware_info:
                    self.settings_service.settings.device = state.hardware_info.recommended_device
                    self.settings_service.settings.compute_type = state.hardware_info.recommended_compute_type

                # Handle analytics opt-in (privacy mode is opposite of analytics enabled)
                self.settings_service.settings.privacy_mode = not state.analytics_enabled

                # Mark onboarding as complete
                self.settings_service.settings.onboarding_completed = True

                # Save settings
                self.settings_service.save()

                # Reinitialize services with new settings
                if self.transcription_service:
                    self.transcription_service.reinitialize(self.settings_service.settings)

                # Update hotkey manager
                if self.hotkey_manager:
                    self.hotkey_manager.set_hotkey(state.hotkey)

                # Update app state
                self.app_state.update_from_settings(self.settings_service.settings)
                if self._hotkey_display:
                    self._hotkey_display.text = f"Hotkey: {state.hotkey.upper()}"

                # Handle auto-start option
                if state.auto_start_enabled:
                    self._enable_auto_start()

            # Close wizard
            if self._setup_wizard:
                self._setup_wizard.close()

        def on_wizard_skip():
            """Handle wizard skip."""
            # Mark onboarding as complete anyway
            if self.settings_service.settings:
                self.settings_service.settings.onboarding_completed = True
                self.settings_service.save()

        # Create and show wizard
        self._setup_wizard = SetupWizard(
            on_complete=on_wizard_complete,
            on_skip=on_wizard_skip,
            settings_service=self.settings_service,
        )
        self._setup_wizard.show(self.page)

    def _enable_auto_start(self):
        """Enable auto-start on Windows boot."""
        try:
            import os
            import shutil

            # Get startup folder path
            startup_folder = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft',
                'Windows',
                'Start Menu',
                'Programs',
                'Startup'
            )

            # Get path to current executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                exe_path = sys.executable
            else:
                # Running as script - skip auto-start for dev
                logger.info("Skipping auto-start setup in development mode")
                return

            # Create shortcut
            shortcut_path = os.path.join(startup_folder, 'faster-whisper-hotkey.lnk')

            # Use PowerShell to create shortcut
            import subprocess
            ps_script = f'''
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{exe_path}"
            $Shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
            $Shortcut.Description = "faster-whisper-hotkey - Push-to-talk transcription"
            $Shortcut.Save()
            '''
            subprocess.run(['powershell', '-Command', ps_script], check=True, capture_output=True)
            logger.info(f"Auto-start shortcut created at {shortcut_path}")

        except Exception as e:
            logger.warning(f"Failed to enable auto-start: {e}")

    def _create_default_settings(self):
        """Create default settings when loading fails."""
        from ..settings import Settings
        return Settings(
            device_name="default",
            model_type="whisper",
            model_name="large-v3",
            compute_type="float16",
            device="cpu",
            language="en",
            hotkey="pause",
        )

    def _start_event_processing(self):
        """Start the event processing timer."""
        def process_events():
            if self._is_shutting_down:
                return

            # Process transcription events
            if self.transcription_service:
                self.transcription_service.process_events()

            # Process hotkey events
            if self.hotkey_manager:
                events = self.hotkey_manager.process_events()
                for event in events:
                    if event.action == "press":
                        # Route based on hotkey name
                        if event.hotkey_name == HotkeyManager.HISTORY_HOTKEY:
                            self._on_history_hotkey_press()
                        else:
                            self._handle_hotkey_press()
                    elif event.action == "release":
                        # Route based on hotkey name
                        if event.hotkey_name == HotkeyManager.HISTORY_HOTKEY:
                            self._on_history_hotkey_release()
                        else:
                            self._handle_hotkey_release()

            # Schedule next processing
            if self.page and not self._is_shutting_down:
                self.page.update()
                self.page.run_thread(process_events, delay=50)

        self.page.run_thread(process_events, delay=50)

    # Event handlers
    def _on_window_event(self, e):
        """Handle window events."""
        if e.data == "close":
            self._minimize_to_tray(None)

    def _on_record_button_click(self, e):
        """Handle record button click."""
        if self.app_state.recording_state == RecordingState.RECORDING:
            self.transcription_service.stop_recording()
        elif self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()

    def _on_hotkey_press(self, event):
        """Handle hotkey press from hotkey manager."""
        if self.app_state.activation_mode == "toggle":
            self._handle_hotkey_press()
        else:
            # Hold mode - handled in release
            pass

    def _on_hotkey_release(self, event):
        """Handle hotkey release from hotkey manager."""
        if self.app_state.activation_mode == "hold":
            self._handle_hotkey_release()

    def _handle_hotkey_press(self):
        """Handle hotkey press action."""
        if self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()
        elif self.app_state.activation_mode == "toggle":
            self.transcription_service.stop_recording()

    def _handle_hotkey_release(self):
        """Handle hotkey release action (hold mode)."""
        if self.app_state.recording_state == RecordingState.RECORDING:
            self.transcription_service.stop_recording()

    def _on_history_hotkey_press(self):
        """
        Handle history hotkey press action.

        Opens the history panel. If the window is minimized to tray,
        it restores the window first. The history panel is refreshed
        and focus is set to allow immediate typing for search.
        """
        # Restore window if minimized to tray
        if not self.app_state.window_visible:
            self.restore_from_tray()

        # Open history panel (this refreshes the history)
        self._open_history(None)

        # Show notification
        self._show_snackbar(f"History opened ({self.hotkey_manager.get_hotkey(HotkeyManager.HISTORY_HOTKEY).upper()})")

    def _on_history_hotkey_release(self):
        """Handle history hotkey release (currently no action needed)."""
        pass

    def _on_state_change(self, state: str):
        """Handle transcription state changes."""
        state_enum = RecordingState(state.lower()) if state.lower() in [s.value for s in RecordingState] else RecordingState.IDLE
        self.app_state.recording_state = state_enum

        # Update UI
        if self._status_text:
            self._status_text.text = state.capitalize()

        if self._status_indicator:
            color_map = {
                RecordingState.IDLE: ft.colors.GREEN,
                RecordingState.RECORDING: ft.colors.RED,
                RecordingState.TRANSCRIBING: ft.colors.AMBER,
                RecordingState.ERROR: ft.colors.RED,
            }
            self._status_indicator.bgcolor = color_map.get(state_enum, ft.colors.GREY)

        # Update panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.update_state(state_enum)
        elif self._transcription_panel:
            self._transcription_panel.update_state(state_enum)

        # Update tray recording state
        if self.tray_manager:
            self.tray_manager.update_recording_state(state_enum == RecordingState.RECORDING)

        # Screen reader announcements for state changes
        state_messages = {
            RecordingState.IDLE: "Ready",
            RecordingState.RECORDING: "Recording started",
            RecordingState.TRANSCRIBING: "Processing audio",
            RecordingState.ERROR: "An error occurred",
        }
        if state_enum in state_messages:
            self.accessibility_manager.announce(state_messages[state_enum], priority="high")

    def _on_transcription(self, text: str):
        """Handle completed transcription."""
        self.app_state.latest_transcription = text

        # Update the appropriate panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.update_transcription(text)
        elif self._transcription_panel:
            self._transcription_panel.update_transcription(text)

        # Save to history
        from datetime import datetime
        from ..history_manager import HistoryItem
        item = HistoryItem(
            timestamp=datetime.now().isoformat(),
            text=text,
            model=self.app_state.model,
            language=self.app_state.language,
            device=self.app_state.device,
        )
        self.history_manager.add_item(item)

        # Track transcription in telemetry (anonymous - word count only)
        if self.telemetry_manager and self.telemetry_manager.is_enabled():
            import re
            word_count = len(re.findall(r'\S+', text)) if text else 0
            device_type = "cuda" if self.app_state.device == "cuda" else "cpu"
            self.telemetry_manager.track_transcription(
                model_name=self.app_state.model or "unknown",
                language=self.app_state.language or "en",
                duration_ms=0,  # Duration is not directly available here
                word_count=word_count,
                device_type=device_type,
            )

        # Update tray with recent items
        self._update_tray_recent_items()

        # Reset tray transcribing state
        if self.tray_manager:
            self.tray_manager.update_transcribing_state(False)

        # Refresh recent transcriptions for modern panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.refresh_recent_transcriptions()

        # Play sound notification
        if self.sound_manager:
            self.sound_manager.play(SoundNotificationManager.EVENT_TRANSCRIPTION_COMPLETE)

        # Screen reader announcement for transcription completion
        self.accessibility_manager.announce(f"Transcription complete: {text[:100]}{'...' if len(text) > 100 else ''}", priority="medium")

    def _on_transcription_start(self, duration: float):
        """Handle transcription start."""
        self.app_state.recording_state = RecordingState.TRANSCRIBING
        if self._status_text:
            self._status_text.text = f"Transcribing ({duration:.1f}s)"

        # Update panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.update_state(RecordingState.TRANSCRIBING)
        elif self._transcription_panel:
            self._transcription_panel.update_state(RecordingState.TRANSCRIBING)

        # Update tray transcribing state
        if self.tray_manager:
            self.tray_manager.update_transcribing_state(True)

    def _on_audio_level(self, level: float):
        """Handle audio level updates."""
        self.app_state.audio_level = level

        # Update the appropriate panel
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.update_audio_level(level)
        elif self._transcription_panel:
            self._transcription_panel.update_audio_level(level)

    def _on_error(self, error: str):
        """Handle transcription errors."""
        logger.error(f"Transcription error: {error}")

        # Track error in telemetry (anonymous - error type only)
        if self.telemetry_manager and self.telemetry_manager.is_enabled():
            device_type = "cuda" if self.app_state.device == "cuda" else "cpu"
            # Extract error type (first word or common pattern)
            error_type = error.split()[0] if error else "unknown"
            self.telemetry_manager.track_transcription_error(
                error_type=error_type,
                model_name=self.app_state.model or "unknown",
                device_type=device_type,
            )

        self._show_error(error)

        # Play error sound notification
        if self.sound_manager:
            self.sound_manager.play(SoundNotificationManager.EVENT_ERROR)

        # Screen reader announcement for errors
        self.accessibility_manager.announce(f"Error: {error}", priority="high")

    def _copy_transcription(self, e):
        """Copy transcription to clipboard."""
        if self._use_modern_ui and self._modern_transcription_panel:
            text = self._modern_transcription_panel.get_transcription_text()
        elif self._transcription_panel:
            text = self._transcription_panel.get_transcription_text()
        else:
            text = ""

        if text:
            self.page.set_clipboard(text)
            self._show_snackbar("Copied to clipboard")

    def _paste_transcription(self, e):
        """Paste transcription to active window."""
        # Get text from the appropriate panel
        if self._use_modern_ui and self._modern_transcription_panel:
            text = self._modern_transcription_panel.get_transcription_text()
        elif self._transcription_panel:
            text = self._transcription_panel.get_transcription_text()
        else:
            text = ""

        if text:
            self._paste_to_active_window(text)
        else:
            self._show_snackbar("No transcription to paste")

    def _open_settings(self, e):
        """Open settings panel."""
        self._switch_view("settings")

    def _open_help(self, e):
        """Open help panel."""
        self._switch_view("help")

    def _open_history(self, e):
        """Open history panel."""
        # Refresh history when opening
        if self._history_panel:
            self._history_panel.refresh()
        self._switch_view("history")

    def _on_recent_transcription_click(self, item):
        """
        Handle click on a recent transcription card.

        Loads the transcription text into the display and copies to clipboard.

        Parameters
        ----------
        item
            The HistoryItem that was clicked.
        """
        # Load the text into transcription display
        if self._use_modern_ui and self._modern_transcription_panel:
            self._modern_transcription_panel.update_transcription(item.text)
        elif self._transcription_panel:
            self._transcription_panel.update_transcription(item.text)

        # Copy to clipboard
        self.page.set_clipboard(item.text)
        self._show_snackbar("Copied to clipboard")

    def _paste_to_active_window(self, text: str):
        """
        Paste text to active window using auto-paste.

        Parameters
        ----------
        text
            The text to paste.
        """
        if not text:
            self._show_snackbar("No text to paste")
            return

        def on_paste_result(result: AutoPasteResult):
            """Handle paste result."""
            if result.success:
                # Determine app name for message
                app_name = result.window_info.window_class or "window"
                self._show_snackbar(f"Pasted to {app_name}")
            else:
                error_msg = result.error_message or "Unknown error"
                self._show_snackbar(f"Paste failed: {error_msg}")

        # Set callback and paste asynchronously
        self.auto_paste.set_result_callback(on_paste_result)
        self.auto_paste.paste_async(text)

        # Show initial message
        self._show_snackbar("Pasting to active window...")

    def _minimize_to_tray(self, e):
        """Minimize window to tray."""
        if self.page:
            self.page.window_visible = False
            self.page.window_prevent_close = True
            self.app_state.window_visible = False

    def restore_from_tray(self):
        """Restore window from tray."""
        if self.page:
            self.page.window_visible = True
            self.page.window_prevent_close = True
            self.app_state.window_visible = True

    def _show_error(self, message: str):
        """Show an error message."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message, color=ft.colors.ERROR),
                    bgcolor=ft.colors.ERROR_CONTAINER,
                )
            )

    def _show_snackbar(self, message: str):
        """Show a snackbar message."""
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    duration=2000,
                )
            )

    def _update_tray_recent_items(self):
        """Update the system tray with recent history items."""
        if not self.tray_manager:
            return

        # Get recent items from history
        from datetime import datetime
        items = self.history_manager.get_all(limit=TrayManager.MAX_RECENT_ITEMS)

        # Convert to RecentItem objects for tray
        recent_items = []
        for item in items:
            # Create a simple ID from timestamp (first 10 chars should be unique enough)
            item_id = item.timestamp[:10]
            recent_items.append(RecentItem(
                text=item.text,
                timestamp=item.timestamp,
                item_id=item_id,
            ))

        # Update tray
        self.tray_manager.update_recent_items(recent_items)

    def _on_tray_recent_item_click(self, item_id: str):
        """
        Handle click on a recent item from the tray menu.

        Restores the window, opens history panel, and shows the item.
        """
        # Restore window if minimized
        if not self.app_state.window_visible:
            self.restore_from_tray()

        # Open history panel (this refreshes the history)
        self._open_history(None)

        # Show notification about the clicked item
        self._show_snackbar("History opened - Recent item selected")

    def _handle_tray_record_toggle(self):
        """Handle record toggle from tray menu."""
        if self.app_state.recording_state == RecordingState.RECORDING:
            self.transcription_service.stop_recording()
        elif self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()

    def _handle_tray_exit(self):
        """Handle exit from tray menu."""
        self._is_shutting_down = True
        if self.page:
            self.page.window_close()

    def _open_history_from_tray(self):
        """Handle view history from tray menu."""
        # Restore window if minimized
        if not self.app_state.window_visible:
            self.restore_from_tray()
        # Open history panel
        self._open_history(None)

    def _open_settings_from_tray(self):
        """Handle settings from tray menu."""
        # Restore window if minimized
        if not self.app_state.window_visible:
            self.restore_from_tray()
        # Open settings panel
        self._open_settings(None)

    def _on_tray_model_selected(self, model_name: str):
        """Handle model selection from tray menu."""
        # Restore window if minimized
        if not self.app_state.window_visible:
            self.restore_from_tray()

        # Update the model in settings
        if self.settings_service.settings:
            self.settings_service.settings.model_name = model_name

            # Reinitialize transcription service with new model
            if self.transcription_service:
                self.transcription_service.reinitialize(self.settings_service.settings)

            # Update app state
            self.app_state.model = model_name

            # Update tray to show new current model
            self._update_tray_models()

            # Show notification
            self._show_snackbar(f"Model changed to {model_name}")

    def _handle_tray_double_click(self):
        """Handle double-click on tray icon (start recording)."""
        # Restore window if minimized
        if not self.app_state.window_visible:
            self.restore_from_tray()

        # Start recording if idle
        if self.app_state.recording_state == RecordingState.IDLE:
            self.transcription_service.start_recording()
        elif self.app_state.recording_state == RecordingState.RECORDING:
            # If already recording, stop it
            self.transcription_service.stop_recording()

    def _update_tray_models(self):
        """Update the system tray with available models."""
        if not self.tray_manager:
            return

        # Get available models from config
        from ..config import accepted_models_whisper

        models = []
        for model in accepted_models_whisper:
            # Create display name (capitalize first letter, replace hyphens with spaces)
            display_name = model.replace("-", " ").replace("_", " ").title()
            models.append(ModelInfo(
                name=model,
                display_name=display_name,
            ))

        # Get current model
        current_model = self.app_state.model or "large-v3"

        # Update tray manager
        self.tray_manager.set_available_models(models, current_model)

    def shutdown(self):
        """Shutdown the application and cleanup resources."""
        self._is_shutting_down = True

        # Track app shutdown in telemetry
        if self.telemetry_manager:
            self.telemetry_manager.track_app_shutdown()
            self.telemetry_manager.shutdown()

        if self.transcription_service:
            self.transcription_service.shutdown()

        if self.hotkey_manager:
            self.hotkey_manager.stop()

        if self.tray_manager:
            self.tray_manager.stop()

        if self._model_manager_panel:
            self._model_manager_panel.destroy()

        logger.info("FletApp shutdown complete")

    # Model manager methods
    def _open_model_manager(self, e=None):
        """
        Open the model manager panel.

        Creates the model manager panel on first access and switches to it.
        """
        if not self._model_manager_panel:
            from .views.model_manager import ModelManagerPanel

            self._model_manager_panel = ModelManagerPanel(
                on_model_selected=self._on_model_selected,
                on_close=lambda: self._switch_view("settings"),
            )

            # Create a new view for model manager
            model_manager_content = ft.Column(
                [
                    self._model_manager_panel.build(),
                    self._build_model_manager_controls(),
                ],
                spacing=0,
                expand=True,
            )

            # Add to content stack
            model_manager_container = ft.Container(
                content=model_manager_content,
                expand=True,
                visible=False,
                key="models",
            )
            self._content_stack.controls.append(model_manager_container)

        self._switch_view("models")

        # Refresh the model manager when opening
        self._model_manager_panel._refresh_model_grid()
        if self.page:
            self.page.update()

    def _build_model_manager_controls(self) -> ft.Container:
        """Build the bottom control panel for model manager view."""
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            tooltip="Back to settings",
            icon_size=24,
            on_click=lambda _: self._switch_view("settings"),
        )

        controls = ft.Container(
            content=ft.Row(
                [back_button],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            bgcolor=ft.colors.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
        )

        return controls

    def _on_model_selected(self, model_name: str):
        """
        Handle model selection from model manager.

        Parameters
        ----------
        model_name
            Selected model identifier.
        """
        # Update settings
        self.settings_service.set_model_name(model_name)

        # Update app state
        if self.settings_service.settings:
            self.app_state.update_from_settings(self.settings_service.settings)

        # Show success message
        self._show_snackbar(f"Model changed to {model_name}")

        # Go back to settings
        self._switch_view("settings")

        # Reinitialize transcription service with new model
        if self.transcription_service and self.settings_service.settings:
            self.transcription_service.reinitialize(self.settings_service.settings)
