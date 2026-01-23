"""
Telemetry and crash reporting module for faster-whisper-hotkey.

This module provides anonymous usage statistics and crash reporting functionality.
All telemetry is opt-in and respects user privacy. No sensitive data is collected.

Classes
-------
TelemetryManager
    Manages telemetry collection, batch transmission, and privacy settings.

CrashReport
    Data class for crash report information.

TelemetryEvent
    Data class for individual telemetry events.

Notes
-----
- All telemetry is anonymous (no user IDs, IP addresses, or personal data)
- Users must explicitly opt-in to enable telemetry
- Telemetry can be disabled at any time
- Events are batched and sent periodically to reduce network overhead
"""

import hashlib
import json
import logging
import os
import platform
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of telemetry events."""
    # App lifecycle
    APP_START = "app_start"
    APP_SHUTDOWN = "app_shutdown"
    APP_UPGRADE = "app_upgrade"

    # Transcription events
    TRANSCRIPTION_START = "transcription_start"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    TRANSCRIPTION_ERROR = "transcription_error"

    # Model events
    MODEL_LOAD = "model_load"
    MODEL_CHANGE = "model_change"
    MODEL_DOWNLOAD_START = "model_download_start"
    MODEL_DOWNLOAD_COMPLETE = "model_download_complete"
    MODEL_DOWNLOAD_ERROR = "model_download_error"

    # Settings events
    SETTINGS_CHANGE = "settings_change"

    # Feature usage
    FEATURE_USE = "feature_use"

    # Errors
    ERROR = "error"
    CRASH = "crash"


class FeatureType(Enum):
    """Feature types for usage tracking."""
    STREAMING = "streaming"
    VOICE_COMMANDS = "voice_commands"
    TEXT_PROCESSING = "text_processing"
    AUTO_PASTE = "auto_paste"
    HISTORY_SEARCH = "history_search"
    SNIPPETS = "snippets"
    APP_RULES = "app_rules"
    HOTKEY_RECORDING = "hotkey_recording"
    LANGUAGE_DETECTION = "language_detection"


@dataclass
class CrashReport:
    """Crash report data."""
    timestamp: str
    error_type: str
    error_message: str
    stack_trace: str
    app_version: str
    os_version: str
    python_version: str
    device_type: str = "cpu"  # cpu or cuda
    model_used: str = ""
    recent_actions: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelemetryEvent:
    """Single telemetry event."""
    event_type: str
    timestamp: str
    app_version: str
    os: str
    os_version: str
    python_version: str
    device_type: str = "cpu"
    # Optional event-specific data
    model_name: str = ""
    language: str = ""
    duration_ms: int = 0
    word_count: int = 0
    error_type: str = ""
    feature_name: str = ""
    setting_key: str = ""
    # Anonymous session identifier (hashed)
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v}


class TelemetryManager:
    """
    Manages anonymous telemetry and crash reporting.

    Features:
    - Anonymous event tracking (no personal identifiers)
    - Opt-in only (disabled by default)
    - Batched transmission to reduce overhead
    - Crash report capture
    - Respects privacy mode
    """

    # Default configuration
    DEFAULT_ENDPOINT = "https://telemetry.example.com/api/v1/events"
    DEFAULT_CRASH_ENDPOINT = "https://telemetry.example.com/api/v1/crash"
    BATCH_SIZE = 20  # Number of events to batch before sending
    FLUSH_INTERVAL = 300  # Seconds between auto-flushes (5 minutes)
    MAX_PENDING_EVENTS = 100  # Max events to queue before dropping oldest
    SESSION_TIMEOUT = 3600  # Seconds before generating new session ID

    def __init__(
        self,
        enabled: bool = False,
        settings_dir: Optional[str] = None,
        endpoint: str = None,
        crash_endpoint: str = None,
    ):
        """
        Initialize telemetry manager.

        Parameters
        ----------
        enabled
            Whether telemetry is enabled (must be opt-in)
        settings_dir
            Directory for storing telemetry state
        endpoint
            Telemetry endpoint URL
        crash_endpoint
            Crash report endpoint URL
        """
        self._enabled = enabled
        self._settings_dir = settings_dir or self._get_default_settings_dir()
        self._endpoint = endpoint or self.DEFAULT_ENDPOINT
        self._crash_endpoint = crash_endpoint or self.DEFAULT_CRASH_ENDPOINT

        # State
        self._pending_events: List[TelemetryEvent] = []
        self._lock = threading.Lock()
        self._session_id = self._load_or_create_session_id()
        self._last_flush = time.time()
        self._app_version = self._get_app_version()
        self._system_info = self._get_system_info()

        # Background thread for periodic flushes
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

        # Install crash handler
        self._original_excepthook = None
        self._crash_in_progress = False

        if self._enabled:
            self._start_flush_thread()
            self._install_crash_handler()

    def _get_default_settings_dir(self) -> str:
        """Get default settings directory."""
        if sys.platform == "win32":
            conf_dir = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        else:
            conf_dir = os.path.expanduser('~/.config')
        settings_dir = os.path.join(conf_dir, "faster_whisper_hotkey")
        os.makedirs(settings_dir, exist_ok=True)
        return settings_dir

    def _get_state_file(self) -> str:
        """Get telemetry state file path."""
        return os.path.join(self._settings_dir, "telemetry_state.json")

    def _load_or_create_session_id(self) -> str:
        """Load existing session ID or create a new one."""
        state_file = self._get_state_file()

        try:
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    # Check if session is still valid
                    last_seen = state.get("last_seen", 0)
                    if time.time() - last_seen < self.SESSION_TIMEOUT:
                        return state.get("session_id", self._generate_session_id())
        except (json.JSONDecodeError, IOError):
            pass

        # Create new session
        return self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate anonymous session ID."""
        # Use timestamp + random bytes, then hash
        data = f"{time.time()}_{os.urandom(8).hex()}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def _save_state(self):
        """Save telemetry state."""
        state_file = self._get_state_file()
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self._session_id,
                    "last_seen": time.time(),
                }, f)
        except IOError as e:
            logger.warning(f"Failed to save telemetry state: {e}")

    def _get_app_version(self) -> str:
        """Get application version."""
        try:
            # Try to get from package metadata
            try:
                from importlib.metadata import version
                return version("faster-whisper-hotkey")
            except ImportError:
                pass

            # Try from version.txt in development
            if getattr(sys, 'frozen', False):
                # Running as executable
                here = os.path.dirname(sys.executable)
            else:
                here = os.path.dirname(__file__)

            version_file = os.path.join(here, "version.txt")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()

        except Exception:
            pass

        return "unknown"

    def _get_system_info(self) -> Dict[str, str]:
        """Get anonymous system information."""
        return {
            "os": platform.system(),
            "os_version": platform.release(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }

    def _start_flush_thread(self):
        """Start background thread for periodic flushes."""
        def flush_loop():
            while not self._stop_flag.is_set():
                self._stop_flag.wait(self.FLUSH_INTERVAL)
                if not self._stop_flag.is_set():
                    self.flush()

        self._flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self._flush_thread.start()

    def _install_crash_handler(self):
        """Install exception hook for crash reporting."""
        if sys.excepthook != self._crash_handler:
            self._original_excepthook = sys.excepthook
            sys.excepthook = self._crash_handler

    def _crash_handler(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if self._crash_in_progress:
            # Prevent recursive crash handling
            return

        self._crash_in_progress = True

        # Create crash report
        crash_report = CrashReport(
            timestamp=datetime.now().isoformat(),
            error_type=exc_type.__name__,
            error_message=str(exc_value),
            stack_trace="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            app_version=self._app_version,
            os_version=platform.platform(),
            python_version=platform.python_version(),
        )

        # Try to save crash report locally first
        self._save_crash_report_locally(crash_report)

        # Try to send crash report
        if self._enabled:
            self._send_crash_report(crash_report)

        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _save_crash_report_locally(self, crash_report: CrashReport):
        """Save crash report to local file."""
        try:
            crash_dir = os.path.join(self._settings_dir, "crashes")
            os.makedirs(crash_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = os.path.join(crash_dir, f"crash_{timestamp}.json")

            with open(crash_file, "w", encoding="utf-8") as f:
                json.dump(asdict(crash_report), f, indent=2)

            logger.info(f"Crash report saved to {crash_file}")
        except IOError as e:
            logger.warning(f"Failed to save crash report: {e}")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable telemetry.

        Parameters
        ----------
        enabled
            True to enable, False to disable
        """
        if self._enabled == enabled:
            return

        self._enabled = enabled

        if enabled:
            self._start_flush_thread()
            self._install_crash_handler()
            # Flush any pending events
            self.flush()
        else:
            # Stop flush thread
            self._stop_flag.set()
            if self._flush_thread:
                self._flush_thread.join(timeout=5)
                self._flush_thread = None
            self._stop_flag.clear()

            # Clear pending events
            with self._lock:
                self._pending_events.clear()

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return self._enabled

    def track_event(
        self,
        event_type: EventType,
        model_name: str = "",
        language: str = "",
        duration_ms: int = 0,
        word_count: int = 0,
        error_type: str = "",
        feature_name: str = "",
        setting_key: str = "",
        device_type: str = "cpu",
    ) -> Optional[TelemetryEvent]:
        """
        Track a telemetry event.

        Parameters
        ----------
        event_type
            Type of event to track
        model_name
            Model name (for transcription/model events)
        language
            Language code (for transcription events)
        duration_ms
            Duration in milliseconds (for transcription events)
        word_count
            Word count (for transcription events)
        error_type
            Error type (for error events)
        feature_name
            Feature name (for feature usage events)
        setting_key
            Setting key (for settings change events)
        device_type
            Device type (cpu, cuda)

        Returns
        -------
        TelemetryEvent if tracking is enabled, None otherwise
        """
        if not self._enabled:
            return None

        event = TelemetryEvent(
            event_type=event_type.value,
            timestamp=datetime.now().isoformat(),
            app_version=self._app_version,
            os=self._system_info["os"],
            os_version=self._system_info["os_version"],
            python_version=self._system_info["python_version"],
            device_type=device_type,
            model_name=model_name,
            language=language,
            duration_ms=duration_ms,
            word_count=word_count,
            error_type=error_type,
            feature_name=feature_name,
            setting_key=setting_key,
            session_id=self._session_id,
        )

        with self._lock:
            self._pending_events.append(event)

            # Trim if too many pending
            if len(self._pending_events) > self.MAX_PENDING_EVENTS:
                self._pending_events = self._pending_events[-self.MAX_PENDING_EVENTS:]

            # Flush if batch size reached
            if len(self._pending_events) >= self.BATCH_SIZE:
                # Defer actual flush to avoid holding lock
                threading.Thread(target=self.flush, daemon=True).start()

        return event

    def track_transcription(
        self,
        model_name: str,
        language: str,
        duration_ms: int,
        word_count: int,
        device_type: str = "cpu",
    ):
        """Track a completed transcription."""
        self.track_event(
            EventType.TRANSCRIPTION_COMPLETE,
            model_name=model_name,
            language=language,
            duration_ms=duration_ms,
            word_count=word_count,
            device_type=device_type,
        )

    def track_transcription_error(
        self,
        error_type: str,
        model_name: str,
        device_type: str = "cpu",
    ):
        """Track a transcription error."""
        self.track_event(
            EventType.TRANSCRIPTION_ERROR,
            error_type=error_type,
            model_name=model_name,
            device_type=device_type,
        )

    def track_model_load(self, model_name: str, duration_ms: int):
        """Track model loading."""
        self.track_event(
            EventType.MODEL_LOAD,
            model_name=model_name,
            duration_ms=duration_ms,
        )

    def track_feature_use(self, feature: FeatureType):
        """Track feature usage."""
        self.track_event(
            EventType.FEATURE_USE,
            feature_name=feature.value,
        )

    def track_settings_change(self, setting_key: str):
        """Track settings change."""
        self.track_event(
            EventType.SETTINGS_CHANGE,
            setting_key=setting_key,
        )

    def track_app_start(self):
        """Track application start."""
        self.track_event(EventType.APP_START)
        self._save_state()

    def track_app_shutdown(self):
        """Track application shutdown."""
        self.track_event(EventType.APP_SHUTDOWN)

    def flush(self):
        """
        Flush pending events to the server.

        This is called automatically periodically and when batch size is reached.
        Can also be called manually.
        """
        if not self._enabled:
            return

        with self._lock:
            if not self._pending_events:
                return
            events = self._pending_events.copy()
            self._pending_events.clear()

        if not events:
            return

        try:
            self._send_events(events)
            self._last_flush = time.time()
        except Exception as e:
            logger.warning(f"Failed to send telemetry events: {e}")
            # Re-queue events on failure
            with self._lock:
                self._pending_events = events + self._pending_events

    def _send_events(self, events: List[TelemetryEvent]):
        """Send events to telemetry endpoint."""
        # Prepare payload
        payload = {
            "events": [e.to_dict() for e in events],
            "sent_at": datetime.now().isoformat(),
        }

        # Try to send
        try:
            import urllib.request
            import urllib.error

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._endpoint,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"faster-whisper-hotkey/{self._app_version}",
                },
                method="POST",
                timeout=10,  # 10 second timeout
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Telemetry server returned status {response.status}")

        except ImportError:
            logger.warning("urllib not available, skipping telemetry send")
        except urllib.error.URLError as e:
            logger.warning(f"Failed to connect to telemetry server: {e}")
        except Exception as e:
            logger.warning(f"Error sending telemetry: {e}")

    def _send_crash_report(self, crash_report: CrashReport):
        """Send crash report to server."""
        try:
            import urllib.request
            import urllib.error

            # Sanitize crash report (remove potentially sensitive info)
            sanitized = self._sanitize_crash_report(crash_report)
            data = json.dumps(asdict(sanitized)).encode("utf-8")

            req = urllib.request.Request(
                self._crash_endpoint,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"faster-whisper-hotkey/{self._app_version}",
                },
                method="POST",
                timeout=10,
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info("Crash report sent successfully")

        except Exception as e:
            logger.warning(f"Failed to send crash report: {e}")

    def _sanitize_crash_report(self, crash_report: CrashReport) -> CrashReport:
        """Sanitize crash report to remove potential sensitive information."""
        # Create a copy
        sanitized = CrashReport(
            timestamp=crash_report.timestamp,
            error_type=crash_report.error_type,
            error_message=crash_report.error_message,
            stack_trace=crash_report.stack_trace,
            app_version=crash_report.app_version,
            os_version=crash_report.os_version,
            python_version=crash_report.python_version,
            device_type=crash_report.device_type,
            model_used=crash_report.model_used,
            recent_actions=[],
            additional_context={},
        )

        # Sanitize stack trace - remove file paths
        sanitized.stack_trace = self._sanitize_paths(sanitized.stack_trace)

        return sanitized

    def _sanitize_paths(self, text: str) -> str:
        """Remove file paths from text."""
        import re
        # Replace Windows paths
        text = re.sub(r'[A-Z]:\\[^\\]*\\', '<path>\\\\', text)
        # Replace Unix paths
        text = re.sub(r'/home/[^/]+/', '<home>/', text)
        text = re.sub(r'/Users/[^/]+/', '<home>/', text)
        return text

    def get_pending_count(self) -> int:
        """Get number of pending events."""
        with self._lock:
            return len(self._pending_events)

    def shutdown(self):
        """Shutdown telemetry manager and flush pending events."""
        if self._enabled:
            # Stop flush thread
            self._stop_flag.set()
            if self._flush_thread:
                self._flush_thread.join(timeout=5)

            # Final flush
            self.flush()
            self._save_state()

    def get_crash_reports(self) -> List[CrashReport]:
        """Get locally stored crash reports."""
        crash_dir = os.path.join(self._settings_dir, "crashes")
        if not os.path.exists(crash_dir):
            return []

        reports = []
        try:
            for filename in os.listdir(crash_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(crash_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            reports.append(CrashReport(**data))
                    except (json.JSONDecodeError, IOError, TypeError):
                        continue
        except IOError:
            pass

        return sorted(reports, key=lambda r: r.timestamp, reverse=True)

    def clear_crash_reports(self):
        """Clear locally stored crash reports."""
        crash_dir = os.path.join(self._settings_dir, "crashes")
        if os.path.exists(crash_dir):
            try:
                for filename in os.listdir(crash_dir):
                    filepath = os.path.join(crash_dir, filename)
                    os.remove(filepath)
                logger.info("Crash reports cleared")
            except IOError as e:
                logger.warning(f"Failed to clear crash reports: {e}")

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get summary of telemetry data being collected."""
        return {
            "enabled": self._enabled,
            "pending_events": self.get_pending_count(),
            "session_id": self._session_id[:8] + "..." if self._session_id else "",
            "app_version": self._app_version,
            "last_flush": datetime.fromtimestamp(self._last_flush).isoformat() if self._last_flush else None,
            "crash_reports_count": len(self.get_crash_reports()),
        }


# Global telemetry manager instance
_telemetry_manager: Optional[TelemetryManager] = None
_telemetry_lock = threading.Lock()


def get_telemetry_manager() -> TelemetryManager:
    """Get the global telemetry manager instance."""
    global _telemetry_manager

    with _telemetry_lock:
        if _telemetry_manager is None:
            # Create disabled by default - must be explicitly enabled
            _telemetry_manager = TelemetryManager(enabled=False)

        return _telemetry_manager


def init_telemetry(enabled: bool = False, settings_dir: str = None) -> TelemetryManager:
    """
    Initialize the telemetry manager.

    Parameters
    ----------
    enabled
        Whether telemetry is enabled (opt-in only)
    settings_dir
        Directory for storing telemetry state

    Returns
    -------
    TelemetryManager instance
    """
    global _telemetry_manager

    with _telemetry_lock:
        if _telemetry_manager is not None:
            _telemetry_manager.shutdown()

        _telemetry_manager = TelemetryManager(
            enabled=enabled,
            settings_dir=settings_dir,
        )

        if enabled:
            _telemetry_manager.track_app_start()

        return _telemetry_manager


def shutdown_telemetry():
    """Shutdown the telemetry manager."""
    global _telemetry_manager

    with _telemetry_lock:
        if _telemetry_manager is not None:
            _telemetry_manager.shutdown()
