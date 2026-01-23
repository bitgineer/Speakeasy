"""
System tray integration for the Flet GUI.

This module provides system tray functionality using pystray, allowing
the application to minimize to tray and provide quick access to common
actions.

Classes
-------
TrayManager
    Manages system tray icon and menu.
"""

import logging
import threading
from typing import Callable, Optional, List
from dataclasses import dataclass

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


@dataclass
class RecentItem:
    """A recent history item for the tray menu."""
    text: str
    timestamp: str
    item_id: str


class TrayManager:
    """
    System tray manager for the Flet application.

    This class manages a system tray icon with context menu options for:
    - Show/Restore window
    - Start/Stop recording
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

    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_record_toggle: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
        on_recent_item_click: Optional[Callable[[str], None]] = None,
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
        self._icon = None
        self._is_running = False
        self._lock = threading.RLock()

        # Create the tray icon image
        self._icon_image = self._create_icon_image()

        # Track recording state for menu updates
        self._is_recording = False

        # Track recent history items
        self._recent_items: List[RecentItem] = []

    def _create_icon_image(self) -> Optional[Image.Image]:
        """
        Create a simple icon image for the tray.

        Returns
        -------
        PIL.Image.Image or None
            The icon image, or None if PIL is not available.
        """
        if Image is None:
            return None

        try:
            # Create a simple microphone icon
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), color=(0, 120, 215))
            draw = ImageDraw.Draw(image)

            # Draw a simple mic shape
            center_x = width // 2
            center_y = height // 2

            # Mic body (ellipse)
            draw.ellipse(
                [(center_x - 10, center_y - 15), (center_x + 10, center_y + 5)],
                fill=(255, 255, 255),
                outline=(255, 255, 255),
                width=2,
            )

            # Mic stand
            draw.line(
                [(center_x, center_y + 5), (center_x, center_y + 15)],
                fill=(255, 255, 255),
                width=2,
            )

            # Mic base
            draw.line(
                [(center_x - 8, center_y + 15), (center_x + 8, center_y + 15)],
                fill=(255, 255, 255),
                width=2,
            )

            return image
        except Exception as e:
            logger.warning(f"Failed to create tray icon image: {e}")
            return None

    def _create_menu(self):
        """Create the tray menu based on current state."""
        if pystray is None:
            return None

        record_text = "Stop Recording" if self._is_recording else "Start Recording"

        # Start with standard menu items
        menu_items = [
            pystray.MenuItem("Show", self._on_show_callback),
            pystray.MenuItem(record_text, self._on_record_callback),
        ]

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

    def _on_exit_callback(self):
        """Handle exit menu item click."""
        logger.debug("Tray: Exit requested")
        if self._on_exit:
            try:
                self._on_exit()
            except Exception as e:
                logger.error(f"Error in exit callback: {e}")

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
        Update the recording state in the tray menu.

        Parameters
        ----------
        is_recording
            Whether recording is currently active.
        """
        if not PYSTRAY_AVAILABLE or not self._icon:
            return

        with self._lock:
            self._is_recording = is_recording
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

        try:
            self._icon.notify(title=title, message=message)
        except Exception as e:
            logger.debug(f"Failed to show tray notification: {e}")

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
