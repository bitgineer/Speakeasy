"""
System tray integration for the Flet GUI.

This module provides system tray functionality using pystray, allowing
the application to minimize to tray and provide quick access to common
actions.

Classes
-------
TrayManager
    Manages system tray icon and menu.
TrayIconState
    Represents the visual state of the tray icon.
"""

import logging
import threading
import time
import math
from typing import Callable, Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    pystray = None
    Image = None
    ImageDraw = None

logger = logging.getLogger(__name__)


class TrayIconState(Enum):
    """Visual states for the tray icon."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


@dataclass
class RecentItem:
    """A recent history item for the tray menu."""
    text: str
    timestamp: str
    item_id: str


@dataclass
class ModelInfo:
    """Information about a transcription model."""
    name: str
    display_name: str
    language: str = "en"


class TrayManager:
    """
    System tray manager for the Flet application.

    This class manages a system tray icon with context menu options for:
    - Show/Restore window
    - Start/Stop recording
    - View History
    - Open Settings
    - Model selector submenu
    - Recent transcriptions (quick access)
    - Exit application

    Note
    ----
    pystray runs in its own thread and communicates with the main app
    via callbacks. The tray icon runs independently of the Flet UI.

    Attributes
    ----------
    icon
        The pystray Icon instance.
    is_running
        Whether the tray icon is currently running.
    """

    # Maximum number of recent items to show in tray menu
    MAX_RECENT_ITEMS = 5

    # Icon size
    ICON_SIZE = 64

    # Animation settings
    ANIMATION_FPS = 20
    ANIMATION_INTERVAL = 1.0 / ANIMATION_FPS

    # Color scheme for different states
    COLORS = {
        TrayIconState.IDLE: (76, 175, 80),        # Green
        TrayIconState.RECORDING: (244, 67, 54),   # Red
        TrayIconState.TRANSCRIBING: (255, 152, 0),  # Orange
        TrayIconState.ERROR: (158, 158, 158),     # Grey
    }

    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_record_toggle: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
        on_recent_item_click: Optional[Callable[[str], None]] = None,
        on_open_history: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_model_selected: Optional[Callable[[str], None]] = None,
        on_double_click: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the tray manager.

        Parameters
        ----------
        on_show
            Callback when "Show" is clicked from tray menu.
        on_record_toggle
            Callback when "Start/Stop Recording" is clicked.
        on_exit
            Callback when "Exit" is clicked from tray menu.
        on_recent_item_click
            Callback when a recent history item is clicked.
            Receives the item_id as parameter.
        on_open_history
            Callback when "View History" is clicked.
        on_open_settings
            Callback when "Settings" is clicked.
        on_model_selected
            Callback when a model is selected from the model submenu.
            Receives the model name as parameter.
        on_double_click
            Callback when the tray icon is double-clicked.
        """
        if not PYSTRAY_AVAILABLE:
            logger.warning("pystray not available, tray integration disabled")
            self._icon = None
            self._is_running = False
            return

        self._on_show = on_show
        self._on_record_toggle = on_record_toggle
        self._on_exit = on_exit
        self._on_recent_item_click = on_recent_item_click
        self._on_open_history = on_open_history
        self._on_open_settings = on_open_settings
        self._on_model_selected = on_model_selected
        self._on_double_click = on_double_click
        self._icon = None
        self._is_running = False
        self._lock = threading.RLock()

        # Icon state management
        self._icon_state = TrayIconState.IDLE
        self._pulse_phase = 0.0
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_animation = threading.Event()

        # Create the tray icon image
        self._icon_image = self._create_icon_image(TrayIconState.IDLE)

        # Track recording state for menu updates
        self._is_recording = False
        self._is_transcribing = False

        # Track recent history items
        self._recent_items: List[RecentItem] = []

        # Available models
        self._available_models: List[ModelInfo] = []
        self._current_model = "large-v3"

        # Notification settings
        self._tray_notifications_enabled = True

        # Click detection for double-click
        self._last_click_time = 0
        self._click_count = 0
        self._double_click_threshold = 0.5  # seconds

    def _create_icon_image(
        self,
        state: TrayIconState = TrayIconState.IDLE,
        pulse_phase: float = 0.0
    ) -> Optional[Image.Image]:
        """
        Create an icon image for the tray with optional animation.

        Parameters
        ----------
        state
            The current state of the icon (determines color).
        pulse_phase
            The phase of the pulse animation (0.0 to 1.0).

        Returns
        -------
        PIL.Image.Image or None
            The icon image, or None if PIL is not available.
        """
        if Image is None:
            return None

        try:
            size = self.ICON_SIZE
            image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            # Get base color for state
            base_color = self.COLORS.get(state, self.COLORS[TrayIconState.IDLE])

            center_x = size // 2
            center_y = size // 2

            # Draw pulse effect for recording state
            if state == TrayIconState.RECORDING:
                pulse_val = (math.sin(pulse_phase * 2 * math.pi) + 1) / 2
                pulse_radius = 20 + (8 * pulse_val)
                opacity = int(180 * (1.0 - pulse_val * 0.7))

                # Draw outer glow ring
                for i in range(3):
                    radius = int(pulse_radius - i * 4)
                    if radius > 10:
                        alpha = max(0, opacity - i * 40)
                        draw.ellipse(
                            [(center_x - radius, center_y - radius),
                             (center_x + radius, center_y + radius)],
                            outline=(*base_color, alpha),
                            width=2,
                        )

            # Draw main circle background
            bg_radius = 26
            draw.ellipse(
                [(center_x - bg_radius, center_y - bg_radius),
                 (center_x + bg_radius, center_y + bg_radius)],
                fill=(*base_color, 255),
            )

            # Draw microphone icon
            mic_color = (255, 255, 255, 255)

            # Mic body (rounded rectangle)
            mic_width = 14
            mic_height = 22
            mic_x = center_x - mic_width // 2
            mic_y = center_y - 8

            # Draw rounded rect for mic body
            draw.rounded_rectangle(
                [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
                radius=7,
                fill=mic_color,
            )

            # Mic stand (line)
            draw.line(
                [(center_x, mic_y + mic_height), (center_x, mic_y + mic_height + 8)],
                fill=mic_color,
                width=3,
            )

            # Mic base (rounded line)
            base_y = mic_y + mic_height + 8
            draw.line(
                [(center_x - 8, base_y), (center_x + 8, base_y)],
                fill=mic_color,
                width=3,
            )

            # Draw small recording indicator when recording
            if state == TrayIconState.RECORDING:
                # Red dot in top right corner
                dot_radius = 6
                dot_x = size - 10
                dot_y = 10
                draw.ellipse(
                    [(dot_x - dot_radius, dot_y - dot_radius),
                     (dot_x + dot_radius, dot_y + dot_radius)],
                    fill=(255, 50, 50, 255),
                )

            return image
        except Exception as e:
            logger.warning(f"Failed to create tray icon image: {e}")
            return None

    def _animation_loop(self):
        """Animation loop for pulsing the tray icon during recording."""
        while not self._stop_animation.is_set():
            with self._lock:
                if self._icon and self._icon_state == TrayIconState.RECORDING:
                    self._pulse_phase += self.ANIMATION_INTERVAL
                    if self._pulse_phase > 1.0:
                        self._pulse_phase = 0.0

                    new_icon = self._create_icon_image(
                        self._icon_state,
                        self._pulse_phase
                    )
                    if new_icon:
                        self._icon.icon = new_icon

            time.sleep(self.ANIMATION_INTERVAL)

    def _start_animation(self):
        """Start the icon animation thread."""
        if self._animation_thread is None or not self._animation_thread.is_alive():
            self._stop_animation.clear()
            self._animation_thread = threading.Thread(
                target=self._animation_loop,
                daemon=True,
            )
            self._animation_thread.start()
            logger.debug("Tray icon animation started")

    def _stop_animation_thread(self):
        """Stop the icon animation thread."""
        self._stop_animation.set()
        if self._animation_thread:
            self._animation_thread.join(timeout=1.0)
            self._animation_thread = None
            logger.debug("Tray icon animation stopped")

    def _update_icon_state(self, state: TrayIconState):
        """
        Update the visual state of the tray icon.

        Parameters
        ----------
        state
            The new state for the icon.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        with self._lock:
            self._icon_state = state

            # Update icon immediately
            new_icon = self._create_icon_image(state, self._pulse_phase)
            if new_icon:
                self._icon.icon = new_icon

            # Start/stop animation based on state
            if state == TrayIconState.RECORDING:
                self._start_animation()
            else:
                self._stop_animation_thread()
                self._pulse_phase = 0.0

    def _create_menu(self):
        """Create the enhanced tray menu based on current state."""
        if pystray is None:
            return None

        # Status indicator in menu
        status_text = self._get_status_text()
        record_text = "Stop Recording" if self._is_recording else "Start Recording"

        # Start with status and quick actions
        menu_items = [
            pystray.MenuItem(status_text, self._on_show_callback, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Window", self._on_show_callback),
            pystray.MenuItem(record_text, self._on_record_callback),
        ]

        # Add View History if callback is available
        if self._on_open_history is not None:
            menu_items.append(pystray.MenuItem("View History", self._on_history_callback))

        # Add Settings if callback is available
        if self._on_open_settings is not None:
            menu_items.append(pystray.MenuItem("Settings", self._on_settings_callback))

        # Add model selector submenu if models are available
        if self._available_models:
            model_menu_items = []
            for model in self._available_models:
                is_current = model.name == self._current_model
                display_text = f"{model.display_name}" + (" (Current)" if is_current else "")
                model_menu_items.append(
                    pystray.MenuItem(
                        display_text,
                        self._create_model_callback(model.name),
                        enabled=not is_current,
                    )
                )
            menu_items.append(pystray.MenuItem("Model", pystray.Menu(*model_menu_items)))

        # Add recent items if available
        if self._recent_items:
            menu_items.append(pystray.Menu.SEPARATOR)
            menu_items.append(pystray.MenuItem("Recent Transcriptions", pystray.Menu.SEPARATOR))

            for item in self._recent_items:
                # Truncate text for menu display
                display_text = self._truncate_text(item.text, 40)
                menu_items.append(
                    pystray.MenuItem(display_text, self._create_item_callback(item.item_id))
                )

        # Add separator and exit
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Exit", self._on_exit_callback))

        return pystray.Menu(*menu_items)

    def _get_status_text(self) -> str:
        """Get the status text for the menu based on current state."""
        if self._is_recording:
            return "● Recording..."
        elif self._is_transcribing:
            return "◐ Transcribing..."
        else:
            return "○ Ready"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max_length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _create_item_callback(self, item_id: str):
        """Create a callback for a recent history item."""
        def callback():
            logger.debug(f"Tray: Recent item clicked: {item_id}")
            if self._on_recent_item_click:
                try:
                    self._on_recent_item_click(item_id)
                except Exception as e:
                    logger.error(f"Error in recent item callback: {e}")
        return callback

    def _create_model_callback(self, model_name: str):
        """Create a callback for a model selection."""
        def callback():
            logger.debug(f"Tray: Model selected: {model_name}")
            if self._on_model_selected:
                try:
                    self._on_model_selected(model_name)
                except Exception as e:
                    logger.error(f"Error in model selection callback: {e}")
        return callback

    def _on_show_callback(self):
        """Handle show menu item click."""
        logger.debug("Tray: Show requested")
        if self._on_show:
            try:
                self._on_show()
            except Exception as e:
                logger.error(f"Error in show callback: {e}")

    def _on_record_callback(self):
        """Handle record toggle menu item click."""
        logger.debug("Tray: Record toggle requested")
        if self._on_record_toggle:
            try:
                self._on_record_toggle()
            except Exception as e:
                logger.error(f"Error in record callback: {e}")

    def _on_history_callback(self):
        """Handle view history menu item click."""
        logger.debug("Tray: History requested")
        if self._on_open_history:
            try:
                self._on_open_history()
            except Exception as e:
                logger.error(f"Error in history callback: {e}")

    def _on_settings_callback(self):
        """Handle settings menu item click."""
        logger.debug("Tray: Settings requested")
        if self._on_open_settings:
            try:
                self._on_open_settings()
            except Exception as e:
                logger.error(f"Error in settings callback: {e}")

    def _on_exit_callback(self):
        """Handle exit menu item click."""
        logger.debug("Tray: Exit requested")
        if self._on_exit:
            try:
                self._on_exit()
            except Exception as e:
                logger.error(f"Error in exit callback: {e}")

    def _on_icon_click(self):
        """Handle tray icon click (single-click shows window)."""
        current_time = time.time()
        time_since_last_click = current_time - self._last_click_time

        self._click_count += 1

        # Check for double-click
        if time_since_last_click < self._double_click_threshold:
            if self._click_count >= 2:
                # Double-click detected
                self._click_count = 0
                logger.debug("Tray: Double-click detected")
                if self._on_double_click:
                    try:
                        self._on_double_click()
                    except Exception as e:
                        logger.error(f"Error in double-click callback: {e}")
                return

        self._last_click_time = current_time

        # Reset click count after threshold
        def reset_click_count():
            time.sleep(self._double_click_threshold + 0.1)
            if time.time() - self._last_click_time >= self._double_click_threshold:
                self._click_count = 0

        threading.Thread(target=reset_click_count, daemon=True).start()

        # Single-click action (show window)
        logger.debug("Tray: Single-click detected")
        if self._on_show:
            try:
                self._on_show()
            except Exception as e:
                logger.error(f"Error in click callback: {e}")

    def start(self, title: str = "faster-whisper-hotkey"):
        """
        Start the system tray icon.

        Parameters
        ----------
        title
            Title for the tray icon tooltip.
        """
        if not PYSTRAY_AVAILABLE:
            logger.warning("Cannot start tray: pystray not available")
            return

        with self._lock:
            if self._is_running:
                logger.warning("Tray icon already running")
                return

            try:
                self._icon = pystray.Icon(
                    name="faster_whisper_hotkey",
                    icon=self._icon_image,
                    title=title,
                    menu=self._create_menu(),
                )

                # Run in a separate thread
                thread = threading.Thread(
                    target=self._icon.run,
                    daemon=True,
                )
                thread.start()

                self._is_running = True
                logger.info("System tray icon started")
            except Exception as e:
                logger.error(f"Failed to start tray icon: {e}")

    def stop(self):
        """Stop the system tray icon."""
        if not PYSTRAY_AVAILABLE:
            return

        # Stop animation first
        self._stop_animation_thread()

        with self._lock:
            if not self._is_running:
                return

            try:
                if self._icon:
                    self._icon.stop()
                    self._icon = None

                self._is_running = False
                logger.info("System tray icon stopped")
            except Exception as e:
                logger.error(f"Error stopping tray icon: {e}")

    def update_recording_state(self, is_recording: bool):
        """
        Update the recording state in the tray menu and icon.

        Parameters
        ----------
        is_recording
            Whether recording is currently active.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        with self._lock:
            self._is_recording = is_recording

            # Update icon visual state
            if is_recording:
                self._update_icon_state(TrayIconState.RECORDING)
            elif self._is_transcribing:
                self._update_icon_state(TrayIconState.TRANSCRIBING)
            else:
                self._update_icon_state(TrayIconState.IDLE)

            # Update the menu
            try:
                self._icon.menu = self._create_menu()
            except Exception as e:
                logger.debug(f"Failed to update tray menu: {e}")

    def update_transcribing_state(self, is_transcribing: bool):
        """
        Update the transcribing state in the tray menu and icon.

        Parameters
        ----------
        is_transcribing
            Whether transcribing is currently active.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        with self._lock:
            self._is_transcribing = is_transcribing

            # Update icon visual state
            if is_transcribing:
                self._update_icon_state(TrayIconState.TRANSCRIBING)
            elif not self._is_recording:
                self._update_icon_state(TrayIconState.IDLE)

            # Update the menu
            try:
                self._icon.menu = self._create_menu()
            except Exception as e:
                logger.debug(f"Failed to update tray menu: {e}")

    def notify(self, title: str, message: str):
        """
        Show a notification from the tray icon.

        Parameters
        ----------
        title
            Notification title.
        message
            Notification message.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        # Respect notification settings
        if not self._tray_notifications_enabled:
            logger.debug("Tray notifications disabled, skipping notification")
            return

        try:
            self._icon.notify(title=title, message=message)
        except Exception as e:
            logger.debug(f"Failed to show tray notification: {e}")

    def set_tray_notifications_enabled(self, enabled: bool):
        """
        Enable or disable tray notifications.

        Parameters
        ----------
        enabled
            Whether tray notifications should be shown.
        """
        self._tray_notifications_enabled = enabled
        logger.debug(f"Tray notifications {'enabled' if enabled else 'disabled'}")

    @property
    def is_running(self) -> bool:
        """Check if the tray icon is running."""
        return self._is_running and PYSTRAY_AVAILABLE

    @property
    def is_available(self) -> bool:
        """Check if tray functionality is available."""
        return PYSTRAY_AVAILABLE

    def update_recent_items(self, items: List[RecentItem]):
        """
        Update the recent history items in the tray menu.

        Parameters
        ----------
        items
            List of RecentItem objects to display in the tray menu.
            Only the first MAX_RECENT_ITEMS will be shown.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        with self._lock:
            # Keep only the most recent items up to MAX_RECENT_ITEMS
            self._recent_items = items[:self.MAX_RECENT_ITEMS]
            # Update the menu
            try:
                self._icon.menu = self._create_menu()
                logger.debug(f"Updated tray menu with {len(self._recent_items)} recent items")
            except Exception as e:
                logger.debug(f"Failed to update tray menu with recent items: {e}")

    def clear_recent_items(self):
        """Clear all recent history items from the tray menu."""
        self.update_recent_items([])

    def set_available_models(self, models: List[ModelInfo], current_model: str):
        """
        Set the available models for the model selector submenu.

        Parameters
        ----------
        models
            List of ModelInfo objects representing available models.
        current_model
            The name of the currently active model.
        """
        if not PYSTRAY_AVAILABLE:
            return

        with self._lock:
            self._available_models = models
            self._current_model = current_model

            # Update the menu if icon is running
            if self._icon:
                try:
                    self._icon.menu = self._create_menu()
                    logger.debug(f"Updated tray menu with {len(models)} models")
                except Exception as e:
                    logger.debug(f"Failed to update tray menu with models: {e}")

    def set_current_model(self, model_name: str):
        """
        Update the current model indicator.

        Parameters
        ----------
        model_name
            The name of the new current model.
        """
        if not PYSTRAY_AVAILABLE:
            return

        with self._lock:
            self._current_model = model_name

            # Update the menu if icon is running
            if self._icon:
                try:
                    self._icon.menu = self._create_menu()
                except Exception as e:
                    logger.debug(f"Failed to update tray menu with current model: {e}")

    def update_tooltip(self, text: str):
        """
        Update the tooltip text for the tray icon.

        Parameters
        ----------
        text
            The new tooltip text.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        try:
            self._icon.title = text
        except Exception as e:
            logger.debug(f"Failed to update tray tooltip: {e}")
