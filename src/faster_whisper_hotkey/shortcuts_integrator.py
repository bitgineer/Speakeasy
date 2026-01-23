"""
Shortcuts integration layer for connecting keyboard shortcuts to actions.

This module provides the integration between the shortcuts manager and the
actual application functionality. It handles registering callbacks and
ensuring shortcuts trigger the correct actions.

Classes
-------
ShortcutsIntegrator
    Main integration class that connects shortcuts to application actions.

ShortcutsKeyboardListener
    Keyboard listener that detects and triggers multiple shortcuts.

Functions
---------
get_shortcuts_integrator
    Get the global shortcuts integrator instance.

initialize_shortcuts_system
    Initialize the shortcuts system.

Notes
-----
The integrator works with the shortcuts_manager to register callbacks
for each shortcut action. It provides methods that the GUI and transcriber
can use to register their action handlers.
"""

import logging
import threading
import time
from typing import Callable, Dict, List, Optional, Any, Set, Tuple

# Lazy import of pynput to avoid issues in headless environments
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False

from .shortcuts_manager import get_shortcuts_manager, ShortcutsManager, parse_hotkey

logger = logging.getLogger(__name__)


# Modifier keys for hotkey detection
MODIFIER_KEYS = {
    keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
    keyboard.Key.alt_l, keyboard.Key.alt_r,
    keyboard.Key.shift_l, keyboard.Key.shift_r,
    keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
} if PYNPUT_AVAILABLE else set()


class ShortcutsKeyboardListener:
    """
    Keyboard listener that detects and triggers multiple shortcuts.

    This listener runs alongside the main transcriber hotkey listener and
    handles triggering additional shortcuts for actions like showing history,
    opening settings, etc.
    """

    def __init__(self, integrator: 'ShortcutsIntegrator'):
        """
        Initialize the shortcuts keyboard listener.

        Args:
            integrator: The ShortcutsIntegrator instance
        """
        if not PYNPUT_AVAILABLE:
            raise RuntimeError("pynput is not available. Cannot create keyboard listener.")

        self.integrator = integrator
        self.listener: Optional[keyboard.Listener] = None
        self.is_running = False
        self.active_modifiers: Set[Any] = set()
        self.last_trigger_time: Dict[str, float] = {}
        self.debounce_delay = 0.2  # Minimum time between triggers for same shortcut

    def _parse_hotkey_to_keys(self, hotkey_str: str) -> Tuple[Set[Any], Any]:
        """
        Parse a hotkey string into modifier keys and main key.

        Args:
            hotkey_str: Hotkey string like "ctrl+shift+f1"

        Returns:
            Tuple of (set of modifier keys, main key)
        """
        if not hotkey_str:
            return set(), None

        # Key mappings
        key_mapping = {
            "pause": keyboard.Key.pause,
            "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
            "insert": keyboard.Key.insert, "home": keyboard.Key.home,
            "end": keyboard.Key.end, "pageup": keyboard.Key.page_up,
            "pagedown": keyboard.Key.page_down, "space": keyboard.Key.space,
            "enter": keyboard.Key.enter, "tab": keyboard.Key.tab,
            "backspace": keyboard.Key.backspace, "delete": keyboard.Key.delete,
            "up": keyboard.Key.up, "down": keyboard.Key.down,
            "left": keyboard.Key.left, "right": keyboard.Key.right,
        }

        modifier_mapping = {
            "ctrl": {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
            "alt": {keyboard.Key.alt_l, keyboard.Key.alt_r},
            "shift": {keyboard.Key.shift_l, keyboard.Key.shift_r},
            "win": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
        }

        parts = hotkey_str.lower().split("+")
        modifiers = set()
        main_key = None

        for part in parts:
            part = part.strip()
            if part in modifier_mapping:
                modifiers.update(modifier_mapping[part])
            elif part in key_mapping:
                main_key = key_mapping[part]
            elif len(part) == 1:
                main_key = keyboard.KeyCode.from_char(part)
            else:
                logger.warning(f"Unknown key in hotkey: {part}")

        return modifiers, main_key

    def _check_hotkey_match(self, key: Any, hotkey_str: str) -> bool:
        """
        Check if the pressed key matches a hotkey string.

        Args:
            key: The key that was pressed
            hotkey_str: The hotkey string to check against

        Returns:
            True if the key + active modifiers match the hotkey
        """
        if not hotkey_str:
            return False

        required_modifiers, main_key = self._parse_hotkey_to_keys(hotkey_str)

        if main_key is None or key != main_key:
            return False

        if required_modifiers:
            return bool(required_modifiers & self.active_modifiers)

        return True

    def _on_press(self, key: Any):
        """Handle key press events."""
        # Track modifier keys
        if key in MODIFIER_KEYS:
            self.active_modifiers.add(key)
            return

        # Check all enabled shortcuts
        current_time = time.time()
        shortcuts = self.integrator.get_all_shortcuts()

        for shortcut in shortcuts:
            if not shortcut.enabled or not shortcut.hotkey:
                continue

            # Debounce check
            last_time = self.last_trigger_time.get(shortcut.id, 0)
            if current_time - last_time < self.debounce_delay:
                continue

            # Check if this key matches the shortcut
            if self._check_hotkey_match(key, shortcut.hotkey):
                logger.debug(f"Shortcut triggered: {shortcut.id} ({shortcut.hotkey})")
                self.last_trigger_time[shortcut.id] = current_time
                self.integrator.trigger_shortcut_by_id(shortcut.id)

    def _on_release(self, key: Any):
        """Handle key release events."""
        if key in MODIFIER_KEYS:
            self.active_modifiers.discard(key)

    def start(self):
        """Start the keyboard listener."""
        if self.is_running:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        self.is_running = True
        logger.info("Shortcuts keyboard listener started")

    def stop(self):
        """Stop the keyboard listener."""
        if not self.is_running:
            return

        if self.listener:
            self.listener.stop()
            self.listener = None

        self.is_running = False
        logger.info("Shortcuts keyboard listener stopped")


class ShortcutsIntegrator:
    """
    Integration layer that connects keyboard shortcuts to application actions.

    This class manages the registration of callbacks for shortcuts and
    provides a thread-safe mechanism for triggering actions.
    """

    def __init__(self, shortcuts_manager: ShortcutsManager = None):
        """
        Initialize the shortcuts integrator.

        Args:
            shortcuts_manager: The shortcuts manager instance (uses global if None)
        """
        self.manager = shortcuts_manager or get_shortcuts_manager()
        self.action_handlers: Dict[str, List[Callable]] = {}
        self.lock = threading.Lock()
        self._initialized = False
        self.keyboard_listener: Optional[ShortcutsKeyboardListener] = None

    def initialize(self):
        """
        Initialize default shortcuts and register them with the manager.
        This should be called during application startup.
        """
        if self._initialized:
            return

        with self.lock:
            # Register default shortcut callbacks
            # These will be connected to actual handlers by the GUI/transcriber
            default_shortcuts = self.manager.get_all()
            for shortcut in default_shortcuts:
                self.action_handlers[shortcut.id] = []

            self._initialized = True
            logger.info(f"Shortcuts integrator initialized with {len(default_shortcuts)} shortcuts")

    def register_action_handler(self, shortcut_id: str, handler: Callable) -> bool:
        """
        Register a callback handler for a specific shortcut action.

        Args:
            shortcut_id: The ID of the shortcut (e.g., 'record_toggle', 'show_history')
            handler: The callable to execute when the shortcut is triggered

        Returns:
            True if registration was successful, False otherwise
        """
        with self.lock:
            if shortcut_id not in self.action_handlers:
                self.action_handlers[shortcut_id] = []

            self.action_handlers[shortcut_id].append(handler)

            # Register with the shortcuts manager's callback system
            self.manager.register_callback(shortcut_id, self._create_callback_wrapper(shortcut_id))

            logger.debug(f"Registered handler for shortcut '{shortcut_id}'")
            return True

    def _create_callback_wrapper(self, shortcut_id: str) -> Callable:
        """
        Create a wrapper callback for the shortcuts manager.

        The wrapper ensures all registered handlers are called when the
        shortcut is triggered.
        """
        def wrapper():
            self._trigger_shortcut(shortcut_id)
        return wrapper

    def _trigger_shortcut(self, shortcut_id: str):
        """
        Trigger all handlers registered for a shortcut.

        This method is called when a shortcut hotkey is detected.
        It executes all registered handlers in order.
        """
        with self.lock:
            handlers = self.action_handlers.get(shortcut_id, []).copy()

        if not handlers:
            logger.warning(f"No handlers registered for shortcut '{shortcut_id}'")
            return

        logger.debug(f"Triggering shortcut '{shortcut_id}' with {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in handler for shortcut '{shortcut_id}': {e}", exc_info=True)

    def trigger_shortcut_by_id(self, shortcut_id: str) -> bool:
        """
        Manually trigger a shortcut by ID (useful for testing or programmatic triggering).

        Args:
            shortcut_id: The ID of the shortcut to trigger

        Returns:
            True if the shortcut was triggered, False if not found
        """
        if shortcut_id in self.action_handlers:
            self._trigger_shortcut(shortcut_id)
            return True
        return False

    def start_keyboard_listener(self):
        """
        Start the keyboard listener for shortcuts.
        This should be called when the application starts.
        """
        if not PYNPUT_AVAILABLE:
            logger.warning("pynput not available, shortcuts keyboard listener not started")
            return

        if self.keyboard_listener is None:
            self.keyboard_listener = ShortcutsKeyboardListener(self)

        self.keyboard_listener.start()

    def stop_keyboard_listener(self):
        """Stop the keyboard listener for shortcuts."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def get_shortcut_hotkey(self, shortcut_id: str) -> Optional[str]:
        """
        Get the hotkey string for a shortcut.

        Args:
            shortcut_id: The ID of the shortcut

        Returns:
            The hotkey string or None if not found
        """
        shortcut = self.manager.get(shortcut_id)
        if shortcut:
            return shortcut.hotkey
        return None

    def is_shortcut_enabled(self, shortcut_id: str) -> bool:
        """
        Check if a shortcut is enabled.

        Args:
            shortcut_id: The ID of the shortcut

        Returns:
            True if enabled, False otherwise
        """
        shortcut = self.manager.get(shortcut_id)
        if shortcut:
            return shortcut.enabled
        return False

    def set_shortcut_hotkey(self, shortcut_id: str, hotkey: str) -> tuple:
        """
        Set a new hotkey for a shortcut.

        Args:
            shortcut_id: The ID of the shortcut
            hotkey: The new hotkey string

        Returns:
            Tuple of (success, error_message)
        """
        return self.manager.set_hotkey(shortcut_id, hotkey)

    def reload_shortcuts(self):
        """
        Reload shortcuts from the configuration file.
        Useful when shortcuts have been modified externally.
        """
        with self.lock:
            self.manager.load()
            # Re-initialize handlers
            for shortcut_id in self.action_handlers:
                self.manager.register_callback(
                    shortcut_id,
                    self._create_callback_wrapper(shortcut_id)
                )
        logger.info("Shortcuts reloaded from configuration")

    def get_all_shortcuts(self) -> List[Any]:
        """Get all shortcuts."""
        return self.manager.get_all()

    def get_shortcuts_by_group(self, group_name: str) -> List[Any]:
        """Get all shortcuts in a specific group."""
        return self.manager.get_group(group_name)


# Global shortcuts integrator instance
_integrator: Optional[ShortcutsIntegrator] = None
_integrator_lock = threading.Lock()


def get_shortcuts_integrator() -> ShortcutsIntegrator:
    """
    Get the global shortcuts integrator instance.

    Returns:
        The global ShortcutsIntegrator instance
    """
    global _integrator
    if _integrator is None:
        with _integrator_lock:
            if _integrator is None:
                _integrator = ShortcutsIntegrator()
    return _integrator


def initialize_shortcuts_system():
    """
    Initialize the shortcuts system.
    This should be called during application startup.
    """
    integrator = get_shortcuts_integrator()
    integrator.initialize()
    logger.info("Shortcuts system initialized")
