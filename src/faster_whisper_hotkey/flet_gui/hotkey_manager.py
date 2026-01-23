"""
Hotkey manager for Flet GUI integration.

This module provides keyboard hotkey detection and management for the Flet GUI,
running in a background thread and communicating events to the Flet UI via
thread-safe queues.

Classes
-------
HotkeyManager
    Manages keyboard hotkey detection and dispatching.
"""

import logging
import threading
import queue
import time
from typing import Callable, Optional, Set, Tuple
from dataclasses import dataclass

from pynput import keyboard

logger = logging.getLogger(__name__)


@dataclass
class HotkeyEvent:
    """Event data for hotkey actions."""
    action: str  # "press" or "release"
    hotkey: str


class HotkeyManager:
    """
    Hotkey detection manager for Flet GUI integration.

    This class runs a pynput keyboard listener in a background thread and
    communicates hotkey events to the Flet UI via a thread-safe queue.
    It supports both single keys and modifier combinations.

    Attributes
    ----------
    hotkey
        The current hotkey string (e.g., "pause", "ctrl+shift+h").
    event_queue
        Thread-safe queue for hotkey events.
    is_running
        Whether the hotkey listener is currently running.
    """

    def __init__(self, hotkey: str = "pause"):
        """
        Initialize the hotkey manager.

        Parameters
        ----------
        hotkey
            Initial hotkey string.
        """
        self._hotkey = hotkey
        self._hotkey_combo: Tuple[Set, any] = self._parse_hotkey(hotkey)
        self._event_queue: queue.Queue = queue.Queue()
        self._listener: Optional[keyboard.Listener] = None
        self._is_running = False
        self._lock = threading.RLock()

        # Modifier tracking for combination hotkeys
        self._active_modifiers: Set = set()

        # Callbacks
        self._callbacks = {
            "hotkey_press": [],
            "hotkey_release": [],
        }

    def _parse_hotkey(self, hotkey_str: str) -> Tuple[Set, any]:
        """
        Parse hotkey string into (modifiers, main_key) tuple.

        Parameters
        ----------
        hotkey_str
            Hotkey string like "pause", "ctrl+f1", "shift+alt+h".

        Returns
        -------
        tuple[set, any]
            (set of modifier keys, main key)
        """
        # Key mappings
        key_mapping = {
            "pause": keyboard.Key.pause,
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
            "insert": keyboard.Key.insert,
            "home": keyboard.Key.home,
            "end": keyboard.Key.end,
            "pageup": keyboard.Key.page_up,
            "pagedown": keyboard.Key.page_down,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
            "escape": keyboard.Key.esc,
            "esc": keyboard.Key.esc,
        }

        modifier_mapping = {
            "ctrl": {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
            "alt": {keyboard.Key.alt_l, keyboard.Key.alt_r},
            "shift": {keyboard.Key.shift_l, keyboard.Key.shift_r},
            "win": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
            "cmd": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
        }

        parts = hotkey_str.lower().split("+")
        modifiers = set()
        main_key = None

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in modifier_mapping:
                modifiers.update(modifier_mapping[part])
            elif part in key_mapping:
                main_key = key_mapping[part]
            elif len(part) == 1:
                main_key = keyboard.KeyCode.from_char(part)
            else:
                logger.warning(f"Unknown hotkey part: {part}")

        return (modifiers, main_key)

    def set_hotkey(self, hotkey: str):
        """
        Update the hotkey combination.

        Parameters
        ----------
        hotkey
            New hotkey string.
        """
        with self._lock:
            self._hotkey = hotkey
            self._hotkey_combo = self._parse_hotkey(hotkey)
            logger.info(f"Hotkey updated to: {hotkey}")

    def get_hotkey(self) -> str:
        """Get the current hotkey string."""
        with self._lock:
            return self._hotkey

    def _is_modifier(self, key) -> bool:
        """Check if a key is a modifier."""
        modifier_keys = {
            keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
        }
        return key in modifier_keys

    def _matches_hotkey(self, key) -> bool:
        """Check if current key + active modifiers match the hotkey."""
        required_modifiers, main_key = self._hotkey_combo

        # Check if main key matches
        if key != main_key:
            return False

        # Check modifiers (if any required)
        if required_modifiers:
            return bool(required_modifiers & self._active_modifiers)

        return True

    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Track modifier keys
            if self._is_modifier(key):
                self._active_modifiers.add(key)
                return True

            # Check if hotkey matches
            if self._matches_hotkey(key):
                self._emit_event("hotkey_press", HotkeyEvent("press", self._hotkey))
                return True

        except AttributeError:
            pass
        return True

    def _on_release(self, key):
        """Handle key release events."""
        try:
            # Track modifier keys
            if self._is_modifier(key):
                self._active_modifiers.discard(key)
                return True

            # Check if main key was released
            _, main_key = self._hotkey_combo
            if key == main_key:
                self._emit_event("hotkey_release", HotkeyEvent("release", self._hotkey))
                return True

        except AttributeError:
            pass
        return True

    def start(self):
        """Start the hotkey listener in a background thread."""
        with self._lock:
            if self._is_running:
                logger.warning("Hotkey listener already running")
                return

            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            self._is_running = True
            logger.info(f"Hotkey listener started: {self._hotkey}")

    def stop(self):
        """Stop the hotkey listener."""
        with self._lock:
            if not self._is_running:
                return

            if self._listener:
                self._listener.stop()
                self._listener = None

            self._is_running = False
            logger.info("Hotkey listener stopped")

    @property
    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._is_running

    def _emit_event(self, event_type: str, event: HotkeyEvent):
        """Emit an event to callbacks and queue."""
        # Add to queue for polling
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            logger.warning("Event queue full, dropping hotkey event")

        # Call registered callbacks
        with self._lock:
            callbacks = self._callbacks.get(event_type, []).copy()

        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Error in {event_type} callback: {e}")

    def on(self, event: str, callback: Callable) -> Callable[[], None]:
        """
        Register a callback for an event type.

        Parameters
        ----------
        event
            Event type: "hotkey_press" or "hotkey_release".
        callback
            Function to call when event occurs.

        Returns
        -------
        Callable[[], None]
            Unsubscribe function.
        """
        if event not in self._callbacks:
            raise ValueError(f"Unknown event type: {event}")

        with self._lock:
            self._callbacks[event].append(callback)

        def unsubscribe():
            with self._lock:
                if event in self._callbacks and callback in self._callbacks[event]:
                    self._callbacks[event].remove(callback)

        return unsubscribe

    def get_next_event(self, timeout: float = 0.0) -> Optional[HotkeyEvent]:
        """
        Get the next event from the queue without blocking.

        Parameters
        ----------
        timeout
            Maximum time to wait in seconds. 0 for non-blocking.

        Returns
        -------
        HotkeyEvent or None
            The next event, or None if queue is empty.
        """
        try:
            if timeout > 0:
                return self._event_queue.get(timeout=timeout)
            else:
                return self._event_queue.get_nowait()
        except queue.Empty:
            return None

    def process_events(self) -> list[HotkeyEvent]:
        """
        Process all pending events from the queue.

        Returns
        -------
        list[HotkeyEvent]
            List of all pending events.
        """
        events = []
        while True:
            event = self.get_next_event(timeout=0.0)
            if event is None:
                break
            events.append(event)
        return events
