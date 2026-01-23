"""
Shared application state for the Flet GUI.

This module provides a thread-safe state management system for the Flet application,
allowing UI components and background services to share and react to state changes.

Classes
-------
AppState
    Thread-safe state container for the Flet application.
"""

import threading
import logging
from typing import Any, Callable, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RecordingState(Enum):
    """Recording states for the transcriber."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


@dataclass
class AppState:
    """
    Thread-safe shared state for the Flet application.

    This class manages all shared application state and provides a
    subscription mechanism for components to react to state changes.

    Attributes
    ----------
    is_recording
        Whether audio recording is currently active.
    recording_state
        Current recording state (idle, recording, transcribing, error).
    current_model
        Name of the currently loaded ASR model.
    language
        Current language code for transcription.
    device
        Current device type (cpu or cuda).
    hotkey
        Current hotkey combination string.
    latest_transcription
        Most recent transcription result.
    audio_level
        Current audio input level (0.0 to 1.0) for visualization.
    status_message
        Current status message to display in the UI.
    """

    # Recording state
    _is_recording: bool = False
    _recording_state: RecordingState = RecordingState.IDLE
    _audio_level: float = 0.0

    # Model/Settings state
    _current_model: str = "large-v3"
    _language: str = "en"
    _device: str = "cpu"
    _hotkey: str = "pause"
    _activation_mode: str = "hold"  # "hold" or "toggle"

    # Transcription output
    _latest_transcription: str = ""
    _streaming_transcription: str = ""

    # UI state
    _status_message: str = "Ready"
    _window_visible: bool = True

    # Thread safety
    _lock: threading.RLock = field(default_factory=threading.RLock)
    _listeners: Dict[str, Set[Callable]] = field(default_factory=dict)

    def subscribe(self, event: str, callback: Callable[[Any], None]) -> Callable[[], None]:
        """
        Subscribe to state change events.

        Parameters
        ----------
        event
            The event name to subscribe to (e.g., "recording_state_changed").
        callback
            The callback function to invoke when the event occurs.

        Returns
        -------
        Callable[[], None]
            Unsubscribe function that removes this subscription.
        """
        with self._lock:
            if event not in self._listeners:
                self._listeners[event] = set()
            self._listeners[event].add(callback)

        def unsubscribe():
            with self._lock:
                if event in self._listeners:
                    self._listeners[event].discard(callback)

        return unsubscribe

    def _notify(self, event: str, *args, **kwargs):
        """Notify all subscribers of an event."""
        with self._lock:
            listeners = self._listeners.get(event, set()).copy()

        for callback in listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Error in state change callback: {e}")

    # Recording state properties
    @property
    def is_recording(self) -> bool:
        """Get whether recording is active."""
        with self._lock:
            return self._is_recording

    @is_recording.setter
    def is_recording(self, value: bool):
        with self._lock:
            if self._is_recording != value:
                self._is_recording = value
                self._notify("recording_changed", value)

    @property
    def recording_state(self) -> RecordingState:
        """Get the current recording state."""
        with self._lock:
            return self._recording_state

    @recording_state.setter
    def recording_state(self, value: RecordingState):
        with self._lock:
            if self._recording_state != value:
                old_state = self._recording_state
                self._recording_state = value
                self._notify("recording_state_changed", value, old_state)

    @property
    def audio_level(self) -> float:
        """Get the current audio level (0.0 to 1.0)."""
        with self._lock:
            return self._audio_level

    @audio_level.setter
    def audio_level(self, value: float):
        with self._lock:
            self._audio_level = max(0.0, min(1.0, value))

    # Model/Settings properties
    @property
    def current_model(self) -> str:
        """Get the current model name."""
        with self._lock:
            return self._current_model

    @current_model.setter
    def current_model(self, value: str):
        with self._lock:
            if self._current_model != value:
                self._current_model = value
                self._notify("model_changed", value)

    @property
    def language(self) -> str:
        """Get the current language code."""
        with self._lock:
            return self._language

    @language.setter
    def language(self, value: str):
        with self._lock:
            if self._language != value:
                self._language = value
                self._notify("language_changed", value)

    @property
    def device(self) -> str:
        """Get the current device type."""
        with self._lock:
            return self._device

    @device.setter
    def device(self, value: str):
        with self._lock:
            if self._device != value:
                self._device = value
                self._notify("device_changed", value)

    @property
    def hotkey(self) -> str:
        """Get the current hotkey string."""
        with self._lock:
            return self._hotkey

    @hotkey.setter
    def hotkey(self, value: str):
        with self._lock:
            if self._hotkey != value:
                self._hotkey = value
                self._notify("hotkey_changed", value)

    @property
    def activation_mode(self) -> str:
        """Get the activation mode ('hold' or 'toggle')."""
        with self._lock:
            return self._activation_mode

    @activation_mode.setter
    def activation_mode(self, value: str):
        with self._lock:
            if self._activation_mode != value:
                self._activation_mode = value
                self._notify("activation_mode_changed", value)

    # Transcription properties
    @property
    def latest_transcription(self) -> str:
        """Get the latest transcription result."""
        with self._lock:
            return self._latest_transcription

    @latest_transcription.setter
    def latest_transcription(self, value: str):
        with self._lock:
            self._latest_transcription = value
            self._notify("transcription_completed", value)

    @property
    def streaming_transcription(self) -> str:
        """Get the current streaming transcription text."""
        with self._lock:
            return self._streaming_transcription

    @streaming_transcription.setter
    def streaming_transcription(self, value: str):
        with self._lock:
            self._streaming_transcription = value
            self._notify("streaming_update", value)

    # UI properties
    @property
    def status_message(self) -> str:
        """Get the current status message."""
        with self._lock:
            return self._status_message

    @status_message.setter
    def status_message(self, value: str):
        with self._lock:
            if self._status_message != value:
                self._status_message = value
                self._notify("status_changed", value)

    @property
    def window_visible(self) -> bool:
        """Get whether the main window is visible."""
        with self._lock:
            return self._window_visible

    @window_visible.setter
    def window_visible(self, value: bool):
        with self._lock:
            if self._window_visible != value:
                self._window_visible = value
                self._notify("window_visibility_changed", value)

    def get_dict(self) -> Dict[str, Any]:
        """Get a snapshot of all state values."""
        with self._lock:
            return {
                "is_recording": self._is_recording,
                "recording_state": self._recording_state.value,
                "audio_level": self._audio_level,
                "current_model": self._current_model,
                "language": self._language,
                "device": self._device,
                "hotkey": self._hotkey,
                "activation_mode": self._activation_mode,
                "latest_transcription": self._latest_transcription,
                "streaming_transcription": self._streaming_transcription,
                "status_message": self._status_message,
                "window_visible": self._window_visible,
            }

    def update_from_settings(self, settings):
        """
        Update state from a Settings object.

        Parameters
        ----------
        settings
            Settings object from the settings module.
        """
        with self._lock:
            self._current_model = settings.model_name
            self._language = settings.language
            self._device = settings.device
            self._hotkey = settings.hotkey
            self._activation_mode = getattr(settings, 'activation_mode', 'hold')

        # Notify listeners of batch update
        self._notify("settings_loaded", settings)
