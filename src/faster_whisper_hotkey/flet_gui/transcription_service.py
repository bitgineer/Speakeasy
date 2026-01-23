"""
Transcription service layer for the Flet GUI.

This module provides a service wrapper around the existing MicrophoneTranscriber,
offering async/Flet-compatible methods with callback support for UI updates.

Classes
-------
TranscriptionService
    Service wrapper for transcription operations.
"""

import logging
import threading
import queue
import time
from typing import Callable, Optional, Any
from dataclasses import dataclass

from ..transcriber import MicrophoneTranscriber
from ..settings import Settings
from .app_state import RecordingState

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionEvent:
    """Event data for transcription state changes."""
    event_type: str  # "state_change", "transcription", "error", "audio_level"
    data: Any = None


class TranscriptionService:
    """
    Service wrapper for transcription with Flet-compatible callbacks.

    This service manages the MicrophoneTranscriber and provides:
    - Thread-safe communication with the Flet UI
    - Event queue for UI updates from background threads
    - Callback registration for state changes
    - Recording control methods

    The service runs the transcription engine in background threads and
    communicates state changes back to the Flet UI via a thread-safe queue.

    Attributes
    ----------
    transcriber
        The underlying MicrophoneTranscriber instance.
    event_queue
        Thread-safe queue for events to be processed by the UI.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the transcription service.

        Parameters
        ----------
        settings
            Settings object to configure the transcriber.
        """
        self._settings = settings
        self._transcriber: Optional[MicrophoneTranscriber] = None
        self._event_queue: queue.Queue = queue.Queue()
        self._lock = threading.RLock()
        self._callbacks = {
            "state_change": [],
            "transcription": [],
            "transcription_start": [],
            "audio_level": [],
            "streaming_update": [],
            "error": [],
        }
        self._is_initialized = False

    def initialize(self) -> bool:
        """
        Initialize the transcriber with current settings.

        Returns
        -------
        bool
            True if initialization was successful.
        """
        with self._lock:
            try:
                # Create transcriber with callbacks
                self._transcriber = MicrophoneTranscriber(
                    self._settings,
                    on_state_change=self._on_state_change,
                    on_transcription=self._on_transcription,
                    on_transcription_start=self._on_transcription_start,
                    on_audio_level=self._on_audio_level,
                    on_streaming_update=self._on_streaming_update,
                )
                self._is_initialized = True
                self._emit_event("initialized", None)
                logger.info("Transcription service initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize transcription service: {e}")
                self._emit_event("error", str(e))
                return False

    def reinitialize(self, settings: Settings) -> bool:
        """
        Reinitialize the transcriber with new settings.

        Parameters
        ----------
        settings
            New Settings object to configure the transcriber.

        Returns
        -------
        bool
            True if reinitialization was successful.
        """
        with self._lock:
            # Stop existing transcriber if running
            if self._transcriber:
                try:
                    self._transcriber.stop()
                except Exception as e:
                    logger.warning(f"Error stopping transcriber: {e}")

            # Reinitialize with new settings
            self._settings = settings
            return self.initialize()

    # Callback registration
    def on(self, event: str, callback: Callable) -> Callable[[], None]:
        """
        Register a callback for an event type.

        Parameters
        ----------
        event
            Event type: "state_change", "transcription", "transcription_start",
            "audio_level", "streaming_update", or "error".
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

    def _emit_event(self, event: str, data: Any = None):
        """Emit an event to all registered callbacks."""
        with self._lock:
            callbacks = self._callbacks.get(event, []).copy()

        # Also add to queue for polling
        try:
            self._event_queue.put_nowait(TranscriptionEvent(event, data))
        except queue.Full:
            logger.warning("Event queue full, dropping event")

        # Call callbacks directly
        for callback in callbacks:
            try:
                if data is not None:
                    callback(data)
                else:
                    callback()
            except Exception as e:
                logger.warning(f"Error in {event} callback: {e}")

    # Transcriber callbacks (called from background threads)
    def _on_state_change(self, state: str):
        """Handle transcriber state changes."""
        self._emit_event("state_change", state)

    def _on_transcription(self, text: str):
        """Handle completed transcription."""
        self._emit_event("transcription", text)

    def _on_transcription_start(self, duration: float):
        """Handle transcription start."""
        self._emit_event("transcription_start", duration)

    def _on_audio_level(self, level: float):
        """Handle audio level updates."""
        self._emit_event("audio_level", level)

    def _on_streaming_update(self, text: str, confidence: float, is_final: bool):
        """Handle streaming transcription updates."""
        self._emit_event("streaming_update", {"text": text, "confidence": confidence, "is_final": is_final})

    # Recording control methods
    def start_recording(self) -> bool:
        """
        Start audio recording.

        Returns
        -------
        bool
            True if recording started successfully.
        """
        with self._lock:
            if not self._transcriber:
                logger.warning("Cannot start recording: transcriber not initialized")
                return False

            if self._transcriber.is_recording:
                logger.debug("Recording already in progress")
                return True

            try:
                self._transcriber.start_recording()
                self._emit_event("state_change", "recording")
                return True
            except Exception as e:
                logger.error(f"Failed to start recording: {e}")
                self._emit_event("error", str(e))
                return False

    def stop_recording(self) -> bool:
        """
        Stop audio recording and start transcription.

        Returns
        -------
        bool
            True if recording stopped successfully.
        """
        with self._lock:
            if not self._transcriber:
                logger.warning("Cannot stop recording: transcriber not initialized")
                return False

            if not self._transcriber.is_recording:
                logger.debug("No recording in progress")
                return True

            try:
                self._transcriber.stop_recording_and_transcribe()
                self._emit_event("state_change", "transcribing")
                return True
            except Exception as e:
                logger.error(f"Failed to stop recording: {e}")
                self._emit_event("error", str(e))
                return False

    def toggle_recording(self) -> bool:
        """
        Toggle recording state.

        Returns
        -------
        bool
            True if operation was successful.
        """
        with self._lock:
            if not self._transcriber:
                return False

            if self._transcriber.is_recording:
                return self.stop_recording()
            else:
                return self.start_recording()

    # Properties
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self._transcriber.is_recording if self._transcriber else False

    @property
    def is_transcribing(self) -> bool:
        """Check if currently transcribing."""
        with self._lock:
            return self._transcriber.is_transcribing if self._transcriber else False

    @property
    def is_initialized(self) -> bool:
        """Check if service has been initialized."""
        return self._is_initialized

    @property
    def event_queue(self) -> queue.Queue:
        """Get the event queue for polling in the UI."""
        return self._event_queue

    def get_next_event(self, timeout: float = 0.0) -> Optional[TranscriptionEvent]:
        """
        Get the next event from the queue without blocking.

        Parameters
        ----------
        timeout
            Maximum time to wait in seconds. 0 for non-blocking.

        Returns
        -------
        TranscriptionEvent or None
            The next event, or None if queue is empty.
        """
        try:
            if timeout > 0:
                return self._event_queue.get(timeout=timeout)
            else:
                return self._event_queue.get_nowait()
        except queue.Empty:
            return None

    def process_events(self) -> list[TranscriptionEvent]:
        """
        Process all pending events from the queue.

        Returns
        -------
        list[TranscriptionEvent]
            List of all pending events.
        """
        events = []
        while True:
            event = self.get_next_event(timeout=0.0)
            if event is None:
                break
            events.append(event)
        return events

    # Cleanup
    def shutdown(self):
        """Shutdown the transcription service and cleanup resources."""
        with self._lock:
            if self._transcriber:
                try:
                    self._transcriber.stop()
                    logger.info("Transcriber stopped")
                except Exception as e:
                    logger.warning(f"Error stopping transcriber: {e}")
                self._transcriber = None

            self._is_initialized = False

    # Update methods for settings changes
    def reload_voice_commands(self):
        """Reload voice command processor from settings."""
        with self._lock:
            if self._transcriber:
                self._transcriber.reload_voice_commands()

    def reload_text_processor(self):
        """Reload text processor from settings."""
        with self._lock:
            if self._transcriber:
                self._transcriber.reload_text_processor()

    @property
    def current_audio_level(self) -> float:
        """Get the current audio level."""
        with self._lock:
            if self._transcriber:
                return self._transcriber.current_audio_level
            return 0.0
